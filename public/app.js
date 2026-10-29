// =====================================================================
// FloatETA — application logic
// =====================================================================

const P = FloatPlanner;
let RIVERS = [], STATES = [], CRAFT = [];
const gaugeCache = new Map(), weatherCache = new Map();
const SPEED_EXPONENT = 0.34; // hydraulic geometry: v ∝ Q^0.34
const MIN_SPEED_MPH = 0.8;
const MAX_SPEED_MPH = 9.0;
const FLOAT_DAY_HOURS = 10; // sections longer than this at current speed = multi-day
const FISH_MIN_PER_MILE = 25; // extra time if stopping to fish
const MAPLIBRE_VERSION = "5.15.0";
const MAPLIBRE_JS = `https://unpkg.com/maplibre-gl@${MAPLIBRE_VERSION}/dist/maplibre-gl.js`;
const MAPLIBRE_CSS = `https://unpkg.com/maplibre-gl@${MAPLIBRE_VERSION}/dist/maplibre-gl.css`;
// Browser-visible, referrer-restricted map key comes from runtime configuration.
// Never place account credentials or private application secrets here.
function satelliteMapStyle(apiKey) {
  if (typeof apiKey !== "string" || !apiKey.trim()) throw new Error("Satellite maps are not configured.");
  const token = encodeURIComponent(apiKey);
  return {
    version: 8,
    sources: {
      "world-imagery": {
        type: "raster",
        tiles: [`https://ibasemaps-api.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}?token=${token}`],
        tileSize: 256, maxzoom: 23,
        attribution: 'Powered by <a href="https://www.esri.com/" target="_blank" rel="noopener">Esri</a> &mdash; Esri, Vantor, GeoEye, Earthstar Geographics, CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS User Community',
      },
      "imagery-labels": {
        type: "raster",
        tiles: [`https://static-map-tiles-api.arcgis.com/arcgis/rest/services/static-basemap-tiles-service/v1/arcgis/imagery/labels/static/tile/{z}/{y}/{x}?token=${token}`],
        tileSize: 512, maxzoom: 22,
        attribution: 'Esri, TomTom, Garmin, FAO, NOAA, USGS, &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a>, and the GIS User Community',
      },
    },
    layers: [
      {id: "world-imagery", type: "raster", source: "world-imagery"},
      {id: "imagery-labels", type: "raster", source: "imagery-labels"},
    ],
  };
}
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
  landMap: null,
  landMapSection: null,
};

let mapLibraryPromise;

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

function loadMapLibrary() {
  if (window.maplibregl) return Promise.resolve(window.maplibregl);
  if (mapLibraryPromise) return mapLibraryPromise;
  mapLibraryPromise = new Promise((resolve, reject) => {
    if (!document.querySelector(`link[href="${MAPLIBRE_CSS}"]`)) {
      const link = document.createElement("link");
      link.rel = "stylesheet"; link.href = MAPLIBRE_CSS;
      document.head.appendChild(link);
    }
    const script = document.createElement("script");
    script.src = MAPLIBRE_JS; script.async = true;
    script.onload = () => resolve(window.maplibregl);
    script.onerror = () => reject(new Error("The map library could not load."));
    document.head.appendChild(script);
  });
  return mapLibraryPromise;
}

function closeLandMap() {
  state.mapGeneration = (state.mapGeneration || 0) + 1;
  state.progress?.destroy(); state.progress = null;
  $("landMapRouteEvidence").hidden = true;
  if (state.landMapSection) {
    const url = new URL(location.href);
    url.searchParams.delete("section"); url.searchParams.delete("map");
    history.replaceState(null, "", url.pathname + url.search + url.hash);
  }
  $("landMapPanel").hidden = true;
  state.landMapSection = null;
  if (state.landMap) {
    state.landMap.remove();
    state.landMap = null;
  }
  $("landMap").replaceChildren();
}

function parcelPopup(properties = {}) {
  const popup = document.createElement("div");
  const title = document.createElement("strong");
  title.textContent = `Montana trust tract ${properties.TractID || ""}`.trim();
  popup.appendChild(title);
  const rows = [
    ["Access", properties.Access_Type],
    ["Special access", properties.Access_Type_Spcl],
    ["Whole tract acres", properties.Acres && Number(properties.Acres).toLocaleString()],
    ["Verification", properties.Verified ? `${properties.Verified} in DNRC data` : null],
  ];
  for (const [label, value] of rows) {
    if (!value) continue;
    const row = document.createElement("p");
    row.textContent = `${label}: ${value}`;
    popup.appendChild(row);
  }
  const note = document.createElement("small");
  note.textContent = "Check current signs, closures, and license rules before entering.";
  popup.appendChild(note);
  return popup;
}

