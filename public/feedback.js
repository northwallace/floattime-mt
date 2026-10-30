(function () {
  "use strict";
  const $ = id => document.getElementById(id);
  const params = new URLSearchParams(location.search);
  let rivers = [];
  const clientToken = crypto.randomUUID();
  const status = $("feedbackStatus");
  $("year").textContent = new Date().getFullYear();
  if (["correction", "access-suggestion"].includes(params.get("type"))) $("feedbackType").value = params.get("type");

  function selectedRiver() { return rivers.find(r => r.id === $("feedbackRiver").value); }
  function fillSections(sectionId = "") {
    const select = $("feedbackSection");
    select.replaceChildren(new Option("Whole river / general correction", ""));
    const river = selectedRiver();
    for (const s of river?.sections || []) select.add(new Option(`${s.putIn} → ${s.takeOut}`, s.id));
    if (river?.sections.some(s => s.id === sectionId)) select.value = sectionId;
    showContext();
  }
  function showContext() {
    const river = selectedRiver();
    const section = river?.sections.find(s => s.id === $("feedbackSection").value);
    $("feedbackContext").textContent = river ? `${river.name}${section ? ` · ${section.putIn} → ${section.takeOut}` : " · Whole river"}` : "";
    $("feedbackBack").href = river ? `/?river=${encodeURIComponent(river.id)}#calculator` : "/";
  }
  function updateMode() {
    const correction = $("feedbackType").value !== "float-request";
    const access = $("feedbackType").value === "access-suggestion";
    $("locationLat").required = $("locationLon").required = access;
    if (access) $("feedbackCategory").value = "map-location";
    $("correctionFields").hidden = $("correctionFields").disabled = !correction;
    $("requestFields").hidden = $("requestFields").disabled = correction;
    $("feedbackMessageLabel").textContent = access ? "Tell us about this access and any restrictions" : correction ? "What is wrong, and what should it say?" : "What should we know about this float?";
    $("feedbackMessage").placeholder = correction ? "Describe the issue and your suggested correction. A location, trip date or source can help." : "Typical duration, your craft, trip date or flow if known, and useful access details…";
    $("feedbackSubmit").textContent = access ? "Suggest this access" : correction ? "Send correction" : "Request this float";
    status.textContent = "";
    const url = new URL(location.href);
    url.searchParams.set("type", $("feedbackType").value);
    history.replaceState(null, "", url.pathname + url.search);
  }
  updateMode();
  $("feedbackType").addEventListener("change", updateMode);
  $("feedbackRiver").addEventListener("change", () => {
    fillSections();
    $("locationLat").value = $("locationLon").value = $("locationLink").value = "";
    $("locationStatus").textContent = "";
    if (locationMap) { locationMap.remove(); locationMap = null; proposedMarker = null; $("locationMap").hidden = true; }
  });
  $("feedbackSection").addEventListener("change", showContext);

  fetch("/catalog-index.json", {signal: AbortSignal.timeout(15000)})
    .then(response => { if (!response.ok) throw new Error(); return response.json(); })
    .then(catalog => {
      rivers = catalog.rivers;
      for (const state of catalog.states) {
        const group = document.createElement("optgroup"); group.label = state.name;
        for (const r of rivers.filter(r => r.state === state.id)) group.appendChild(new Option(r.name, r.id));
        $("feedbackRiver").appendChild(group);
        $("feedbackStates").appendChild(new Option(state.name, state.name));
      }
      const byId = rivers.find(r => r.id === params.get("riverId"));
      const byName = rivers.filter(r => r.name === params.get("river"));
      const river = byId || (byName.length === 1 ? byName[0] : null);
      if (river) $("feedbackRiver").value = river.id;
      fillSections(params.get("sectionId") || "");
      if (params.get("state")) $("requestState").value = params.get("state").slice(0, 80);
    })
    .catch(() => {
      status.className = "report-status err";
      status.textContent = "River choices could not load. Refresh to suggest a correction; you can still request a missing float.";
    });

  let locationMap = null, proposedMarker = null, locationMethod = "manual";
  function locationValue(point, method) {
    $("locationLat").value = point.lat.toFixed(6); $("locationLon").value = point.lon.toFixed(6); locationMethod = method;
    $("locationStatus").textContent = `Proposed ${$("locationType").selectedOptions[0].text}: ${point.lat.toFixed(6)}, ${point.lon.toFixed(6)}. Review before sending.`;
    if (locationMap) {
      if (!proposedMarker) {
        proposedMarker = new maplibregl.Marker({color:"#a25f25",draggable:true}).setLngLat([point.lon,point.lat]).addTo(locationMap);
        proposedMarker.on("dragend", () => {const p=proposedMarker.getLngLat();locationValue({lat:p.lat,lon:p.lng},"map");});
      } else proposedMarker.setLngLat([point.lon,point.lat]);
    }
  }
  $("locationParse").addEventListener("click",()=>{try {const p=AccessLocation.parse($("locationLink").value);locationValue(p,"manual");locationMap?.flyTo({center:[p.lon,p.lat],zoom:16});}catch(e){$("locationStatus").textContent=e.message;}});
  for (const id of ["locationLat","locationLon"]) $(id).addEventListener("change",()=>{if ($("locationLat").value && $("locationLon").value && AccessLocation.valid(+$("locationLat").value,+$("locationLon").value)) locationValue({lat:+$("locationLat").value,lon:+$("locationLon").value},"manual");});
  $("locationGPS").addEventListener("click",()=>{
    if (!navigator.geolocation) {$("locationStatus").textContent="Location is unavailable in this browser. Paste coordinates or choose a pin instead.";return;}
    navigator.geolocation.getCurrentPosition(fix=>{const p={lat:fix.coords.latitude,lon:fix.coords.longitude};locationValue(p,"gps");locationMap?.flyTo({center:[p.lon,p.lat],zoom:16});},()=>{$("locationStatus").textContent="Location could not be obtained. You can choose a pin or paste coordinates.";},{enableHighAccuracy:true,timeout:15000,maximumAge:0});
  });
  $("locationOpen").addEventListener("click",async()=>{
    try {
      if (locationMap) {locationMap.resize();return;}
      $("locationStatus").textContent="Loading satellite map…";
      const [lib,response]=await Promise.all([loadMapLibrary(),fetch("/api/map-config")]);
      if (!response.ok) throw Error("Satellite map is unavailable. You can still enter coordinates.");
      const config=await response.json(), river=selectedRiver();
      const hasPoint=$("locationLat").value && $("locationLon").value;
      const point=hasPoint?{lat:+$("locationLat").value,lon:+$("locationLon").value}:{lat:river?.lat||39,lon:river?.lon||-110};
      $("locationMap").hidden=false;
      locationMap=new lib.Map({container:"locationMap",style:satelliteMapStyle(config.arcgisApiKey),center:[point.lon,point.lat],zoom:hasPoint?16:river?10:4});
      locationMap.addControl(new lib.NavigationControl({showCompass:false}));
      locationMap.on("click",e=>locationValue({lat:e.lngLat.lat,lon:e.lngLat.lng},"map"));
      locationMap.on("error",()=>{$("locationStatus").textContent="Some imagery could not load. You can still paste coordinates.";});
      if (hasPoint) locationValue(point,locationMethod);
      $("locationStatus").textContent="Tap the actual landing, parking area, or entrance to propose a pin. You can drag it to adjust.";
    } catch(e) {$("locationStatus").textContent=e.message;}
  });

  $("feedbackForm").addEventListener("submit", async event => {
    event.preventDefault();
    const button = $("feedbackSubmit");
    if (button.disabled) return;
    const correction = $("feedbackType").value !== "float-request";
    const body = {
      type: $("feedbackType").value,
      message: $("feedbackMessage").value,
      sourceUrl: $("feedbackSource").value,
      name: $("feedbackName").value,
      email: $("feedbackEmail").value,
      website: $("feedbackWebsite").value,
      clientToken,

    };
    if (correction) Object.assign(body, {riverId: $("feedbackRiver").value, sectionId: $("feedbackSection").value, category: $("feedbackCategory").value});
    else Object.assign(body, {state: $("requestState").value, riverName: $("requestRiver").value, putIn: $("requestPutIn").value, takeOut: $("requestTakeOut").value});
    const lat = $("locationLat").value, lon = $("locationLon").value;
    if (lat !== "" || lon !== "") {
      if (!lat || !lon || !AccessLocation.valid(Number(lat),Number(lon))) { status.textContent = "Enter both valid latitude and longitude."; return; }
      body.location = {lat:Number(lat),lon:Number(lon),endpoint:$("locationEndpoint").value,pinType:$("locationType").value,method:locationMethod,observedOn:$("locationDate").value,firsthand:$("locationFirsthand").checked};
    }
    button.disabled = true;
    status.className = "report-status";
    status.textContent = "Sending…";
    try {
      const response = await fetch("/api/feedback", {method:"POST", headers:{"Content-Type":"application/json"}, signal:AbortSignal.timeout(15000), body:JSON.stringify(body)});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Please try again.");
      $("feedbackForm").hidden = true;
      $("feedbackThanks").hidden = false;
      $("feedbackConfirmation").textContent = `${$("feedbackType").value === "access-suggestion" ? "Your access suggestion" : correction ? "Your correction" : "Your float request"} has been received.${data.id ? ` Reference: ${data.id}.` : ""}`;
      if (!correction) $("feedbackBack").href = "/directory.html";
      $("feedbackThanks").setAttribute("tabindex", "-1");
      $("feedbackThanks").focus();
    } catch (error) {
      status.className = "report-status err";
      status.textContent = `Couldn't send: ${error.message} Your details are still here.`;
    } finally { button.disabled = false; }
  });
})();
