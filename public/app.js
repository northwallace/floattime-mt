// =====================================================================
// FloatETA — application logic
// =====================================================================

const P = FloatPlanner;
let RIVERS = [], STATES = [], CRAFT = [];
const gaugeCache = new Map(), weatherCache = new Map();
const USGS_IV = "https://waterservices.usgs.gov/nwis/iv/";
const SPEED_EXPONENT = 0.34; // hydraulic geometry: v ∝ Q^0.34
const MIN_SPEED_MPH = 0.8;
const MAX_SPEED_MPH = 9.0;
const FLOAT_DAY_HOURS = 10; // sections longer than this at current speed = multi-day
const FISH_MIN_PER_MILE = 25; // extra time if stopping to fish

const $ = (id) => document.getElementById(id);
const riverState = (river) => (river && river.state) || "MT";

const state = {
  river: null,          // current river object
  craft: null,          // current craft object
  putIn: null,          // Date for today's put-in, or null if unset
  fishing: false,       // add FISH_MIN_PER_MILE per mile for stop-and-fish floats
  gaugeCache: {},       // gauge id -> { flow, temp, series, fetchedAt }
  weatherCache: {},     // river id -> { airF, windMph }
  reports: [],
  votedIds: new Set(),
  reportsStatus: "loading",
  request: 0,
  gauge: null,
};

// ---------------------------------------------------------------------
// Sunset (NOAA simplified algorithm) — good to ~1 minute, plenty here.
// ---------------------------------------------------------------------

function sunsetToday(lat, lon) { return P.sunset(lat, lon, state.river.timezone); }
function fmtClock(date) { return P.clock(date, state.river.timezone); }
function fmtDuration(hours) { return P.duration(hours * 60); }
async function json(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json();
}
function cached(map, key, load, ttl = 300000) {
  const old = map.get(key);
  if (old && Date.now() - old.at < ttl) return old.promise;
  const entry = { at: Date.now(), promise: load() };
  map.set(key, entry);
  entry.promise.catch(() => {
    if (map.get(key) === entry) map.delete(key);
  });
  return entry.promise;
}
function gaugeFor(river) {
  return cached(gaugeCache, river.gauge, async () => {
    const data = await json(
      `https://waterservices.usgs.gov/nwis/iv/?format=json&sites=${encodeURIComponent(river.gauge)}&parameterCd=00060,00010&period=P7D&siteStatus=all`,
    );
    const result = { flow: null, at: null, temp: null, tempAt: null, series: [] };
    for (const series of data.value?.timeSeries || []) {
      const code = series.variable?.variableCode?.[0]?.value;
      const noData = Number(series.variable?.noDataValue ?? -999999);
      const values = (series.values || [])
        .flatMap((v) => v.value || [])
        .map((v) => ({ value: Number(v.value), at: Date.parse(v.dateTime) }))
        .filter(
          (v) =>
            Number.isFinite(v.value) &&
            v.value !== noData &&
            Number.isFinite(v.at) &&
            (code === "00060" ? v.value >= 0 : v.value > -5 && v.value < 60),
        )
        .sort((a, b) => a.at - b.at);
      const last = values.at(-1);
      if (!last) continue;
      if (code === "00060") {
        result.flow = last.value;
        result.at = last.at;
        result.series = values.map(v => ({t:v.at,q:v.value}));
      }
      if (code === "00010") {
        result.temp = last.value;
        result.tempAt = last.at;
      }
    }
    return result;
  });
}
function weatherFor(river) {
  return cached(weatherCache, river.id, () =>
    json(
      `https://api.open-meteo.com/v1/forecast?latitude=${river.lat}&longitude=${river.lon}&current=temperature_2m,wind_speed_10m&daily=precipitation_probability_max,uv_index_max,temperature_2m_max,temperature_2m_min&forecast_days=2&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=${encodeURIComponent(river.timezone)}`,
    ),
  );
}
// ---------------------------------------------------------------------
// Float math
// ---------------------------------------------------------------------

function riverSpeedMph(river, flowCfs) {
  const v = river.refSpeedMph * Math.pow(flowCfs / river.refFlowCfs, SPEED_EXPONENT);
  return Math.min(MAX_SPEED_MPH, Math.max(MIN_SPEED_MPH, v));
}

