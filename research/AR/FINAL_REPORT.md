# Arkansas v1 — final report (2026-10-30)

**103/115 catalog sections exact, 12 approximate, 0 pending; 18/22 rivers audited verified; 100/115 ready for visitors; 11 draft-only rivers.**

## What was done
- AGFC's Public Use Facilities layer (boating and canoe/kayak accesses) was matched to rivers with USGS NHD HR and NLDI; NPS Buffalo National River POIs and USFS recreation sites (Ouachita NF float camps, Albert Pike, Long Pool, Bayou Bluff, Richland Creek) were added.
- Every point got an NHD HR distance check (local HU4 GeoPackages) and an Esri imagery tile; verdicts are in `research/raw/imagery-review-AR.json`.
- Buffalo sections follow NPS "Things To Do" trip pairs (NPS river miles + NPS durations); other rivers were built in downstream order (NLDI chainage), merging points under 1 mile apart; miles use NPS river miles, then AGFC water-trail tables (only where the access identity is clear), then NLDI distance.
- Restrictions (15), each with a fetched source: AR-RES-001 container-law; AR-RES-002 life-jacket; AR-RES-003 access-law; AR-RES-004 vessel-rules; AR-RES-005 container-rules; AR-RES-006 life-jacket; AR-RES-007 motor-limits; AR-RES-008 access-change; AR-RES-009 dam-operations; AR-RES-010 dam-operations; AR-RES-011 hazard; AR-RES-012 hazard; AR-RES-013 permit; AR-RES-014 seasonal; AR-RES-015 low-water.
- Timing: 24 agency float-time rows (21 matched to sections).

## Counts
- Registry endpoints: 136 (128 verified, 8 access-verified, 0 pending).
- All researched points: 165 (148 / 17 / 0).
- Sections: 115 catalog (103 exact, 12 approximate, 0 pending); 100 ready for visitors; 10 draft sections.
- Rivers: 22 in the catalog (16 fully ready, 4 partly ready, 2 in catalog but not ready); draft-only: 11 (big-piney-creek, cossatot-river, current-river-ar, fourche-lafave-river, illinois-bayou, little-maumelle-river, little-missouri-river-upper, richland-creek, saline-river-lower, st-francis-river-ar, war-eagle-creek).
- Gauges: 15 catalog rivers with current USGS discharge; without: white-river-beaver-tailwater, north-fork-river-ar, south-fork-spring-river, strawberry-river, little-missouri-river, crooked-creek, bayou-deview.
- Sources: 153 (9 failed fetches, none relied on).

## Catalog sections not ready for visitors
- `dalton-boat-ramp-to-eleven-point-boat-ramp`: put-in-approximate
- `high-bank-access-to-indian-creek-access`: take-out-approximate
- `indian-creek-access-to-redding-recreation-area-canoe-access`: put-in-approximate
- `cherry-hill-boat-ramp-to-shirley-creek`: take-out-approximate
- `shirley-creek-to-oden-boating-access`: put-in-approximate
- `oden-boating-access-to-rocky-shoals`: take-out-approximate
- `rocky-shoals-to-fulton-branch`: put-in-approximate, take-out-approximate
- `fulton-branch-to-dragover`: put-in-approximate
- `dragover-to-river-bluff`: take-out-approximate
- `hwy-285-boat-ramp-to-shaw-bridge-boat-ramp`: permission-unresolved
- `shaw-bridge-boat-ramp-to-hwy-64-boat-ramp`: permission-unresolved
- `siloam-springs-kayak-park-access-to-woka-whitewater-park-canoe-kayakng-access`: permission-unresolved
- `highway-17-boating-access-to-rock-island-rr-boating-access`: take-out-approximate
- `rock-island-rr-boating-access-to-apple-lake-boat-access`: put-in-approximate, take-out-approximate
- `apple-lake-boat-access-to-bank-of-brinkley-boating-access`: put-in-approximate

