/* Explicit field-test route validation; ordinary reviewed routes are unchanged. */
(function(root) {
  'use strict';
  const G = typeof module === 'object' && module.exports ? require('./river-route.js') : root.FloatRoute;
  function matches(entry, id, river, section) {
    return !!id && entry?.id === id && entry.riverId === river.id && entry.sectionId === section.id;
  }
  function prepare(data, river, section) {
    const snapshot = data.catalogSnapshot;
    if (data.status !== 'field-pilot' || data.riverId !== river.id || data.sectionId !== section.id ||
        snapshot?.miles !== section.miles || section.accessReview || section.distanceReview) throw Error('Pilot no longer matches this section');
    for (const field of ['putIn', 'takeOut']) {
      const saved = snapshot[field], current = section[field + 'Coords'];
      if (!current || saved?.name !== section[field] || saved.lat !== current.lat || saved.lon !== current.lon) throw Error('Pilot access snapshot changed');
    }
    if (data.takeOut?.status !== 'user-confirmed' || !G.validPoint([data.takeOut.lon, data.takeOut.lat]) ||
        data.putIn?.status !== 'approximate-area' || !G.validPoint([data.putIn.lon, data.putIn.lat])) throw Error('Pilot endpoint evidence missing');
    // Geometry mileage is checked separately from the rounded agency guide mileage.
    // This never changes the normal section calculator or promotes an access pin.
    const route = G.prepare({status:'local-pilot', catalogMiles:data.routeMiles, geometry:data.geometry});
    if (Math.abs(route.length / 1609.344 - data.routeMiles) > .01 ||
        G.distance(route.coordinates[0], [data.putIn.lon, data.putIn.lat]) > 200 ||
        G.distance(route.coordinates.at(-1), [data.takeOut.lon, data.takeOut.lat]) > 75) throw Error('Pilot geometry changed');
    return route;
  }
  const api = {matches, prepare};
  if (typeof module === 'object' && module.exports) module.exports = api; else root.FloatFieldPilot = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