function riverBankLabel(access) {
  if (access?.status === "access-verified") return "";
  if (access?.riverBank === "river-left") return "River left";
  if (access?.riverBank === "river-right") return "River right";
  return "";
}

function prepareSectionRoute(data, river, section, experiment = false) {
  if (data.riverId !== river.id || data.sectionId !== section.id || data.catalogMiles !== section.miles) throw new Error("Route does not match section");
  if (!experiment && (data.status !== "reviewed" || data.features?.display !== true)) throw new Error("Route is not reviewed for display");
  for (const [saved, current, name] of [[data.putIn, section.putInCoords, section.putIn], [data.takeOut, section.takeOutCoords, section.takeOut]]) {
    if (saved?.lat !== current.lat || saved?.lon !== current.lon || (!experiment && saved.name !== name)) throw new Error("Route endpoints need review");
  }
  return FloatRoute.prepare(data);
}

function mountFloatProgress(map, maplibregl, data, route, river, section, fieldTest = false) {
  const box = $("floatProgress"), result = $("floatProgressResult"), detail = $("floatProgressDetail");
  let fix = null, demo = false, marker = null;
  box.hidden = false;
  $("floatProgressTag").textContent = fieldTest ? "Field test · estimate" : "Local pilot";
  $("fieldPilotNote").hidden = !fieldTest;
  $("fieldPilotNote").textContent = fieldTest ? "To the user-confirmed Greycliff takeout pin. Side channels, wind, rowing and stops can change your time. Keep this page open for updates; confirm the landing visually." : "";
  $("floatProgressSource").href = data.sourceUrl;
  $("progressDemo").hidden = fieldTest;
  $("progressDemo").open = false;
  $("progressDemoControls").hidden = true;
  $("progressDemoPosition").value = "50";
  $("progressDemoQuality").value = "good";
  function refresh() {
    let current = fix;
    const prefix = demo ? "Demo · " : "";
    if (demo) {
      const point = FloatProgress.pointAt(route, Number($("progressDemoPosition").value) / 100);
      const quality = $("progressDemoQuality").value;
      if (quality === "off") point[1] += .02;
      current = {longitude:point[0], latitude:point[1], accuracy:quality === "poor" ? 200 : 10, timestamp:Date.now() - (quality === "stale" ? 60000 : 0)};
      marker.setLngLat(point);
    }
    const position = FloatProgress.locate(route, current);
    const messages = {
      missing:"Use the location button on the map to estimate what’s left.",
      stale:"Waiting for a fresh location—time remaining is paused.",
      inaccurate:"GPS is too imprecise to estimate time remaining.",
      "off-route":"Location is away from this river section. No estimate available.",
      ambiguous:"Nearby river bends make your position uncertain. No estimate available.",
      "near-takeout":"Near the take-out—confirm the landing and river bank.",
    };
    result.textContent = prefix + (messages[position.status] || "Calculating…");
    detail.textContent = demo ? "Simulated position · example flow 1,200 cfs · not your GPS" : "Waiting for a clear, recent GPS reading on this section.";
    if (!["on-route", "near-takeout"].includes(position.status)) return;
    detail.textContent = `${prefix}${position.remainingMiles.toFixed(1)} mapped river miles remaining · ${state.craft.label || state.craft.id}`;
    if (position.status === "near-takeout") return;
    const gauge = demo ? {flow:1200, at:Date.now()} : state.gauge;
    const restricted = /\b(?:III|IV|V|VI)\b/.test(section.difficulty) && ["tube", "sup"].includes(state.craft.id);
    const estimate = !restricted && P.fresh(gauge) && P.estimate(river, {...section,miles:position.remainingMiles}, gauge.flow, state.craft.mult, state.fishing ? position.remainingMiles * FISH_MIN_PER_MILE : 0);
    if (!estimate) {
      result.textContent = prefix + "Distance available; time estimate unavailable.";
      detail.textContent += restricted ? " · This craft is not supported on this section." : " · A fresh flow reading and supported timing model are required.";
      return;
    }
    result.textContent = `${prefix}About ${P.duration(Math.max(15, Math.round(estimate.rawMinutes / 15) * 15))} remaining`;
    detail.textContent += ` · ${demo ? "example" : "current"} flow ${Math.round(gauge.flow).toLocaleString()} cfs · ${state.fishing ? "includes 25 min/mile of future fishing stops" : "excludes stops"}`;
  }
  function stopDemo() {
    demo = false; marker?.remove(); marker = null;
    $("progressDemoControls").hidden = true;
    $("progressDemoStart").hidden = false;
    refresh();
  }
  $("progressDemoStart").onclick = () => {
    if (fieldTest) return;
    demo = true;
    const el = document.createElement("div"); el.className = "progress-demo-marker"; el.textContent = "D"; el.setAttribute("aria-label", "Simulated position");
    marker = new maplibregl.Marker({element:el}).setLngLat(FloatProgress.pointAt(route, .5)).addTo(map);
    $("progressDemoControls").hidden = false; $("progressDemoStart").hidden = true;
    refresh();
  };
  $("progressDemoStart").hidden = false;
  $("progressDemoStop").onclick = stopDemo;
  $("progressDemoPosition").oninput = refresh;
  $("progressDemoQuality").onchange = refresh;
  const timer = setInterval(refresh, 5000);
  refresh();
  return {
    refresh,
    update(event) { fix = {longitude:event.coords.longitude, latitude:event.coords.latitude, accuracy:event.coords.accuracy, timestamp:event.timestamp}; if (demo) stopDemo(); else refresh(); },
    unavailable() { fix = null; refresh(); },
    destroy() {
      clearInterval(timer); marker?.remove(); box.hidden = true;
      $("progressDemoStart").onclick = $("progressDemoStop").onclick = $("progressDemoPosition").oninput = $("progressDemoQuality").onchange = null;
    },
  };
}