## Blockers and review queue (41 items)
- **AR-RQ-001** [medium] in-lake-polygon — Beaver Lake Dam Site Boat Ramp: Pin plots inside NHD waterbody ['Table Rock Lake']; imagery decides. → Confirm against a published agency page before publishing; do not contact agencies from this package.
- **AR-RQ-002** [high] access-change — Buffalo Point (Buffalo NR): NPS mileage page: 'The road down to the launch at Buffalo Point is closed. If you put in or take out at Buffalo Point you will need to carry your boat and gear up the large and steep gravel bar to the parking lot. You may want to consider taking out at Dillards Ferry, which is 1.5 miles upstream from Buffalo Point.' → Confirm against a published agency page before publishing; do not contact agencies from this package.
- **AR-RQ-003** [high] owner-unlisted — Hwy 64 Boat Ramp: AGFC facility record owner is 'Other' — AHTD Right of Way, Project needs sign designating area from HWY 64.; public-use status comes from the AGFC Public Use Facilities layer only. → Confirm against a published agency page before publishing; do not contact agencies from this package.
- **AR-RQ-004** [medium] nhd-name — Peeler Bend Boat Ramp: NHD HR names the channel at this ramp 'Alum Fork Saline River'; AGFC Saline River Water Trail lists Peeler Bend on the Saline River trail. → Confirm against a published agency page before publishing; do not contact agencies from this package.
- **AR-RQ-005** [high] owner-unlisted — Shaw Bridge Boat Ramp: AGFC facility record owner is 'Other' — AHTD Right of Way; public-use status comes from the AGFC Public Use Facilities layer only. → Confirm against a published agency page before publishing; do not contact agencies from this package.
- **AR-RQ-006** [high] owner-unlisted — WOKA Whitewater Park Canoe-Kayakng Access: AGFC facility record owner is 'Other - See Comments' — Ownership belongs to GRDA (Grand River Dam Authority); public-use status comes from the AGFC Public Use Facilities layer only. → Confirm against a published agency page before publishing; do not contact agencies from this package.
- **AR-RQ-007** [low] off-reach — Brookings Boat Ramp: Off the routed reach (NLDI distance 2060.8 m): 2.1 km from the routed NHDPlus V2 Black River line (likely an old channel/slough); research-only. → Keep research-only unless an agency page confirms it is on the floated channel.
- **AR-RQ-008** [low] off-reach — Dripping Springs Boat Ramp: Off the routed reach (NLDI distance 1110.7 m): 1.1 km from the routed NHDPlus V2 Little Red River line; research-only. → Keep research-only unless an agency page confirms it is on the floated channel.
- **AR-RQ-009** [low] off-reach — Pinnacle Mountain State Park - Little Maumelle Boat Ramp: Off the routed reach (NLDI distance 1693.2 m): routes to the Maumelle River, not the Little Maumelle; research-only. → Keep research-only unless an agency page confirms it is on the floated channel.
- **AR-RQ-010** [low] off-reach — Dark Corner Spur Boating Access: Off the routed reach (NLDI distance 489.0 m): off the main Bayou DeView channel (spur); AGFC lists Dark Corner as a water-trail access; research-only. → Keep research-only unless an agency page confirms it is on the floated channel.
- **AR-RQ-011** [low] off-reach — Hickson Lake Boat Ramp: Off the routed reach (NLDI distance 1843.1 m): on Hickson Lake (oxbow) off the routed Bayou DeView line; AGFC lists it as a water-trail access; research-only. → Keep research-only unless an agency page confirms it is on the floated channel.
- **AR-RQ-012** [medium] put-in/take-out approximate — Dalton Boat Ramp: imagery verdict 'flag': Pin among buildings roughly 80 m from the river; ramp not identifiable at the pin → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **AR-RQ-013** [medium] put-in/take-out approximate — Indian Creek Access: imagery verdict 'flag': Pin at a parking loop roughly 60-70 m from the river → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **AR-RQ-014** [medium] put-in/take-out approximate — Shirley Creek (USFS): imagery verdict 'flag': Pin in woods roughly 100 m from the river → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **AR-RQ-015** [medium] put-in/take-out approximate — Rocky Shoals (USFS): the USFS record is a recreation-area / day-use point whose description does not document a boat or canoe launch → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **AR-RQ-016** [medium] put-in/take-out approximate — Fulton Branch (USFS): the USFS record is a recreation-area / day-use point whose description does not document a boat or canoe launch → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **AR-RQ-017** [medium] put-in/take-out approximate — River Bluff (USFS): the USFS record is a recreation-area / day-use point whose description does not document a boat or canoe launch → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **AR-RQ-018** [medium] put-in/take-out approximate — Rock Island RR Boating Access: imagery verdict 'flag': Pin on a linear clearing in forest roughly 100 m from the mapped channel; launch not identifiable → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **AR-RQ-019** [medium] put-in/take-out approximate — Apple Lake Boat Access: NHD HR named-river distance 272.4 m exceeds 150 m → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **AR-RQ-020** [low] timing-unmatched — Rush (Buffalo NR) → Shipp's Ferry Boat Ramp: duration is in days (multi-day); kept in the section note, not as hourly guideTimes → Attach the time once both endpoints exist.
- **AR-RQ-021** [low] timing-unmatched — Tony Kelly → Lyle Park: Tony Kelly Ford is not a point in this package (no AGFC facility record selected). → Attach the time once both endpoints exist.
- **AR-RQ-022** [low] timing-unmatched — Lyle Park → Saline Crossing: Saline Crossing / Cherry Demuth are not confirmed to be the AGFC 'I -30 Cherry Gingles Boat Ramp' record (identity open; see review queue). → Attach the time once both endpoints exist.
- **AR-RQ-023** [low] timing-unmatched — Moore Ford → Peeler Bend: Moore Ford is not a point in this package. → Attach the time once both endpoints exist.
- **AR-RQ-024** [low] source-unavailable — https://www.agfc.com/education/arkansas-water-trails/: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **AR-RQ-025** [low] source-unavailable — https://www.agfc.com/en/explore-outdoors/canoeing-and-kayaking/water-trails/: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **AR-RQ-026** [low] source-unavailable — https://law.justia.com/cases/arkansas/supreme-court/1980/79-320-0.html: Fetch failed: HTTP Error 403: Forbidden → Retry later; nothing in the catalog depends on it.
- **AR-RQ-027** [low] source-unavailable — https://www.nps.gov/buff/planyourvisit/brochures.htm: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **AR-RQ-028** [low] source-unavailable — https://www.nps.gov/buff/planyourvisit/floating.htm: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **AR-RQ-029** [low] source-unavailable — https://www.nps.gov/buff/planyourvisit/canoeing-outfitters.htm: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **AR-RQ-030** [low] source-unavailable — https://www.nps.gov/buff/planyourvisit/preventive-search-and-rescue.htm: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **AR-RQ-031** [low] source-unavailable — https://www.nps.gov/buff/planyourvisit/river-levels.htm: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **AR-RQ-032** [low] source-unavailable — https://www.nps.gov/buff/planyourvisit/rules-and-regulations.htm: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **AR-RQ-033** [high] timing — All catalog rivers: No flow-to-speed calibration; timing.mode is 'unavailable' everywhere. NPS guideTimes cover Buffalo sections and AGFC covers Peeler Bend → Lyle Park. AGFC 'about 2 mph' (Crooked, Saline) and '1-2 mph' (Bayou DeView) rules of thumb were NOT applied. → North: decide whether guide ranges alone are enough for visitors, and whether agency mph statements may ever be used.
- **AR-RQ-034** [medium] mileage-preliminary — NLDI-only mileages: 96 sections use NHDPlus V2 routed distance (no agency river miles). → Accept as preliminary or find agency mile tables.
- **AR-RQ-035** [medium] long-sections — Long reaches (> 20 mi): 9 catalog sections are longer than 20 river miles (rivers: Black River — Arkansas line to Black Rock, Buffalo National River — Boxley to Buffalo City, Kings River, Little Missouri River — below Narrows Dam, Saline River — Benton to Jenkins Ferry, Strawberry River). Rush → Shipp's Ferry (30.2 mi) is an NPS multi-day trip. → North: decide whether to show these as day trips or split them.
- **AR-RQ-036** [medium] identity — Crooked Creek Pyatt accesses: AGFC water trail names 'Lower Pyatt' (US 62 bridge) and 'Upper Pyatt' (~1 mi upstream, US 62 Spur); the AGFC facility layer has 'Pyatt #1' and 'Pyatt #2'. Which is which is not stated, so the AGFC 6.7-mile Lower Pyatt→Snow figure was not applied. → Match from a published AGFC map.
- **AR-RQ-037** [medium] identity — Bayou DeView Highway 17 / Benson Creek: AGFC water trail starts at 'Benson Creek'; the AGFC layer point is 'Highway 17 Boating Access'. Identity not confirmed, so the AGFC Benson Creek mileages were not applied. → Match from a published AGFC map.
- **AR-RQ-038** [medium] identity — Saline Crossing / Cherry Demuth vs 'I -30 Cherry Gingles Boat Ramp': AGFC water trail lists Cherry Demuth (temporarily closed at low water) and Saline Crossing; the facility layer has 'I -30 Cherry Gingles Boat Ramp'. Identity not confirmed, so AGFC Lyle Park→Saline Crossing (4.2 mi / 2-3 h) was not attached. → Match from a published AGFC map.
- **AR-RQ-039** [low] source-unavailable — Buffalo NR floating / river-levels / PSAR pages: Several NPS Buffalo pages returned errors; the NPS conditions page carries no alert text in its static HTML, so current road/low-water closures (e.g. Kyles Landing road, Woolum low-water crossing) are not captured. → Check https://www.nps.gov/buff/planyourvisit/conditions.htm before each season.
- **AR-RQ-040** [low] gauge-missing — Rivers without a live gauge: Assigned gauge has no current USGS discharge for: white-river-beaver-tailwater, north-fork-river-ar, south-fork-spring-river, strawberry-river, little-missouri-river, crooked-creek, bayou-deview. Live estimates are hidden only; the station id is kept because the app requires one. → Optional: find a suitable USGS gauge.
- **AR-RQ-041** [low] cross-state — MO → AR sections: Myrtle → Dalton, Coon Island → Kody Riggan Datto, T. L. Wright → Johnston's Eddy are PROPOSED only (see research/cross-state-references.json). → Coder: decide whether to support cross-state endpoints.

