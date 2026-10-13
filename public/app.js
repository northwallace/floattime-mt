// =====================================================================
// FloatETA — application logic
// =====================================================================

const USGS_IV = "https://waterservices.usgs.gov/nwis/iv/";
const SPEED_EXPONENT = 0.34; // hydraulic geometry: v ∝ Q^0.34
const MIN_SPEED_MPH = 0.8;
const MAX_SPEED_MPH = 9.0;
const FLOAT_DAY_HOURS = 10; // sections longer than this at current speed = multi-day
const FISH_MIN_PER_MILE = 35; // extra time if stopping to fish

const $ = (id) => document.getElementById(id);

const state = {
  river: null,          // current river object
  craft: null,          // current craft object
  putIn: null,          // Date for today's put-in, or null if unset
  fishing: false,       // add FISH_MIN_PER_MILE per mile for stop-and-fish floats
  gaugeCache: {},       // gauge id -> { flow, temp, series, fetchedAt }
  weatherCache: {},     // river id -> { airF, windMph }
  reports: [],
  votedIds: new Set(JSON.parse(localStorage.getItem("ft_voted") || "[]")),
};

// ---------------------------------------------------------------------
// Sunset (NOAA simplified algorithm) — good to ~1 minute, plenty here.
// ---------------------------------------------------------------------

function sunsetToday(lat, lon) {
  const now = new Date();
  const start = new Date(now.getFullYear(), 0, 0);
  const dayOfYear = Math.floor((now - start) / 86400000);

  const zenith = 90.833 * Math.PI / 180;
  const latRad = lat * Math.PI / 180;
  const lngHour = lon / 15;
  const t = dayOfYear + (18 - lngHour) / 24; // approx time for sunset

  const M = 0.9856 * t - 3.289;
  let L = M + 1.916 * Math.sin(M * Math.PI / 180) + 0.020 * Math.sin(2 * M * Math.PI / 180) + 282.634;
  L = ((L % 360) + 360) % 360;

  let RA = Math.atan(0.91764 * Math.tan(L * Math.PI / 180)) * 180 / Math.PI;
  RA = ((RA % 360) + 360) % 360;
  RA += Math.floor(L / 90) * 90 - Math.floor(RA / 90) * 90;
  RA /= 15;

  const sinDec = 0.39782 * Math.sin(L * Math.PI / 180);
  const cosDec = Math.cos(Math.asin(sinDec));

  const cosH = (Math.cos(zenith) - sinDec * Math.sin(latRad)) / (cosDec * Math.cos(latRad));
  if (cosH < -1 || cosH > 1) return null; // no sunset (not in MT)

  const H = (Math.acos(cosH) * 180 / Math.PI) / 15;
  const T = H + RA - 0.06571 * t - 6.622;
  let UT = T - lngHour;
  UT = ((UT % 24) + 24) % 24;

  const sunset = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, Math.round(UT * 3600)));
  // If computed sunset landed "yesterday/tomorrow" due to UTC rollover, nudge to same local day
  if (sunset.getDate() !== now.getDate()) sunset.setDate(now.getDate());
  return sunset;
}

function fmtClock(date) {
  return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function fmtDuration(hours) {
  if (hours >= 24) return `${(hours / 24).toFixed(1)} days`;
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  if (h === 0) return `${m} min`;
  if (m === 0) return `${h} hr`;
  return `${h} hr ${m} min`;
}

// ---------------------------------------------------------------------
// Data fetching
// ---------------------------------------------------------------------

async function fetchGauge(siteId) {
  const cached = state.gaugeCache[siteId];
  if (cached && Date.now() - cached.fetchedAt < 10 * 60 * 1000) return cached;

  const url = `${USGS_IV}?format=json&sites=${siteId}&parameterCd=00060,00010&period=P7D&siteStatus=all`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`USGS ${res.status}`);
  const data = await res.json();

  const out = { flow: null, temp: null, series: [], reportedAt: null, fetchedAt: Date.now() };
  for (const ts of data.value.timeSeries) {
    const code = ts.variable.variableCode[0].value;
    const vals = ts.values[0].value.filter((v) => Number(v.value) > -99999);
    if (!vals.length) continue;
    const last = vals[vals.length - 1];
    const latest = Number(last.value);
    if (code === "00060") {
      out.flow = latest;
      out.reportedAt = new Date(last.dateTime).getTime();
      out.series = vals.map((v) => ({ t: new Date(v.dateTime).getTime(), q: Number(v.value) }));
    } else if (code === "00010") {
      out.temp = latest; // °C
    }
  }
  state.gaugeCache[siteId] = out;
  return out;
}