async function showLandMap(section) {
  if (!section.mapReleased || section.accessReview) return;
  const panel = $("landMapPanel"), status = $("landMapStatus"), locationStatus = $("landMapLocationStatus");
  const isMontana = riverState(state.river) === "MT";
  closeLandMap();
  state.landMapSection = section.id;
  const generation = state.mapGeneration, river = state.river;
  const mapUrl = new URL(location.href);
  mapUrl.searchParams.set("section", section.id); mapUrl.searchParams.set("map", "1");
  history.replaceState(null, "", mapUrl.pathname + mapUrl.search + mapUrl.hash);
  panel.hidden = false;
  const takeOutBank = riverBankLabel(section.takeOutAccess);
  $("landMapAccuracy").textContent = section.distanceReview ? "Route and distance under review" : section.mapPrecision === "approximate" ? "Approximate access locations" : "Verified access facilities";
  $("landMapRoute").textContent = `${section.putIn} → ${section.takeOut}${takeOutBank ? ` · Take-out: ${takeOutBank.toLowerCase()}` : ""}`;
  $("landMapPanel").querySelector("h3").textContent = isMontana ? "River access and Montana state land" : "River access map";
  $("landMapLandLegend").hidden = !isMontana;
  $("landMapLandNote").hidden = !isMontana;
  $("landMapLandNote").textContent = "Trust-land boundaries and access details are approximate. State ownership does not guarantee unrestricted access. Verify signs, closures, and current license requirements before leaving the river.";
  status.textContent = "Loading river access and available map layers…";
  locationStatus.textContent = navigator.geolocation
    ? "Tap the target button to show your approximate location. Float ETA does not save it; the map provider receives the area needed to draw the map."
    : "Location is unavailable in this browser.";
  panel.scrollIntoView({behavior:"smooth", block:"nearest"});
  try {
    const fieldTestId = new URL(location.href).searchParams.get("fieldtest") || "";
    const [maplibregl, mapConfig] = await Promise.all([loadMapLibrary(), json("/api/map-config" + (fieldTestId ? "?fieldtest=" + encodeURIComponent(fieldTestId) : ""))]);
    if (generation !== state.mapGeneration) return;
    let pilot = null, route = null, routeUnavailable = false, fieldTest = false;
    const testEntry = FloatFieldPilot.matches(mapConfig.fieldTest, fieldTestId, river, section) ? mapConfig.fieldTest : null;
    const entry = testEntry || (mapConfig.routes || mapConfig.routePilots)?.find(item => item.riverId === river.id && item.sectionId === section.id);
    if (entry) {
      try {
        let data;
        if (testEntry) {
          const response = await fetch("/" + entry.file, {signal:AbortSignal.timeout(15000), cache:"no-store"});
          if (!response.ok) throw Error("Pilot unavailable");
          const raw = await response.arrayBuffer();
          const digest = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", raw)), byte => byte.toString(16).padStart(2,"0")).join("");
          if (digest !== entry.sha256) throw Error("Pilot changed; refresh required");
          data = JSON.parse(new TextDecoder().decode(raw));
          if (!FloatFieldPilot.matches(data, fieldTestId, river, section)) throw Error("Pilot identity mismatch");
        } else data = await json("/" + entry.file);
        if (generation !== state.mapGeneration) return;
        route = testEntry ? FloatFieldPilot.prepare(data, river, section) : prepareSectionRoute(data, river, section, !mapConfig.routes);
        fieldTest = !!testEntry;
        pilot = data;
      } catch {
        if (generation !== state.mapGeneration) return;
        routeUnavailable = true; // Keep the existing access map usable.
      }
    }
    const takeOutPoint = fieldTest ? pilot.takeOut : section.takeOutCoords;
    const points = [section.putInCoords, takeOutPoint];
    if (fieldTest) $("landMapAccuracy").textContent = "Field test · user-confirmed takeout";
    const bounds = new maplibregl.LngLatBounds();
    for (const point of points) bounds.extend([point.lon, point.lat]);
    if (route) for (const point of route.coordinates) bounds.extend(point);
    const style = satelliteMapStyle(mapConfig.arcgisApiKey);
    if (fieldTest) {
      // The pilot needs imagery and its river path, without depending on the
      // separately licensed optional labels service to initialize GPS timing.
      delete style.sources["imagery-labels"];
      style.layers = style.layers.filter(layer => layer.id !== "imagery-labels");
    }
    const map = new maplibregl.Map({
      container: "landMap",
      style,
      bounds,
      // Leave room for expanded provider credits so they do not cover a landing.
      fitBoundsOptions: {padding: {top:54, left:54, right:54, bottom:$("landMap").clientWidth < 640 ? 150 : 100}},
      attributionControl: false,
    });
    state.landMap = map;
    map.addControl(new maplibregl.NavigationControl({showCompass:false}), "top-right");
    const geolocate = new maplibregl.GeolocateControl({
      positionOptions: {enableHighAccuracy:true},
      trackUserLocation: true,
      showUserHeading: true,
      showAccuracyCircle: true,
      fitBoundsOptions: {maxZoom:16},
    });
    map.addControl(geolocate, "top-right");
    const geolocateButton = map.getContainer().querySelector(".maplibregl-ctrl-geolocate");
    if (!geolocateButton || geolocateButton.disabled) {
      locationStatus.textContent = "Location is unavailable in this browser. On a phone, open the HTTPS site in Safari or Chrome and allow location access.";
    }
    geolocate.on("geolocate", event => {
      state.progress?.update(event);
      locationStatus.textContent = "Your approximate location is shown in blue. Float ETA does not save it; the map provider receives the area needed to draw the map.";
    });
    geolocate.on("error", event => {
      state.progress?.unavailable();
      locationStatus.textContent = event?.code === 1
        ? "Location permission was not granted. You can enable it in your browser settings."
        : "Your location could not be determined. GPS can be unreliable in canyons or without a clear sky view.";
    });
    map.addControl(new maplibregl.AttributionControl({compact:true}), "bottom-right");
    for (const [point, access, label, className] of [
      [section.putInCoords, section.putInAccess, section.putIn, "put-in"],
      [takeOutPoint, section.takeOutAccess, section.takeOut, "take-out"],
    ]) {
      const marker = document.createElement("button");
      marker.type = "button"; marker.className = `access-marker ${className}`;
      const reportedTakeout = fieldTest && className === "take-out";
      const approximate = access.status === "access-verified" && !reportedTakeout;
      if (approximate) marker.className += " approximate-access";
      marker.textContent = (className === "put-in" ? "P" : "T") + (reportedTakeout ? "*" : approximate ? "~" : "");
      marker.setAttribute("aria-label", `${className === "put-in" ? "Put-in" : "Take-out"}: ${label}`);
      const popup = document.createElement("div");
      const title = document.createElement("strong"); title.textContent = label; popup.appendChild(title);
      const detail = document.createElement("p"); detail.textContent = `${access.accessType || "Access area"}${access.operator ? ` · ${access.operator}` : ""}`; popup.appendChild(detail);
      if (reportedTakeout) {
        const reported = document.createElement("p");
        reported.textContent = `User-confirmed takeout · ${takeOutPoint.lat.toFixed(6)}, ${takeOutPoint.lon.toFixed(6)}. Checked against imagery; not an agency-surveyed landing. Confirm the ramp visually.`;
        popup.appendChild(reported);
      }
      if (approximate) {
        const accuracy = document.createElement("p");
        accuracy.textContent = "Approximate facility location. Exact landing is not confirmed. " + access.directions;
        popup.appendChild(accuracy);
      }
      const bank = riverBankLabel(access);
      if (className === "take-out" && bank) {
        const bankRow = document.createElement("p");
        bankRow.className = "popup-bank";
        bankRow.textContent = `${bank} while facing downstream`;
        popup.appendChild(bankRow);
      }
      const source = document.createElement("a"); source.href = access.sourceUrl; source.target = "_blank"; source.rel = "noopener"; source.textContent = `Access source · checked ${access.verifiedOn}`; popup.appendChild(source);
      if (className === "take-out" && access.bankSourceUrl) {
        const bankSource = document.createElement("a");
        bankSource.className = "popup-bank-source"; bankSource.href = access.bankSourceUrl; bankSource.target = "_blank"; bankSource.rel = "noopener";
        bankSource.textContent = `Bank side source · checked ${access.bankVerifiedOn}`;
        popup.appendChild(bankSource);
      }
      const phoneMap = map.getContainer().clientWidth < 640;
      const accessPopup = new maplibregl.Popup({offset:18, maxWidth:"230px", ...(phoneMap ? {anchor:"bottom"} : {})}).setDOMContent(popup);
      if (phoneMap) accessPopup.on("open", () => {
        // Keep the whole source card inside a narrow map when a marker is tapped.
        const container = map.getContainer();
        const creditsHeight = container.querySelector(".maplibregl-ctrl-attrib")?.getBoundingClientRect().height || 0;
        const offsetY = Math.min(70, container.clientHeight / 2 - creditsHeight - 28);
        map.panTo([point.lon, point.lat], {offset:[0,offsetY], duration:0});
      });
      new maplibregl.Marker({element:marker}).setLngLat([point.lon, point.lat]).setPopup(accessPopup).addTo(map);
    }
    await new Promise((resolve, reject) => {
      map.once("load", resolve);
      map.once("error", event => reject(event.error || new Error("The basemap could not load.")));
    });
    if (geolocateButton?.disabled) {
      locationStatus.textContent = "Location is unavailable in this browser. On a phone, open the HTTPS site in Safari or Chrome and allow location access.";
    }
    if (generation !== state.mapGeneration) return;
    if (!isMontana) {
      status.textContent = section.mapPrecision === "approximate"
        ? "Markers with ~ show approximate facility locations, not confirmed landings. Open each marker for access directions and sources."
        : `Access sources checked: put-in ${section.putInAccess.verifiedOn}; take-out ${section.takeOutAccess.verifiedOn}.`;
      return;
    }
    // Only reviewed river corridors identify land near the float. An endpoint
    // bounding box includes unrelated inland properties, especially on long trips.
    const landUnavailable = !pilot?.land;
    const parcels = {type:"FeatureCollection", features:pilot?.land?.features || []};
    $("landMapLandLegend").hidden = landUnavailable;
    $("landMapLandNote").hidden = landUnavailable;
    if (landUnavailable) $("landMapPanel").querySelector("h3").textContent = "River access map";
    map.addSource("mt-trust-land", {type:"geojson", data:parcels});
    const accessColors = ["match", ["get","mapAccess"], "public","#3f8d60", "special","#d7a93b", "no","#b95d4b", "#7a857d"];
    map.addLayer({id:"mt-trust-land-fill", type:"fill", source:"mt-trust-land", paint:{"fill-color":accessColors,"fill-opacity":.3}});
    map.addLayer({id:"mt-trust-land-line", type:"line", source:"mt-trust-land", paint:{"line-color":accessColors,"line-width":2}});
    map.on("click", "mt-trust-land-fill", event => {
      const feature = event.features?.[0];
      if (!feature) return;
      new maplibregl.Popup().setLngLat(event.lngLat).setDOMContent(parcelPopup(feature.properties)).addTo(map);
    });
    map.on("mouseenter", "mt-trust-land-fill", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "mt-trust-land-fill", () => { map.getCanvas().style.cursor = ""; });
    if (pilot) {
      map.addSource("pilot-river", {type:"geojson", data:{type:"Feature", properties:{}, geometry:pilot.geometry}});
      map.addLayer({id:"pilot-river-line",type:"line",source:"pilot-river",paint:{"line-color":"#7de4ff","line-width":3,"line-dasharray":[3,2]}});
      if (pilot.land) $("landMapLandNote").textContent = pilot.landNote + " State ownership does not guarantee unrestricted access. Check current DNRC rules and signs.";
      const evidence = $("landMapRouteEvidence"); evidence.hidden = false; evidence.replaceChildren();
      const description = document.createElement("span");
      description.textContent = `Approximate mapped river path: ${pilot.routeMiles.toFixed(1)} mi. Planning distance remains ${section.miles} mi. Dashed line is an agency centerline, not a recommended navigation channel. ` + (fieldTest ? "T* marks the user-confirmed pilot destination; P~ is the approximate put-in area. " : "");
      evidence.appendChild(description);
      const source = document.createElement("a"); source.href = pilot.sourceUrl; source.target = "_blank"; source.rel = "noopener"; source.textContent = `River-line source · checked ${pilot.checkedOn}`; evidence.appendChild(source);
      // The saved GPS experiment is independently opt-in; ordinary route maps never enable it.
      if (fieldTest || (!mapConfig.routes && mapConfig.routePilots && pilot.status === "local-pilot")) state.progress = mountFloatProgress(map, maplibregl, pilot, route, river, section, fieldTest);
    }
    if (routeUnavailable) { $("landMapRouteEvidence").hidden = false; $("landMapRouteEvidence").textContent = "The reviewed river line is unavailable. Access markers remain available."; }
    const verified = fieldTest ? "Pilot takeout: user-confirmed Greycliff ramp, checked against imagery. P~ remains an approximate access-area marker. " : (section.mapPrecision === "approximate"
      ? "Markers with ~ show approximate facility locations, not confirmed landings. " : "") +
      `Access sources checked: put-in ${section.putInAccess.verifiedOn}; take-out ${section.takeOutAccess.verifiedOn}. `;
    status.textContent = verified + (landUnavailable
      ? "Land shading is not shown until a reviewed river corridor is available. Access markers remain visible."
      : `Approximate river line shown dashed. ${parcels.features.length} trust-land tract${parcels.features.length === 1 ? "" : "s"} clipped to within ${pilot.corridorMeters} metres of the river; DNRC data checked ${pilot.landCheckedOn}.`);
  } catch (error) {
    if (generation !== state.mapGeneration) return;
    status.innerHTML = isMontana
      ? `The interactive map could not load. <a href="https://dnrc.mt.gov/TrustLandMaps" target="_blank" rel="noopener">Open the official Montana DNRC map</a>.`
      : "The interactive access map could not load. Use the official source links on this stretch to confirm access details.";
    console.warn("Land map preview failed");
  }
}
function gaugeFor(river) {
  return cached(gaugeCache, river.gauge, () =>
    json(`/api/gauge?site=${encodeURIComponent(river.gauge)}`),
  );
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
  if (!Number.isFinite(river.refFlowCfs) || river.refFlowCfs <= 0) return {cls:"cond-mellow",label:"Live flow",note:"A reference-flow comparison is not established for this river.",craft:"Check agency guidance, access restrictions, and local conditions."};
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
function distanceEvidenceHtml(section) {
  const e = section.distanceEvidence;
  if (!e) return "";
  return `<details class="distance-source"><summary>How this distance was checked</summary><p>${esc(e.note)}</p><a href="${esc(e.sourceUrl)}" target="_blank" rel="noopener">${esc(e.sourceName)}</a><p>River mile ${esc(e.putIn.riverMile)} to ${esc(e.takeOut.riverMile)} · checked ${esc(e.checkedOn)}</p></details>`;
}
function renderSections(river, gauge, sunset) {
  state.progress?.refresh();
  if (state.landMapSection && !river.sections.some(sec => sec.id === state.landMapSection)) closeLandMap();
  const container = $("sectionCards");
  container.replaceChildren();
  const launch = parsePutIn($("putInTime").value);
  for (const sec of river.sections) {
    const stops = state.fishing ? sec.miles * FISH_MIN_PER_MILE : 0;
    const estimate = P.fresh(gauge) ? P.estimate(river, sec, gauge.flow, state.craft.mult, stops) : null;
    const restricted = /\b(?:III|IV|V|VI)\b/.test(sec.difficulty) && ["tube", "sup"].includes(state.craft.id);
    let timing = "", duration = "—", detail = "";
    if (sec.accessReview) {
      timing = `<div class="section-notice"><strong>Access and route under review</strong><p>${esc(sec.accessReview)}</p><p>No trip estimate is offered for this stretch until the access issue is resolved.</p></div>`;
    } else if (sec.distanceReview) {
      timing = `<div class="section-notice"><strong>Distance and endpoints under review</strong><p>${esc(sec.distanceReview)}</p></div>`;
    } else if (restricted) {
      timing = '<p class="fc-launch tight">Class III+ whitewater: no tube or recreational paddleboard estimate. Check local guidance and choose an appropriate craft.</p>';
    } else if (river.timing?.mode === "unavailable") {
      timing = '<p class="fc-launch tight">A live float-time estimate is not available for this river yet.</p>';
    } else if (!estimate) {
      timing = '<p class="fc-launch tight">No recent, positive flow reading is available. A current estimate cannot be calculated.</p>';
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
    const bank = riverBankLabel(sec.takeOutAccess);
    const mapButton = sec.mapReleased && sec.putInCoords && sec.takeOutCoords ? `<div class="map-card-actions"><button class="map-preview-button" type="button" data-map-section="${esc(sec.id)}"><span aria-hidden="true">⌖</span> ${sec.mapPrecision === "approximate" ? "View access map · approximate locations" : (sec.distanceReview ? "Inspect access map · under review" : "View verified access map")} <small>Sources</small></button>${bank ? `<span class="takeout-bank">Take-out: ${bank.toLowerCase()} <small>facing downstream</small></span>` : ""}</div>` : "";
    const mapPending = sec.mapPilot && !sec.mapReleased ? '<p class="map-pending-note">Access maps for this state are being reviewed for release.</p>' : sec.mapPendingReason ? `<div class="map-pending-note"><strong>Map unavailable:</strong> ${esc(sec.mapPendingReason)}</div>` : "";
    const guides = (sec.guideTimes || []).map(g => `<div class="guide-time"><strong>Published guide: ${esc(g.min === g.max ? g.min : `${g.min}–${g.max}`)} ${esc(g.unit)}</strong><p>${esc(g.conditions)}</p><a href="${esc(g.sourceUrl)}" target="_blank" rel="noopener">${esc(g.sourceName)}</a></div>`).join("");
    const notices = (sec.notices || []).map(n => `<div class="section-notice"><strong>${esc(n.title)}</strong><p>${esc(n.text)}</p><a href="${esc(n.sourceUrl)}" target="_blank" rel="noopener">${esc(n.sourceName)}</a><small>Source checked ${esc(n.checkedOn)}</small></div>`).join("");
    const guideNote = guides ? '<p class="fc-notes">Guide times are published planning guidance. They are not adjusted for today’s flow, your craft, fishing stops, or put-in time.</p>' : "";
    const correctionUrl = '/feedback.html?' + new URLSearchParams({type:'correction',riverId:river.id,sectionId:sec.id});
    const correction = `<a class="section-correction" href="${esc(correctionUrl)}">Suggest a correction <span class="sr-only">for ${esc(sec.putIn)} to ${esc(sec.takeOut)}</span></a>`;
    card.innerHTML = `<div class="fc-route">${esc(sec.putIn)}<span class="arrow">→</span>${esc(sec.takeOut)}</div><div class="fc-meta"><span>${sec.distanceEvidence ? "≈ " : ""}${sec.miles} mi${sec.distanceReview || sec.accessReview ? " · unverified" : ""}</span><span class="diff">${sec.accessReview ? "Route under review" : esc(sec.difficulty)}</span></div><div class="fc-time"${(sec.accessReview || sec.distanceReview || river.timing?.mode === "unavailable" || restricted) ? ' hidden' : ''}><span class="fc-time-label">${estimate?.multiDay ? "Total estimated time on water" : state.fishing ? "Estimated time (fishing)" : "Estimated float time"}</span>${duration}</div><div class="fc-speed">${detail}</div>${notices}${timing}${guides}${guideNote}${hazards}<div class="fc-notes">${esc(sec.notes)}</div>${distanceEvidenceHtml(sec)}${mapPending}${mapButton}${correction}`;
    container.appendChild(card);
  }
}

async function renderRiver() {
  const river = state.river, request = ++state.request;
  if (!river) return;
  state.gauge = null;
  $("riverDash").hidden = false;
  const selectedState = STATES.find(item => item.id === riverState(river));
  const permitNotice = $("permitNotice");
  if (selectedState?.permitNotice) {
    permitNotice.hidden = false;
    permitNotice.innerHTML = `${esc(selectedState.permitNotice)} <a href="${esc(selectedState.permitUrl)}" target="_blank" rel="noopener">Check current permit rules</a>.`;
  } else {
    permitNotice.hidden = true;
    permitNotice.replaceChildren();
  }
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
  renderSections(river, null, sunsetToday(river.lat, river.lon));
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
  $("gaugeName").textContent = `USGS ${river.gauge} — ${river.gaugeName} · ${gaugeAge(gauge?.at)}${gauge?.stale ? " · cached reading; USGS refresh unavailable" : ""}`;
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
    const featured = {MT:["madison-upper","madison-lower","yellowstone-paradise","gallatin-canyon"], ID:["boise","snake-sf-canyon","henrys-fork-box","payette-main"], OR:["deschutes-maupin","rogue-grants-pass","rogue-wild","mckenzie"], WA:["yakima-canyon","klickitat","skagit-eagle","wenatchee-leavenworth"], UT:["green-river-flaming-gorge","colorado-river-moab","green-river-labyrinth","san-juan"], AZ:["salt-river-lower","verde-river-camp-verde","verde-river-upper","colorado-river-grand-canyon"]};
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
    if (!state.landMapSection) { url.searchParams.delete("section"); url.searchParams.delete("map"); }
    history.replaceState(null, "", url.pathname + url.search + url.hash);
  }
  function chooseRiver() {
    closeLandMap();
    state.request++;
    state.river = RIVERS.find(r => r.id === riverSel.value) || null;
    const chosen = !!state.river;
    $("riverDash").hidden = !chosen; $("loadError").hidden = true;
    $("locationPrompt").hidden = chosen;
    $("locationPromptText").textContent = stateSel.value ? "Now choose your river to see its live gauges and float sections." : "Choose a state and river to see live flow, weather, and float times.";
    $("statDaylight").parentElement.hidden = !chosen;
    craftSel.disabled = !chosen; $("putInTime").disabled = !chosen; $("fishingToggle").disabled = !chosen;
    const liveTiming = chosen && state.river.timing?.mode !== "unavailable";
    $("putInTime").disabled = !liveTiming;
    $("fishingToggle").disabled = !liveTiming;
    $("putInTime").title = $("fishingToggle").title = chosen && !liveTiming ? "Published guide times are not adjusted for launch time or fishing stops." : "";
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
  const linkedSection = start?.sections.find(sec => sec.id === params.get("section") && sec.mapReleased);
  if (params.get("map") === "1" && linkedSection) showLandMap(linkedSection);
  stateSel.addEventListener("change", () => { fillRivers(stateSel.value); chooseRiver(); });
  riverSel.addEventListener("change", chooseRiver);
  craftSel.addEventListener("change", () => { state.craft=CRAFT.find(c=>c.id===craftSel.value); syncUrl(); if(state.river)renderRiver(); });
  $("putInTime").addEventListener("input", () => {syncUrl();if(state.river)renderSections(state.river,state.gauge,renderDaylight(state.river));});
  $("fishingToggle").addEventListener("change", () => {state.fishing=$("fishingToggle").checked;syncUrl();if(state.river)renderSections(state.river,state.gauge,renderDaylight(state.river));});
  $("filterReports").addEventListener("change", renderReports);
  $("reportForm").addEventListener("submit", submitReport);
  $("reportsList").addEventListener("click", ev=>{if(ev.target.closest("[data-retry-reports]")){loadReports();return;} const btn=ev.target.closest(".vote-btn");if(btn&&!btn.disabled)vote(btn.dataset.id,btn.dataset.action);});
  $("sectionCards").addEventListener("click", event => {
    const button = event.target.closest("[data-map-section]");
    if (!button || !state.river) return;
    const section = state.river.sections.find(sec => sec.id === button.dataset.mapSection);
    if (section) showLandMap(section);
  });
  $("landMapClose").addEventListener("click", closeLandMap);
  loadReports();
  setInterval(()=>{if(!document.hidden && state.river) {renderDaylight(state.river);renderSections(state.river,state.gauge,sunsetToday(state.river.lat,state.river.lon));}},60000);
  setInterval(()=>{if(!document.hidden && state.river){renderRiver();loadReports();}},300000);
  document.addEventListener("visibilitychange",()=>{if(!document.hidden && state.river){renderRiver();loadReports();}});
}
init();