## Proposals
- **AR-RP-001** (alternate-endpoint) Jim Griffin Boat Ramp: 'Forrest & Nina Wood Rivercliff Boat Ramp' is 0.19 mi from 'Jim Griffin Boat Ramp' and was merged as an alternate.
- **AR-RP-002** (alternate-endpoint) Bull Shoals Boat Ramp: 'Jim Griffin Boat Ramp' is 0.91 mi from 'Bull Shoals Boat Ramp' and was merged as an alternate.
- **AR-RP-003** (alternate-endpoint) Calvin Road Boat Ramp: 'Amity Landing Boat Ramp' is 0.68 mi from 'Calvin Road Boat Ramp' and was merged as an alternate.
- **AR-RP-004** (alternate-endpoint) Pyatt #2 Boat Ramp: 'Pyatt #1 Crooked Creek Boat Ramp' is 0.67 mi from 'Pyatt #2 Boat Ramp' and was merged as an alternate.
- **AR-RP-005** (upgrade-to-verified) Dalton Boat Ramp: Find an agency launch-level coordinate (AGFC boating-access feature, NPS river access or USFS launch) to upgrade this approximate endpoint.
- **AR-RP-006** (upgrade-to-verified) Indian Creek Access: Find an agency launch-level coordinate (AGFC boating-access feature, NPS river access or USFS launch) to upgrade this approximate endpoint.
- **AR-RP-007** (upgrade-to-verified) Shirley Creek (USFS): Find an agency launch-level coordinate (AGFC boating-access feature, NPS river access or USFS launch) to upgrade this approximate endpoint.
- **AR-RP-008** (upgrade-to-verified) Rocky Shoals (USFS): Find an agency launch-level coordinate (AGFC boating-access feature, NPS river access or USFS launch) to upgrade this approximate endpoint.
- **AR-RP-009** (upgrade-to-verified) Fulton Branch (USFS): Find an agency launch-level coordinate (AGFC boating-access feature, NPS river access or USFS launch) to upgrade this approximate endpoint.
- **AR-RP-010** (upgrade-to-verified) River Bluff (USFS): Find an agency launch-level coordinate (AGFC boating-access feature, NPS river access or USFS launch) to upgrade this approximate endpoint.
- **AR-RP-011** (upgrade-to-verified) Rock Island RR Boating Access: Find an agency launch-level coordinate (AGFC boating-access feature, NPS river access or USFS launch) to upgrade this approximate endpoint.
- **AR-RP-012** (upgrade-to-verified) Apple Lake Boat Access: Find an agency launch-level coordinate (AGFC boating-access feature, NPS river access or USFS launch) to upgrade this approximate endpoint.

