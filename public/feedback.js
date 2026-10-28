(function () {
  "use strict";
  const $ = id => document.getElementById(id);
  const params = new URLSearchParams(location.search);
  let rivers = [];
  const clientToken = crypto.randomUUID();
  const status = $("feedbackStatus");
  $("year").textContent = new Date().getFullYear();
  if (params.get("type") === "correction") $("feedbackType").value = "correction";

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
    const correction = $("feedbackType").value === "correction";
    $("correctionFields").hidden = $("correctionFields").disabled = !correction;
    $("requestFields").hidden = $("requestFields").disabled = correction;
    $("feedbackMessageLabel").textContent = correction ? "What is wrong, and what should it say?" : "What should we know about this float?";
    $("feedbackMessage").placeholder = correction ? "Describe the issue and your suggested correction. A location, trip date or source can help." : "Typical duration, your craft, trip date or flow if known, and useful access details…";
    $("feedbackSubmit").textContent = correction ? "Send correction" : "Request this float";
    status.textContent = "";
    const url = new URL(location.href);
    url.searchParams.set("type", correction ? "correction" : "float-request");
    history.replaceState(null, "", url.pathname + url.search);
  }
  updateMode();
  $("feedbackType").addEventListener("change", updateMode);
  $("feedbackRiver").addEventListener("change", () => fillSections());
  $("feedbackSection").addEventListener("change", showContext);

  fetch("/catalog.json", {signal: AbortSignal.timeout(15000)})
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

  $("feedbackForm").addEventListener("submit", async event => {
    event.preventDefault();
    const button = $("feedbackSubmit");
    if (button.disabled) return;
    const correction = $("feedbackType").value === "correction";
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
    button.disabled = true;
    status.className = "report-status";
    status.textContent = "Sending…";
    try {
      const response = await fetch("/api/feedback", {method:"POST", headers:{"Content-Type":"application/json"}, signal:AbortSignal.timeout(15000), body:JSON.stringify(body)});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Please try again.");
      $("feedbackForm").hidden = true;
      $("feedbackThanks").hidden = false;
      $("feedbackConfirmation").textContent = `${correction ? "Your correction" : "Your float request"} has been received.${data.id ? ` Reference: ${data.id}.` : ""}`;
      if (!correction) $("feedbackBack").href = "/directory.html";
      $("feedbackThanks").setAttribute("tabindex", "-1");
      $("feedbackThanks").focus();
    } catch (error) {
      status.className = "report-status err";
      status.textContent = `Couldn't send: ${error.message} Your details are still here.`;
    } finally { button.disabled = false; }
  });
})();
