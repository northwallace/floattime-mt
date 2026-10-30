/* Pure planning functions shared by the browser and regression tests. */
(function (root) {
  "use strict";
  const minute = 60000;
  function localParts(date, zone) {
    return Object.fromEntries(
      new Intl.DateTimeFormat("en-CA", {
        timeZone: zone,
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23",
      })
        .formatToParts(date)
        .filter((p) => p.type !== "literal")
        .map((p) => [p.type, p.value]),
    );
  }
  function dateKey(date, zone) {
    const p = localParts(date, zone);
    return `${p.year}-${p.month}-${p.day}`;
  }
  function clock(date, zone) {
    return new Intl.DateTimeFormat("en-US", {
      timeZone: zone,
      hour: "numeric",
      minute: "2-digit",
      timeZoneName: "short",
    }).format(date);
  }
  function launch(value, zone, now = new Date()) {
    if (!value) return now;
    if (!/^\d{2}:\d{2}$/.test(value)) return null;
    const [h, m] = value.split(":").map(Number);
    if (h > 23 || m > 59) return null;
    const p = localParts(now, zone),
      target = Date.UTC(+p.year, +p.month - 1, +p.day, h, m);
    let result = target;
    for (let i = 0; i < 3; i++) {
      const t = localParts(new Date(result), zone);
      result +=
        target - Date.UTC(+t.year, +t.month - 1, +t.day, +t.hour, +t.minute);
    }
    const d = new Date(result),
      t = localParts(d, zone);
    return +t.hour === h &&
      +t.minute === m &&
      dateKey(d, zone) === dateKey(now, zone)
      ? d
      : null;
  }
  function duration(totalMinutes) {
    const n = Math.max(0, Math.round(totalMinutes));
    return n < 60
      ? `${n} min`
      : `${Math.floor(n / 60)} hr${n % 60 ? " " + (n % 60) + " min" : ""}`;
  }
  function sunset(lat, lon, zone, now = new Date()) {
    const p = localParts(now, zone),
      midnight = Date.UTC(+p.year, +p.month - 1, +p.day);
    const day = Math.floor((midnight - Date.UTC(+p.year, 0, 0)) / 86400000),
      rad = Math.PI / 180,
      lng = lon / 15,
      t = day + (18 - lng) / 24;
    const M = 0.9856 * t - 3.289;
    let L =
      (M +
        1.916 * Math.sin(M * rad) +
        0.02 * Math.sin(2 * M * rad) +
        282.634 +
        360) %
      360;
    let RA = (Math.atan(0.91764 * Math.tan(L * rad)) / rad + 360) % 360;
    RA = (RA + Math.floor(L / 90) * 90 - Math.floor(RA / 90) * 90) / 15;
    const sin = 0.39782 * Math.sin(L * rad),
      cos = Math.cos(Math.asin(sin)),
      cosH =
        (Math.cos(90.833 * rad) - sin * Math.sin(lat * rad)) /
        (cos * Math.cos(lat * rad));
    if (cosH > 1 || cosH < -1) return null;
    const UT =
      (((Math.acos(cosH) / rad / 15 + RA - 0.06571 * t - 6.622 - lng) % 24) +
        24) %
      24;
    const candidate = midnight + Math.round(UT * 3600) * 1000;
    for (const offset of [-1, 0, 1]) {
      const d = new Date(candidate + offset * 86400000);
      if (dateKey(d, zone) === dateKey(now, zone)) return d;
    }
    return null;
  }
  function estimate(river, section, flow, mult, stops) {
    if (
      !supportsLiveTiming(river) ||
      section.accessReview || section.distanceReview || river.timing?.mode === "unavailable" ||
      !Number.isFinite(river.refFlowCfs) || river.refFlowCfs <= 0 ||
      !Number.isFinite(river.refSpeedMph) || river.refSpeedMph <= 0 ||
      !Number.isFinite(flow) ||
      flow <= 0 ||
      !Number.isFinite(stops) ||
      stops < 0 ||
      !Number.isFinite(mult) ||
      mult <= 0
    )
      return null;
    const speed =
      Math.min(
        9,
        Math.max(
          0.8,
          river.refSpeedMph * Math.pow(flow / river.refFlowCfs, 0.34),
        ),
      ) * mult;
    const rawMinutes = (section.miles / speed) * 60 + stops;
    return {
      speed,
      rawMinutes,
      minutes: Math.max(5, Math.round(rawMinutes / 5) * 5),
      multiDay: !!river.multiDay || !!section.multiDay || rawMinutes > 600,
      days: Math.ceil(rawMinutes / 420),
    };
  }
  function fresh(reading, now = Date.now()) {
    return (
      !!reading &&
      Number.isFinite(reading.flow) &&
      reading.flow > 0 &&
      Number.isFinite(reading.at) &&
      now - reading.at >= -5 * minute &&
      now - reading.at <= 120 * minute
    );
  }
  function gaugeRelationship(river) {
    return river.gaugeRelationship || (river.gauge || river.flowSource ? "representative" : "none");
  }
  function supportsLiveTiming(river) {
    return gaugeRelationship(river) === "representative" && river.timing?.mode !== "unavailable";
  }
  const api = {
    localParts,
    dateKey,
    clock,
    launch,
    duration,
    sunset,
    estimate,
    fresh,
    gaugeRelationship,
    supportsLiveTiming,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.FloatPlanner = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