async function fetchWeather(river) {
  if (state.weatherCache[river.id]) return state.weatherCache[river.id];
  try {
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${river.lat}&longitude=${river.lon}` +
      `&current=temperature_2m,wind_speed_10m` +
      `&daily=precipitation_probability_max,uv_index_max,temperature_2m_max,temperature_2m_min` +
      `&temperature_unit=fahrenheit&wind_speed_unit=mph&forecast_days=2`;
    const res = await fetch(url);
    const data = await res.json();
    const daily = data.daily || {};
    const out = {
      airF: Math.round(data.current.temperature_2m),
      windMph: Math.round(data.current.wind_speed_10m),
      rainToday: daily.precipitation_probability_max ? daily.precipitation_probability_max[0] : null,
      rainTomorrow: daily.precipitation_probability_max ? daily.precipitation_probability_max[1] : null,
      uv: daily.uv_index_max ? Math.round(daily.uv_index_max[0]) : null,
      highF: daily.temperature_2m_max ? Math.round(daily.temperature_2m_max[0]) : null,
      lowF: daily.temperature_2m_min ? Math.round(daily.temperature_2m_min[0]) : null,
    };
    state.weatherCache[river.id] = out;
    return out;
  } catch {
    return null; // weather is a nice-to-have; never block the page on it
  }
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
  if (ratio < 0.4)  return { cls: "cond-low",    label: "Low & bony",  note: "Expect to drag in the shallows. Tubes OK, hard boats will scrape.", craft: "Tubes and small rafts. Drift boats will scrape." };
  if (ratio < 0.8)  return { cls: "cond-mellow", label: "Mellow",      note: "Lazy current, relaxed pace. Great tube and family water.", craft: "Anything floats — tubes, SUPs, and rafts." };
  if (ratio < 1.5)  return { cls: "cond-prime",  label: "Prime",       note: "Healthy flow and a good clip. This is the float you came for.", craft: "Rafts, kayaks, and SUPs. Tubes if you're a strong swimmer." };
  if (ratio < 2.5)  return { cls: "cond-high",   label: "High & fast", note: "Pushy water, fewer eddies. Strong swimmers and PFDs only.", craft: "Rafts and kayaks. Leave the tubes at home." };
  return               { cls: "cond-danger", label: "Runoff — caution", note: "Flood-stage water moves wood and eats boats. Most floaters should wait.", craft: "Experienced whitewater crews only — or wait it out." };
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
  if (uv <= 2) return `${uv} low`;
  if (uv <= 5) return `${uv} mod`;
  if (uv <= 7) return `${uv} high`;
  return `${uv} very high`;
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
  if (!sunset) return null;
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
  return sunset;
}

function parsePutIn(value) {
  if (!value) return null;
  const [h, m] = value.split(":").map(Number);
  if (Number.isNaN(h) || Number.isNaN(m)) return null;
  const d = new Date();
  d.setHours(h, m, 0, 0);
  return d;
}

function takeOutTime(putIn, hoursOnWater, isMultiDay) {
  if (isMultiDay) {
    const days = Math.max(1, Math.round(hoursOnWater / 7));
    const finish = new Date(putIn.getTime());
    finish.setDate(finish.getDate() + days - 1);
    finish.setHours(putIn.getHours() + 7, putIn.getMinutes(), 0, 0); // ~7 hrs floating that last day
    return { finish, days };
  }
  return { finish: new Date(putIn.getTime() + hoursOnWater * 3600000), days: 1 };
}

function renderSections(river, flow, sunset) {
  const speed = riverSpeedMph(river, flow) * state.craft.mult;
  const container = $("sectionCards");
  container.innerHTML = "";
  const now = new Date();

  for (const sec of river.sections) {
    const driftHours = sec.miles / speed;
    const fishHours = state.fishing ? sec.miles * (FISH_MIN_PER_MILE / 60) : 0;
    const hours = driftHours + fishHours;
    const card = document.createElement("div");
    card.className = "float-card";

    const isMultiDay = river.multiDay || hours > FLOAT_DAY_HOURS;

    let timeDisplay = fmtDuration(hours);
    let launchHtml = "";
    let etaHtml = "";
    if (isMultiDay) {
      const days = Math.max(1, Math.round(hours / 7)); // ~7 floating hrs/day
      timeDisplay = `~${days} day${days > 1 ? "s" : ""}`;
      launchHtml = `<div class="fc-launch ok"><span class="multi-day-badge">Multi-day</span> &nbsp;About ${Math.round(hours)} total hours on the water, at ~7 floating hrs per day.</div>`;
    } else if (sunset && !state.putIn) {
      const latestLaunch = new Date(sunset.getTime() - hours * 3600000 - 30 * 60000); // 30 min buffer
      const minutesUntilLatest = (latestLaunch - now) / 60000;
      if (minutesUntilLatest > 90) {
        launchHtml = `<div class="fc-launch ok">☀️ Launch by <strong>${fmtClock(latestLaunch)}</strong> to take out before sunset.</div>`;
      } else if (minutesUntilLatest > 0) {
        launchHtml = `<div class="fc-launch tight">⏳ Tight — launch by <strong>${fmtClock(latestLaunch)}</strong> (${Math.round(minutesUntilLatest)} min from now).</div>`;
      } else {
        launchHtml = `<div class="fc-launch no">🌙 Not enough daylight left for this one today.</div>`;
      }
    }

    if (state.putIn) {
      const { finish, days } = takeOutTime(state.putIn, hours, isMultiDay);
      const afterDark = sunset && finish > sunset && days === 1;
      const dayNote = days > 1
        ? ` on day ${days} (${finish.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" })})`
        : "";
      etaHtml = `
        <div class="fc-eta">
          <div class="fc-eta-leg"><span class="fc-eta-label">Put in</span><span class="fc-eta-time">${fmtClock(state.putIn)}</span></div>
          <div class="fc-eta-arrow" aria-hidden="true">→</div>
          <div class="fc-eta-leg"><span class="fc-eta-label">Take out</span><span class="fc-eta-time">~${fmtClock(finish)}${dayNote}</span></div>
        </div>`;
      if (afterDark) {
        launchHtml = `<div class="fc-launch no">🌙 That take-out is after sunset (${fmtClock(sunset)}). Launch earlier or pick a shorter stretch.</div>`;
      } else if (sunset && days === 1) {
        const slackMin = Math.round((sunset - finish) / 60000);
        if (slackMin >= 0 && slackMin < 45) {
          launchHtml = `<div class="fc-launch tight">⏳ You'll make sunset with about ${slackMin} min to spare.</div>`;
        } else if (slackMin >= 45) {
          launchHtml = `<div class="fc-launch ok">☀️ On the water ${fmtDuration(hours)}. Take-out before sunset (${fmtClock(sunset)}).</div>`;
        }
      }
    }

    const hazards = state.reports.filter((r) => r.river === river.name && (!r.section || r.section === `${sec.putIn} → ${sec.takeOut}`));
    const hazardHtml = hazards.length
      ? `<div class="fc-hazard">⚠️ ${hazards.length} active obstruction report${hazards.length > 1 ? "s" : ""} on this river — see River Reports below.</div>`
      : "";

    card.innerHTML = `
      <div class="fc-route">${esc(sec.putIn)}<span class="arrow">→</span>${esc(sec.takeOut)}</div>
      <div class="fc-meta">
        <span>${sec.miles} mi</span>
        <span class="diff">${esc(sec.difficulty)}</span>
      </div>
      <div class="fc-time"><span class="fc-time-label">${state.fishing ? "Estimated time (fishing)" : "Estimated float time"}</span>${timeDisplay}</div>
      ${etaHtml}
      <div class="fc-speed">~${speed.toFixed(1)} mph in a ${state.craft.label.toLowerCase().split(" (")[0]} at ${flow.toLocaleString()} cfs${state.fishing ? ` · plus ${FISH_MIN_PER_MILE} min/mi for fishing (${fmtDuration(fishHours)} extra)` : ""}</div>
      ${launchHtml}
      ${hazardHtml}
      <div class="fc-notes">${esc(sec.notes)}</div>
    `;
    container.appendChild(card);
  }
}

async function renderRiver() {
  const river = state.river;
  $("riverDash").hidden = false;
  $("loadError").hidden = true;
  $("riverBlurb").textContent = river.blurb;
  $("gaugeName").textContent = `USGS ${river.gauge} — ${river.gaugeName}`;
  $("packWear").textContent = "Checking the put-in…";
  $("rainToday").textContent = "–";
  $("rainTomorrow").textContent = "–";
  $("uvIndex").textContent = "–";
  $("packHighLow").textContent = "";

  const sunset = renderDaylight(river);

  // weather (non-blocking)
  $("airTemp").textContent = "–";
  $("windSpeed").textContent = "–";
  fetchWeather(river).then((w) => {
    if (!(w && state.river === river)) return;
    $("airTemp").textContent = `${w.airF}°F`;
    $("windSpeed").textContent = `${w.windMph} mph`;
    $("rainToday").textContent = w.rainToday != null ? `${w.rainToday}%` : "n/a";
    $("rainTomorrow").textContent = w.rainTomorrow != null ? `${w.rainTomorrow}%` : "n/a";
    $("uvIndex").textContent = uvLabel(w.uv);
    if (w.highF != null && w.lowF != null) {
      $("packHighLow").textContent = `Put-in high ${w.highF}° / low ${w.lowF}° today`;
    }
  });

  let gauge;
  try {
    gauge = await fetchGauge(river.gauge);
  } catch (e) {
    $("riverDash").hidden = true;
    $("loadError").hidden = false;
    return;
  }
  if (state.river !== river) return; // user switched rivers mid-fetch

  if (gauge.flow == null) {
    $("riverDash").hidden = true;
    $("loadError").hidden = false;
    $("loadError").textContent = "This gauge isn't reporting flow right now. Try another river.";
    return;
  }

  $("flowValue").textContent = gauge.flow.toLocaleString();
  const trend = trendFor(gauge.series);
  const trendEl = $("flowTrend");
  trendEl.textContent = trend.text;
  trendEl.className = `dash-sub ${trend.cls}`;
  drawSparkline($("sparkline"), gauge.series);

  const cond = conditionFor(river, gauge.flow);
  const badge = $("conditionBadge");
  badge.textContent = cond.label;
  badge.className = `condition-badge ${cond.cls}`;
  $("conditionNote").textContent = cond.note;
  $("craftHint").textContent = cond.craft;
  $("waterTemp").textContent = gauge.temp != null ? waterTempLabel(gauge.temp) : "n/a";
  $("packWear").textContent = dressFor(gauge.temp);
  const age = gaugeAge(gauge.reportedAt);
  $("gaugeName").textContent = `USGS ${river.gauge} — ${river.gaugeName} · ${age}`;

  renderSections(river, gauge.flow, sunset);
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
  try {
    const res = await fetch("/api/reports");
    state.reports = await res.json();
  } catch {
    state.reports = [];
  }
  renderReports();
}

function renderReports() {
  const list = $("reportsList");
  const filterOn = $("filterReports").checked;
  let reports = state.reports;
  if (filterOn && state.river) reports = reports.filter((r) => r.river === state.river.name);

  if (!reports.length) {
    list.innerHTML = `<div class="reports-empty">No reports${filterOn ? " for this river" : ""} yet. If the water's clean, that's good news — if you spot something, report it!</div>`;
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
          <button class="vote-btn" data-id="${r.id}" data-action="confirm" ${voted ? "disabled" : ""}>👍 Still there (${r.confirmVotes || 0})</button>
          <button class="vote-btn" data-id="${r.id}" data-action="cleared" ${voted ? "disabled" : ""}>✅ Cleared (${r.clearedVotes || 0})</button>
        </span>
      </div>
    `;
    list.appendChild(card);
  }
}

async function vote(id, action) {
  state.votedIds.add(id);
  localStorage.setItem("ft_voted", JSON.stringify([...state.votedIds]));
  try {
    await fetch(`/api/reports/${id}/${action}`, { method: "POST" });
  } catch { /* best effort */ }
  loadReports();
}

async function submitReport(ev) {
  ev.preventDefault();
  const btn = $("reportSubmit");
  const status = $("reportStatus");
  btn.disabled = true;
  status.className = "report-status";
  status.textContent = "Submitting…";

  const body = {
    river: $("reportRiver").value,
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
    $("reportRiver").value = body.river;
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

function init() {
  $("year").textContent = new Date().getFullYear();

  // hero stats
  $("statRivers").textContent = RIVERS.length;
  $("statSections").textContent = RIVERS.reduce((n, r) => n + r.sections.length, 0);
  const sunset = sunsetToday(46.6, -112.0); // Montana-ish centroid for the hero stat
  if (sunset) {
    const hrs = (sunset - new Date()) / 3600000;
    $("statDaylight").textContent = hrs > 0 ? fmtDuration(hrs).replace(" min", "m").replace(" hr", "h") : "0";
  }

  // selectors
  const riverSel = $("riverSelect");
  const reportRiverSel = $("reportRiver");
  for (const r of RIVERS) {
    riverSel.add(new Option(r.name, r.id));
    reportRiverSel.add(new Option(r.name, r.name));
  }
  const craftSel = $("craftSelect");
  for (const c of CRAFT) craftSel.add(new Option(c.label, c.id));

  const wanted = new URLSearchParams(location.search).get("river");
  if (wanted && RIVERS.some((r) => r.id === wanted)) {
    riverSel.value = wanted;
  }

  state.river = RIVERS.find((r) => r.id === riverSel.value) || RIVERS[0];
  state.craft = CRAFT[0];
  reportRiverSel.value = state.river.name;

  function syncRiverUrl() {
    const url = new URL(location.href);
    url.searchParams.set("river", state.river.id);
    history.replaceState(null, "", url.pathname + url.search + url.hash);
  }

  riverSel.addEventListener("change", () => {
    state.river = RIVERS.find((r) => r.id === riverSel.value);
    reportRiverSel.value = state.river.name;
    syncRiverUrl();
    renderRiver();
    if ($("filterReports").checked) renderReports();
  });
  craftSel.addEventListener("change", () => {
    state.craft = CRAFT.find((c) => c.id === craftSel.value);
    renderRiver();
  });
  $("putInTime").addEventListener("input", () => {
    state.putIn = parsePutIn($("putInTime").value);
    renderRiver();
  });
  $("fishingToggle").addEventListener("change", () => {
    state.fishing = $("fishingToggle").checked;
    renderRiver();
  });

  $("filterReports").addEventListener("change", renderReports);
  $("reportForm").addEventListener("submit", submitReport);
  $("reportsList").addEventListener("click", (ev) => {
    const btn = ev.target.closest(".vote-btn");
    if (btn && !btn.disabled) vote(btn.dataset.id, btn.dataset.action);
  });

  loadReports().then(renderRiver);

  // refresh daylight countdown every minute
  setInterval(() => { if (state.river) renderDaylight(state.river); }, 60000);
}

init();