function conditionFor(river, flowCfs) {
  const ratio = flowCfs / river.refFlowCfs;
  const level = ratio < .4 ? ["cond-low", "Well below reference"] : ratio < .8 ? ["cond-mellow", "Below reference"] : ratio < 1.5 ? ["cond-prime", "Near reference"] : ratio < 2.5 ? ["cond-high", "Above reference"] : ["cond-danger", "Well above reference"];
  return {cls:level[0],label:level[1],note:"Compared with this river’s reference flow. This is not a safety rating.",craft:"Check your stretch, skill level, and local conditions."};
}

function dressFor(tempC) {
  if (tempC == null) return "No water temp from this gauge — pack a layer you'd swim in.";
  const f = tempC * 9 / 5 + 32;
  if (f < 50) return `Water is ${Math.round(f)}°F — drysuit or thick wetsuit. This is hypothermia water.`;
  if (f < 60) return `Water is ${Math.round(f)}°F — wetsuit. A dunk will knock the wind out of you.`;
  if (f < 68) return `Water is ${Math.round(f)}°F — wetsuit or splash top. Dunks are still cold.`;
  return `Water is ${Math.round(f)}°F — summer kit. PFD is still non-negotiable.`;
}

function uvLabel(uv) {
  if (uv == null) return "–";
  if (uv <= 2) return `${Math.round(uv)} low`;
  if (uv <= 5) return `${Math.round(uv)} mod`;
  if (uv <= 7) return `${Math.round(uv)} high`;
  return `${Math.round(uv)} very high`;
}

function gaugeAge(ts) {
  if (!ts) return "reading time unknown";
  const mins = Math.max(0, Math.round((Date.now() - ts) / 60000));
  if (mins < 2) return "updated just now";
  if (mins < 60) return `updated ${mins} min ago`;
  const hrs = Math.round(mins / 60);
  return hrs === 1 ? "updated 1 hr ago" : `updated ${hrs} hr ago`;
}

function trendFor(series) {
  if (series.length < 10) return { cls: "trend-flat", text: "trend unavailable" };
  const latest = series[series.length - 1].q;
  const dayAgoTime = series[series.length - 1].t - 24 * 3600 * 1000;
  let past = series[0];
  for (const p of series) { if (p.t <= dayAgoTime) past = p; else break; }
  const delta = latest - past.q;
  const pct = past.q ? (delta / past.q) * 100 : 0;
  if (pct > 4)  return { cls: "trend-up",   text: `▲ rising — up ${Math.abs(pct).toFixed(0)}% in 24 hr` };
  if (pct < -4) return { cls: "trend-down", text: `▼ dropping — down ${Math.abs(pct).toFixed(0)}% in 24 hr` };
  return { cls: "trend-flat", text: "● steady over the last 24 hr" };
}

function waterTempLabel(tempC) {
  const f = tempC * 9 / 5 + 32;
  return `${Math.round(f)}°F`;
}

// ---------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------