## Open questions for North
1. Timing: only NPS Buffalo durations and one AGFC Saline range are shown, as guide ranges. AGFC says "about 2 miles per hour" (Crooked Creek, Saline) and "1-2 miles per hour" (Bayou DeView), but those were not turned into times. Should agency mph statements ever be used, or are guide ranges enough for visitors?
2. Buffalo Point: the NPS mileage page says the Buffalo Point road is closed. The Dillard's Ferry → Buffalo Point section carries that note but is still in the catalog. Keep it, or hide it until the road reopens?
3. Saline: is AGFC's "Saline Crossing" / "Cherry Demuth" (temporarily closed at low water) the same as the AGFC layer's "I -30 Cherry Gingles Boat Ramp"? This decides whether the Lyle Park → Saline Crossing 4.2 mi / 2-3 h figure can be attached.
4. Crooked Creek: which of AGFC "Pyatt #1" / "Pyatt #2" is "Lower Pyatt" vs "Upper Pyatt"? Bayou DeView: is "Highway 17 Boating Access" the water trail's "Benson Creek"?
5. Buffalo: Kyles Landing's road and the Woolum low-water crossing close seasonally (NPS conditions page not captured). Should the app link the NPS conditions page on every Buffalo section?
6. The Buffalo ends at Shipp's Ferry on the White River (NPS text) instead of Buffalo City. Is that right for the app?
7. Cadron Creek (Shaw Bridge, Hwy 64) and WOKA (GRDA, on the Oklahoma line): the AGFC record does not list a public owner, so 3 sections are marked permission-unresolved. Keep them in the catalog as not ready, or move them to drafts?
8. Long sections (>20 mi; see review queue). Show them as they are, or split them?
9. Cossatot River (no agency access coordinates), Fourche LaFave and the lower Saline are drafts. Should a later pass add them?
10. Should the app support cross-state sections (Myrtle → Dalton, Coon Island → Kody Riggan Datto, T. L. Wright → Johnston's Eddy)?

## Notes
- Off the routed line or off the channel and kept out of sections: Brookings (Black), Dripping Springs (Little Red), Dark Corner Spur and Hickson Lake (Bayou DeView), and the Pinnacle Mountain SP Little Maumelle ramp. The Beaver Dam Site pin falls inside the NHD Table Rock Lake polygon (see review queue).
- 9 fetches failed (404/403), including the NPS Buffalo floating, river-levels, outfitters and PSAR pages, the AGFC water-trails index pages, and the Justia copy of McIlroy (OpenJurist was used instead).
- NHD HR GeoPackages are not bundled. Their URLs and zip sha256 are in research/sources.json.
- Validation: RESULT: PASS (0 failures).