function drawSparkline(svg, series) {
  svg.innerHTML = "";
  if (series.length < 2) return;
  const W = 300, H = 60, pad = 4;
  const t0 = series[0].t, t1 = series[series.length - 1].t;
  const qs = series.map((p) => p.q);
  const qMin = Math.min(...qs), qMax = Math.max(...qs);
  const qSpan = qMax - qMin || 1;

  const pts = series.map((p) => {
    const x = pad + ((p.t - t0) / (t1 - t0 || 1)) * (W - 2 * pad);
    const y = H - pad - ((p.q - qMin) / qSpan) * (H - 2 * pad);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const line = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  line.setAttribute("points", pts.join(" "));
  line.setAttribute("fill", "none");
  line.setAttribute("stroke", "#4fd1a5");
  line.setAttribute("stroke-width", "2");

  const area = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
  area.setAttribute("points", `${pad},${H - pad} ${pts.join(" ")} ${W - pad},${H - pad}`);
  area.setAttribute("fill", "rgba(79,209,165,0.12)");

  svg.appendChild(area);
  svg.appendChild(line);
}

function renderDaylight(river) {
  const sunset = sunsetToday(river.lat, river.lon);
  if (!sunset) { $("sunsetTime").textContent = "Sunset unavailable"; $("daylightLeft").textContent = "—"; return null; }
  const now = new Date();
  const hoursLeft = (sunset - now) / 3600000;

  $("sunsetTime").textContent = `Sunset at ${fmtClock(sunset)}`;
  if (hoursLeft <= 0) {
    $("daylightLeft").textContent = "After sunset";
    $("daylightNote").textContent = "The river will still be there tomorrow.";
  } else {
    $("daylightLeft").textContent = fmtDuration(hoursLeft);
    $("daylightNote").textContent = "";
  }
  $("statDaylight").textContent = $("daylightLeft").textContent;
  return sunset;
}

function parsePutIn(value) { return value ? P.launch(value, state.river.timezone) : null; }
function reportMatches(r, river) { return r.riverId ? r.riverId === river.id : r.river === river.name; }
function renderSections(river, gauge, sunset) {
  const container = $("sectionCards");
  container.replaceChildren();
  const launch = parsePutIn($("putInTime").value);
  for (const sec of river.sections) {
    const stops = state.fishing ? sec.miles * FISH_MIN_PER_MILE : 0;
    const estimate = P.fresh(gauge) ? P.estimate(river, sec, gauge.flow, state.craft.mult, stops) : null;
    const restricted = /\b(?:III|IV|V|VI)\b/.test(sec.difficulty) && ["tube", "sup"].includes(state.craft.id);
    let timing = "", duration = "—", detail = "";
    if (!estimate) {
      timing = '<p class="fc-launch tight">No recent, positive flow reading is available. A current estimate cannot be calculated.</p>';
    } else if (restricted) {
      timing = '<p class="fc-launch tight">Class III+ whitewater: no tube or recreational paddleboard estimate. Check local guidance and choose an appropriate craft.</p>';
    } else {
      duration = P.duration(estimate.minutes);
      detail = `~${estimate.speed.toFixed(1)} mph · rounded to 5 minutes${state.fishing ? ` · includes ${P.duration(stops)} for fishing` : ""}`;
      if (estimate.multiDay) {
        timing = `<p class="fc-launch">At least ${estimate.days} floating days at 7 hours per day. Total time on water shown above; plan overnight stops separately.</p>`;
      } else if ($("putInTime").value && !launch) {
        timing = '<p class="fc-launch tight">Enter a valid time for today at the river.</p>';
      } else if (launch) {
        const finish = new Date(launch.getTime() + estimate.minutes * 60000);
        const nextDay = P.dateKey(finish,river.timezone) !== P.dateKey(launch,river.timezone);
        const spare = sunset ? Math.floor((sunset-finish)/60000) : null;
        timing = `<div class="fc-eta"><div class="fc-eta-leg"><span class="fc-eta-label">Put in today</span><span class="fc-eta-time">${fmtClock(launch)}</span></div><div class="fc-eta-arrow" aria-hidden="true">→</div><div class="fc-eta-leg"><span class="fc-eta-label">Take out ≈</span><span class="fc-eta-time">${fmtClock(finish)}${nextDay ? " · next day" : ""}</span></div></div>`;
        timing += `<p class="fc-launch ${spare !== null && spare < 30 ? "no" : "ok"}">${spare === null ? "Sunset unavailable." : spare < 0 ? `Estimated finish is ${P.duration(-spare)} after sunset. Launch earlier or choose a shorter stretch.` : `About ${P.duration(spare)} before sunset. Allow a safety margin.`}</p>`;
        if (launch < new Date()) timing += '<p class="fc-notes">This launch time has already passed today.</p>';
      } else if (sunset) {
        const latest = new Date(sunset-estimate.minutes*60000-30*60000);
        timing = latest > new Date() ? `<p class="fc-launch ok">Launch by ${fmtClock(latest)} for a 30-minute sunset buffer.</p>` : '<p class="fc-launch no">Not enough daylight left for this stretch today with a 30-minute buffer.</p>';
      }
    }
    const reports = state.reports.filter(r => reportMatches(r, river) && (!r.section || r.section === `${sec.putIn} → ${sec.takeOut}`));
    const hazards = state.reportsStatus !== "ready" ? '<p class="fc-hazard">Community reports are loading or unavailable. Check local conditions.</p>' : reports.length ? `<a class="fc-hazard" href="#reports">${reports.length} community report(s) on this river or stretch ↓</a>` : "";
    const card = document.createElement("article"); card.className = "float-card"; card.id = `section-${sec.id}`;
    card.innerHTML = `<div class="fc-route">${esc(sec.putIn)}<span class="arrow">→</span>${esc(sec.takeOut)}</div><div class="fc-meta"><span>${sec.miles} mi</span><span class="diff">${esc(sec.difficulty)}</span></div><div class="fc-time"><span class="fc-time-label">${estimate?.multiDay ? "Total estimated time on water" : state.fishing ? "Estimated time (fishing)" : "Estimated float time"}</span>${duration}</div><div class="fc-speed">${detail}</div>${timing}${hazards}<div class="fc-notes">${esc(sec.notes)}</div>`;
    container.appendChild(card);
  }
}

async function renderRiver() {
  const river = state.river, request = ++state.request;
  if (!river) return;
  state.gauge = null;
  $("riverDash").hidden = false;
  $("loadError").hidden = true;
  $("riverBlurb").textContent = river.blurb;
  const st = STATES.find(s => s.id === river.state);
  $("agencyLink").textContent = st.agency; $("agencyLink").href = st.agencyUrl;
  $("gaugeName").textContent = `USGS ${river.gauge} — ${river.gaugeName} · checking reading…`;
  for (const id of ["flowValue","flowTrend","waterTemp","airTemp","windSpeed","rainToday","rainTomorrow","uvIndex"]) $(id).textContent = "—";
  $("conditionBadge").textContent = "Checking flow";
  $("conditionBadge").className = "condition-badge";
  $("conditionNote").textContent = ""; $("craftHint").textContent = "";
  $("packWear").textContent = "Checking water temperature…"; $("packHighLow").textContent = "";
  drawSparkline($("sparkline"), []);
  renderDaylight(river);
  $("sectionCards").innerHTML = '<p role="status">Checking the latest gauge reading…</p>';
  weatherFor(river).then(w => {
    if (request !== state.request) return;
    const c=w.current || {}, d=w.daily || {};
    const show=(value,suffix) => Number.isFinite(value) ? `${Math.round(value)}${suffix}` : "n/a";
    $("airTemp").textContent=show(c.temperature_2m,"°F"); $("windSpeed").textContent=show(c.wind_speed_10m," mph");
    $("rainToday").textContent=show(d.precipitation_probability_max?.[0],"%"); $("rainTomorrow").textContent=show(d.precipitation_probability_max?.[1],"%");
    $("uvIndex").textContent=uvLabel(d.uv_index_max?.[0]);
    $("packHighLow").textContent=`Put-in high ${show(d.temperature_2m_max?.[0],"°F")} / low ${show(d.temperature_2m_min?.[0],"°F")} today`;
  }).catch(() => {if (request===state.request) $("packHighLow").textContent="Weather unavailable. Check the local forecast.";});
  let gauge = null;
  try { gauge = await gaugeFor(river); }
  catch { /* Keep route details and daylight visible when USGS is unavailable. */ }
  if (request !== state.request) return;
  state.gauge = gauge;
  $("flowValue").textContent = gauge?.flow == null ? "—" : gauge.flow.toLocaleString();
  $("gaugeName").textContent = `USGS ${river.gauge} — ${river.gaugeName} · ${gaugeAge(gauge?.at)}`;
  if (gauge) { const trend=trendFor(gauge.series); $("flowTrend").textContent=trend.text; $("flowTrend").className=`dash-sub ${trend.cls}`; drawSparkline($("sparkline"),gauge.series); }
  const current = P.fresh(gauge), cond = current ? conditionFor(river,gauge.flow) : {label:gauge?.flow > 0 ? "Stale reading" : "Reading unavailable",cls:"cond-low",note:"A recent positive flow is needed for estimates.",craft:""};
  $("conditionBadge").textContent=cond.label; $("conditionBadge").className=`condition-badge ${cond.cls}`;
  $("conditionNote").textContent=cond.note; $("craftHint").textContent=cond.craft;
  const tempFresh = gauge?.temp != null && Number.isFinite(gauge.tempAt) && Date.now()-gauge.tempAt >= -300000 && Date.now()-gauge.tempAt <=7200000;
  $("waterTemp").textContent=tempFresh ? waterTempLabel(gauge.temp) : "n/a";
  $("packWear").textContent=dressFor(tempFresh ? gauge.temp : null);
  if (!current) { $("loadError").hidden=false; $("loadError").innerHTML='Current estimates are unavailable. <button type="button" id="retryGauge" class="btn-primary">Retry gauge</button>'; $("retryGauge").onclick=()=>{gaugeCache.delete(river.gauge);renderRiver();}; }
  renderSections(river,gauge,renderDaylight(river));
}

// ---------------------------------------------------------------------
// Reports
// ---------------------------------------------------------------------

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s == null ? "" : String(s);
  return d.innerHTML;
}

const TYPE_LABELS = {
  strainer: "Strainer", diversion: "Diversion dam", fence: "Fence",
  "low-bridge": "Low bridge", debris: "Debris", other: "Hazard",
};

function timeAgo(ts) {
  const mins = Math.floor((Date.now() / 1000 - ts) / 60);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} hr ago`;
  const days = Math.floor(hrs / 24);
  return days === 1 ? "yesterday" : `${days} days ago`;
}

async function loadReports() {
  state.reportsStatus="loading";
  renderReports();
  try {
    const reports=await json("/api/reports");
    if (!Array.isArray(reports)) throw new Error("Invalid reports");
    state.reports=reports; state.reportsStatus="ready";
  } catch { state.reports=[]; state.reportsStatus="error"; }
  renderReports();
  if(state.river)renderSections(state.river,state.gauge,renderDaylight(state.river));
}

function renderReports() {
  const list = $("reportsList");
  if (state.reportsStatus !== "ready") {
    list.innerHTML = state.reportsStatus === "loading" ? '<p role="status">Loading reports…</p>' : '<p role="status">Reports could not load. This does not mean the river is clear.</p><button type="button" class="btn-primary" data-retry-reports>Retry reports</button>';
    return;
  }
  const filterOn = $("filterReports").checked;
  let reports = state.reports;
  if (filterOn && state.river) reports = reports.filter((r) => reportMatches(r, state.river));

  if (!reports.length) {
    list.innerHTML = `<div class="reports-empty">No reports${filterOn ? " for this river" : ""} yet. Hazards may still exist. Check local conditions.</div>`;
    return;
  }

  list.innerHTML = "";
  for (const r of reports) {
    const card = document.createElement("div");
    card.className = `report-card type-${r.type}`;
    const voted = state.votedIds.has(r.id);
    const confirmedNote = r.lastConfirmedAt
      ? ` · confirmed ${timeAgo(r.lastConfirmedAt)}`
      : "";
    card.innerHTML = `
      <div class="rc-top">
        <span class="rc-river">${esc(r.river)}${r.section ? ` · ${esc(r.section)}` : ""}</span>
        <span class="rc-time">${timeAgo(r.createdAt)}${confirmedNote}</span>
      </div>
      <span class="rc-type">${TYPE_LABELS[r.type] || "Hazard"}</span>
      ${r.location ? `<div class="rc-loc">📍 ${esc(r.location)}</div>` : ""}
      <div class="rc-desc">${esc(r.description)}</div>
      <div class="rc-foot">
        <span class="rc-by">— ${esc(r.reporter)}</span>
        <span class="rc-votes">
          <button class="vote-btn" data-id="${esc(r.id)}" data-action="confirm" ${voted ? "disabled" : ""}>👍 Still there (${r.confirmVotes || 0})</button>
          <button class="vote-btn" data-id="${esc(r.id)}" data-action="cleared" ${voted ? "disabled" : ""}>Reported cleared (${r.clearedVotes || 0})</button>
        </span>
      </div>
    `;
    list.appendChild(card);
  }
}

async function vote(id, action) {
  try {
    await json(`/api/reports/${encodeURIComponent(id)}/${action}`,{method:"POST"});
    state.votedIds.add(id);
    try {localStorage.setItem("ft_voted",JSON.stringify([...state.votedIds]));} catch {}
    $("reportStatus").textContent="Vote recorded.";
    await loadReports();
  } catch { $("reportStatus").textContent="Vote failed or was already recorded. Please try refreshing reports."; }
}

async function submitReport(ev) {
  ev.preventDefault();
  const btn = $("reportSubmit");
  const status = $("reportStatus");
  btn.disabled = true;
  status.className = "report-status";
  status.textContent = "Submitting…";

  const body = {
    riverId: $("reportRiver").value,
    type: $("reportType").value,
    location: $("reportLocation").value,
    description: $("reportDesc").value,
    reporter: $("reportName").value,
  };

  try {
    const res = await fetch("/api/reports", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error((await res.json()).error || "Failed");
    status.className = "report-status ok";
    status.textContent = "Thanks — your report is live. Float safe out there. 🤙";
    $("reportForm").reset();
    $("reportRiver").value = body.riverId;
    loadReports();
  } catch (e) {
    status.className = "report-status err";
    status.textContent = `Couldn't submit: ${e.message}`;
  } finally {
    btn.disabled = false;
  }
}

// ---------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------

async function init() {
  try {state.votedIds=new Set(JSON.parse(localStorage.getItem("ft_voted") || "[]"));} catch {}
  try {
    const catalog=await json("/catalog.json");
    RIVERS=catalog.rivers; STATES=catalog.states; CRAFT=catalog.craft;
    if(!RIVERS?.length || !STATES?.length || !CRAFT?.length)throw new Error("Invalid catalog");
  } catch {
    $("locationPromptText").textContent="The river catalog could not load. Reload the page to try again.";
    return;
  }
  document.querySelector(".coming-soon-pill").textContent=STATES.map(s=>s.name).join(" · ");
  document.querySelector(".nav-drop-menu").innerHTML='<a href="/directory.html">All rivers</a>'+STATES.map(s=>`<a href="/${esc(s.slug)}">${esc(s.name)}</a>`).join("");
  $("year").textContent = new Date().getFullYear();
  $("statRivers").textContent = RIVERS.length;
  $("statSections").textContent = RIVERS.reduce((n, r) => n + r.sections.length, 0);
  const stateSel = $("stateSelect"), riverSel = $("riverSelect"), reportRiverSel = $("reportRiver"), craftSel = $("craftSelect");
  function placeholder(select, text) {
    const option = new Option(text, ""); option.disabled = true; option.selected = true; select.add(option);
  }
  placeholder(stateSel, "Choose a state");
  for (const st of STATES) stateSel.add(new Option(st.name, st.id));
  for (const c of CRAFT) craftSel.add(new Option(c.label, c.id));
  state.craft = CRAFT[0];
  placeholder(reportRiverSel, "Choose a river");
  for (const st of STATES) {
    const group = document.createElement("optgroup"); group.label = st.name;
    for (const r of RIVERS.filter(r => riverState(r) === st.id)) group.appendChild(new Option(r.name, r.id));
    reportRiverSel.appendChild(group);
  }
  function fillRivers(code, id) {
    riverSel.replaceChildren(); placeholder(riverSel, code ? "Choose a river" : "Choose a state first");
    for (const r of RIVERS.filter(r => riverState(r) === code)) riverSel.add(new Option(r.name, r.id));
    riverSel.disabled = !code;
    if (id) riverSel.value = id;
  }
  function showPopular(code) {
    const selected = STATES.find(s => s.id === code);
    $("explorePrompt").hidden = !!selected;
    $("popularContent").hidden = !selected;
    if (!selected) { $("popularPanels").replaceChildren(); return; }
    $("popularStateName").textContent = selected.name;
    $("browseRivers").href = "directory.html?state=" + encodeURIComponent(code);
    const featured = {MT:["madison-upper","madison-lower","yellowstone-paradise","gallatin-canyon"], ID:["boise","snake-sf-canyon","henrys-fork-box","payette-main"], OR:["deschutes-maupin","rogue-grants-pass","rogue-wild","mckenzie"]};
    const list = RIVERS.filter(r => riverState(r) === code);
    const chosen = (featured[code] || []).map(id => list.find(r => r.id === id)).filter(Boolean);
    for (const r of list) { if (chosen.length >= 4) break; if (!chosen.includes(r)) chosen.push(r); }
    $("popularPanels").innerHTML = chosen.slice(0,4).map(r => `<li><a href="index.html?river=${encodeURIComponent(r.id)}#calculator">${esc(r.name)}</a><span>${esc(r.sections[0].putIn)} → ${esc(r.sections[0].takeOut)}</span></li>`).join("");
  }
  function syncUrl() {
    const url = new URL(location.href);
    if (stateSel.value) url.searchParams.set("state", stateSel.value); else url.searchParams.delete("state");
    if (state.river) url.searchParams.set("river", state.river.id); else url.searchParams.delete("river");
    url.searchParams.set("craft", state.craft.id);
    if ($("putInTime").value) url.searchParams.set("launch",$("putInTime").value); else url.searchParams.delete("launch");
    if (state.fishing) url.searchParams.set("fishing","1"); else url.searchParams.delete("fishing");
    history.replaceState(null, "", url.pathname + url.search + url.hash);
  }
  function chooseRiver() {
    state.request++;
    state.river = RIVERS.find(r => r.id === riverSel.value) || null;
    const chosen = !!state.river;
    $("riverDash").hidden = !chosen; $("loadError").hidden = true;
    $("locationPrompt").hidden = chosen;
    $("locationPromptText").textContent = stateSel.value ? "Now choose your river to see its live gauges and float sections." : "Choose a state and river to see live flow, weather, and float times.";
    $("statDaylight").parentElement.hidden = !chosen;
    craftSel.disabled = !chosen; $("putInTime").disabled = !chosen; $("fishingToggle").disabled = !chosen;
    reportRiverSel.value = chosen ? state.river.id : "";
    syncUrl(); showPopular(stateSel.value); renderReports();
    if (chosen) {
      const sunset = sunsetToday(state.river.lat, state.river.lon);
      const hrs = sunset ? (sunset-new Date())/3600000 : 0;
      $("statDaylight").textContent = hrs > 0 ? fmtDuration(hrs) : "After sunset";
      renderRiver();
    }
  }
  const params = new URLSearchParams(location.search);
  state.craft=CRAFT.find(c=>c.id===params.get("craft")) || CRAFT[0]; craftSel.value=state.craft.id;
  if (/^\d{2}:\d{2}$/.test(params.get("launch") || "")) $("putInTime").value=params.get("launch");
  state.fishing=params.get("fishing")==="1"; $("fishingToggle").checked=state.fishing;
  const start = RIVERS.find(r => r.id === params.get("river"));
  const code = start ? riverState(start) : STATES.find(st => st.id === (params.get("state") || "").toUpperCase())?.id || "";
  stateSel.value = code; fillRivers(code, start?.id); chooseRiver();
  stateSel.addEventListener("change", () => { fillRivers(stateSel.value); chooseRiver(); });
  riverSel.addEventListener("change", chooseRiver);
  craftSel.addEventListener("change", () => { state.craft=CRAFT.find(c=>c.id===craftSel.value); syncUrl(); if(state.river)renderRiver(); });
  $("putInTime").addEventListener("input", () => {syncUrl();if(state.river)renderSections(state.river,state.gauge,renderDaylight(state.river));});
  $("fishingToggle").addEventListener("change", () => {state.fishing=$("fishingToggle").checked;syncUrl();if(state.river)renderSections(state.river,state.gauge,renderDaylight(state.river));});
  $("filterReports").addEventListener("change", renderReports);
  $("reportForm").addEventListener("submit", submitReport);
  $("reportsList").addEventListener("click", ev=>{if(ev.target.closest("[data-retry-reports]")){loadReports();return;} const btn=ev.target.closest(".vote-btn");if(btn&&!btn.disabled)vote(btn.dataset.id,btn.dataset.action);});
  loadReports();
  setInterval(()=>{if(!document.hidden && state.river) {renderDaylight(state.river);renderSections(state.river,state.gauge,sunsetToday(state.river.lat,state.river.lon));}},60000);
  setInterval(()=>{if(!document.hidden && state.river){renderRiver();loadReports();}},300000);
  document.addEventListener("visibilitychange",()=>{if(!document.hidden && state.river){renderRiver();loadReports();}});
}
init();
