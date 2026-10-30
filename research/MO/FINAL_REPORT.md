# Missouri v1 — final report (2026-10-30)

**88/141 catalog sections exact, 53 approximate, 0 pending; 6/23 rivers audited verified; 88/141 ready for visitors; 5 draft-only rivers.**

## What was done
- MDC's Discover Nature boat-ramp layer and conservation-area layer were matched to rivers with USGS NHD HR and NLDI; NPS Ozark NSR POIs and USFS Mark Twain NF recreation sites added for the Current, Jacks Fork and Eleven Point.
- Every point got an NHD HR distance check (local HU4 GeoPackages) and an Esri imagery tile; verdicts are in `research/raw/imagery-review-MO.json`.
- Sections were built per river in downstream order (NLDI chainage), merging points under 1 mile apart; miles use NPS brochure river miles, then USFS descriptions, then NLDI distance.
- Restrictions (18), each with a fetched source: MO-RES-001 container-law; MO-RES-002 litter; MO-RES-003 life-jacket; MO-RES-004 access-law; MO-RES-005 flood-closure; MO-RES-006 motor-limits; MO-RES-007 vessel-rules; MO-RES-008 access-use; MO-RES-009 access-change; MO-RES-010 low-water; MO-RES-011 concessions; MO-RES-012 forest-order; MO-RES-013 low-water; MO-RES-014 area-rules; MO-RES-015 dam-operations; MO-RES-016 navigation-hazard; MO-RES-017 military-land; MO-RES-018 state-park.
- Timing: 24 agency float-time rows (16 matched to sections).

## Counts
- Registry endpoints: 154 (121 verified, 33 access-verified, 0 pending).
- All researched points: 212 (132 / 34 / 46).
- Sections: 141 catalog (88 exact, 53 approximate, 0 pending); 88 ready for visitors.
- Rivers: 23 in the catalog (6 fully ready, 14 partly ready, 3 in catalog but not ready); draft-only: 5 (courtois-creek, fourche-creek, mississippi-river-mo, sac-river, spring-river).
- Gauges: 21 catalog rivers with current USGS discharge; without: osage-fork, elk-river.
- Sources: 259 (15 failed fetches, none relied on).

## Blockers and review queue (76 items)
- **MO-RQ-001** [medium] no-coordinate — Welch Landing (Ozark NSR): NPS lists this landing (RM 92) but no NPS feature with a usable coordinate exists. → Wait for an NPS GIS feature; do not use OSM/AW coordinates.
- **MO-RQ-002** [medium] no-coordinate — Paint Rock (Ozark NSR): NPS lists this landing (RM 33) but no NPS feature with a usable coordinate exists. → Wait for an NPS GIS feature; do not use OSM/AW coordinates.
- **MO-RQ-003** [medium] no-coordinate — Beal Landing (Ozark NSR): NPS lists this landing (RM 37) but no NPS feature with a usable coordinate exists. → Wait for an NPS GIS feature; do not use OSM/AW coordinates.
- **MO-RQ-004** [medium] no-coordinate — Waymeyer (Ozark NSR): NPS lists this landing (RM 27) but no NPS feature with a usable coordinate exists. → Wait for an NPS GIS feature; do not use OSM/AW coordinates.
- **MO-RQ-005** [medium] no-coordinate — Raftyard (Ozark NSR): NPS lists this landing (RM 24) but no NPS feature with a usable coordinate exists. → Wait for an NPS GIS feature; do not use OSM/AW coordinates.
- **MO-RQ-006** [medium] no-coordinate — Chilton Creek (Ozark NSR): NPS lists this landing (RM 29) but no NPS feature with a usable coordinate exists. → Wait for an NPS GIS feature; do not use OSM/AW coordinates.
- **MO-RQ-007** [medium] no-coordinate — Buck Hollow (Ozark NSR): NPS lists this landing (RM 88) but no NPS feature with a usable coordinate exists. → Wait for an NPS GIS feature; do not use OSM/AW coordinates.
- **MO-RQ-008** [medium] no-coordinate — Bluff View (Ozark NSR): NPS lists this landing (RM 87) but no NPS feature with a usable coordinate exists. → Wait for an NPS GIS feature; do not use OSM/AW coordinates.
- **MO-RQ-009** [low] motorized-only — Chilton Creek (Ozark NSR): Compendium §3.8: Chilton Creek ramp is designated for motorized vessels only; no floater access. → Keep pending (not a floater access).
- **MO-RQ-010** [medium] identity — Unidentified NPS canoe access POI 14342: Unlabelled canoe/kayak POI (possibly Chilton Creek, motorized-only per compendium, or Waymeyer). Identity unconfirmed. → Confirm against an agency page before publishing.
- **MO-RQ-011** [medium] identity — Unidentified NPS canoe access POI 15210: Unlabelled canoe/kayak POI near Hwy 17 (probably Buck Hollow, RM 88). Identity unconfirmed. → Confirm against an agency page before publishing.
- **MO-RQ-012** [medium] identity — Unidentified NPS canoe access POI 15653: Unlabelled canoe/kayak POI between Log Yard and Van Buren (possibly Paint Rock, RM 33). Identity unconfirmed. → Confirm against an agency page before publishing.
- **MO-RQ-013** [medium] identity — Unidentified NPS canoe access POI 15840: Unlabelled canoe/kayak POI ~400 m from Blue Spring campground (possibly Bluff View, RM 87). Identity unconfirmed. → Confirm against an agency page before publishing.
- **MO-RQ-014** [medium] identity — Unidentified NPS canoe access POI 15997: Unlabelled canoe/kayak POI ~1.6 km from Log Yard (possibly Beal Landing, RM 37). Identity unconfirmed. → Confirm against an agency page before publishing.
- **MO-RQ-015** [medium] identity — Unidentified NPS canoe access POI 16322: Unlabelled canoe/kayak POI near Montauk (probably Tan Vat, the first NPS landing below Montauk State Park). Not in the brochure mileage list; identity unconfirmed. → Confirm against an agency page before publishing.
- **MO-RQ-016** [medium] identity — Unidentified NPS canoe access POI 16736: Unlabelled canoe/kayak POI ~2 km upstream of Akers (probably Welch Landing, brochure RM 92). Identity unconfirmed. → Confirm against an agency page before publishing.
- **MO-RQ-017** [medium] put-in/take-out approximate — Baptist (Ozark NSR): the NPS record is a parking lot near the landing, not the landing itself → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-018** [medium] put-in/take-out approximate — Round Spring (Ozark NSR): imagery verdict 'flag': Pin roughly 40-150 m from the water in woods, a campground or a parking area; launch spot not identifiable at the pin. Coordinate kept only as an area centre → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-019** [medium] put-in/take-out approximate — Jerktail Landing (Ozark NSR): imagery verdict 'flag': Pin roughly 40-150 m from the water in woods, a campground or a parking area; launch spot not identifiable at the pin. Coordinate kept only as an area centre → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-020** [medium] put-in/take-out approximate — Shawnee Creek (Ozark NSR): the NPS POI is not a canoe-access feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-021** [medium] put-in/take-out approximate — Powder Mill (Ozark NSR): the NPS record is a parking lot near the landing, not the landing itself → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-022** [medium] put-in/take-out approximate — Rocky Creek Conservation Area: imagery verdict 'flag': Pin roughly 40-150 m from the water in woods, a campground or a parking area; launch spot not identifiable at the pin. Coordinate kept only as an area centre → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-023** [medium] put-in/take-out approximate — Roberts Field (Ozark NSR): imagery verdict 'flag': Pin roughly 40-150 m from the water in woods, a campground or a parking area; launch spot not identifiable at the pin. Coordinate kept only as an area centre → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-024** [medium] put-in/take-out approximate — Log Yard (Ozark NSR): imagery verdict 'flag': Pin roughly 40-150 m from the water in woods, a campground or a parking area; launch spot not identifiable at the pin. Coordinate kept only as an area centre → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-025** [medium] put-in/take-out approximate — Big Spring (Ozark NSR): imagery verdict 'flag': Pin roughly 40-150 m from the water in woods, a campground or a parking area; launch spot not identifiable at the pin. Coordinate kept only as an area centre → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-026** [medium] put-in/take-out approximate — Gooseneck (Ozark NSR): imagery verdict 'flag': Pin roughly 40-150 m from the water in woods, a campground or a parking area; launch spot not identifiable at the pin. Coordinate kept only as an area centre → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-027** [medium] put-in/take-out approximate — Float Camp Recreation Area (USFS): the USFS record is a recreation-area point, not a boat-launch feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-028** [medium] put-in/take-out approximate — Greer Crossing (USFS): NHD HR named-river distance 157.0 m exceeds 150 m → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-029** [medium] put-in/take-out approximate — Highway 142 River Access (The Narrows, USFS): imagery verdict 'flag': Pin roughly 40-150 m from the water in woods, a campground or a parking area; launch spot not identifiable at the pin. Coordinate kept only as an area centre → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-030** [medium] put-in/take-out approximate — Short Bend Access: the MDC record is a conservation-area centroid, not a launch feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-031** [medium] put-in/take-out approximate — Red Bluff Recreation Area (USFS): the USFS record is a recreation-area point, not a boat-launch feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-032** [medium] put-in/take-out approximate — Baptist Camp Access: the MDC record is a conservation-area centroid, not a launch feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-033** [medium] put-in/take-out approximate — Slabtown Recreation Area (USFS): the USFS record is a recreation-area point, not a boat-launch feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-034** [medium] put-in/take-out approximate — East Gate Access (USFS): imagery verdict 'flag': Pin roughly 40-150 m from the water in woods, a campground or a parking area; launch spot not identifiable at the pin. Coordinate kept only as an area centre → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-035** [medium] put-in/take-out approximate — Crossroads Access (USFS): NHD HR named-river distance 209.2 m exceeds 150 m → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-036** [medium] put-in/take-out approximate — Lane Spring Recreation Area (USFS): the USFS record is a recreation-area point, not a boat-launch feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-037** [medium] put-in/take-out approximate — Rader Access: the MDC record is a conservation-area centroid, not a launch feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-038** [medium] put-in/take-out approximate — Williams Ford Access: the MDC record is a conservation-area centroid, not a launch feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-039** [medium] put-in/take-out approximate — Hebron Access: the MDC record is a conservation-area centroid, not a launch feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-040** [medium] put-in/take-out approximate — North Fork Recreation Area (USFS): imagery verdict 'flag': Pin roughly 40-150 m from the water in woods, a campground or a parking area; launch spot not identifiable at the pin. Coordinate kept only as an area centre → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-041** [medium] put-in/take-out approximate — Flo Cook Access: the MDC record is a conservation-area centroid, not a launch feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-042** [medium] put-in/take-out approximate — Hendrickson Boat Launch (USFS): NHD HR named-river distance 265.3 m exceeds 150 m → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-043** [medium] put-in/take-out approximate — Gruner Ford Access: the MDC record is a conservation-area centroid, not a launch feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-044** [medium] put-in/take-out approximate — Tea Access: the MDC record is a conservation-area centroid, not a launch feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-045** [medium] put-in/take-out approximate — Wenkel Ford Access: the MDC record is a conservation-area centroid, not a launch feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-046** [medium] put-in/take-out approximate — Reiker Ford Access: the MDC record is a conservation-area centroid, not a launch feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-047** [medium] put-in/take-out approximate — Bootleg Access: the MDC record is a conservation-area centroid, not a launch feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-048** [medium] put-in/take-out approximate — Leadwood Access: the MDC record is a conservation-area centroid, not a launch feature → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-049** [medium] put-in/take-out approximate — Delaware Town Access: imagery verdict 'flag': Pin roughly 40-150 m from the water in woods, a campground or a parking area; launch spot not identifiable at the pin. Coordinate kept only as an area centre → Find a launch-level agency coordinate; until then the app shows an approximate area.
- **MO-RQ-050** [low] timing-unmatched — Waymeyer → Van Buren: NPS Waymeyer (RM 27) has no agency coordinate → Attach the time once both endpoints exist.
- **MO-RQ-051** [low] timing-unmatched — Big Spring → Cataract: NPS 'Cataract' landing has no agency coordinate in this package → Attach the time once both endpoints exist.
- **MO-RQ-052** [low] timing-unmatched — Alley → Eminence: NPS 'Eminence' landing is not confirmed to be the MDC Joshua T. Chilton Memorial Landing in Eminence (identity unconfirmed; see review queue) → Attach the time once both endpoints exist.
- **MO-RQ-053** [low] timing-unmatched — Eminence → Two Rivers: NPS 'Eminence' landing is not confirmed to be the MDC Joshua T. Chilton Memorial Landing in Eminence (identity unconfirmed; see review queue) → Attach the time once both endpoints exist.
- **MO-RQ-054** [low] timing-unmatched — Hwy 17 → Alley: NPS 'Hwy 17' = Hwy 17 Bridge (Buck Hollow, RM 88), which has no agency coordinate → Attach the time once both endpoints exist.
- **MO-RQ-055** [low] timing-unmatched — Prongs → Hwy 17: NPS 'Prongs' (Jacks Fork headwaters) has no agency coordinate in this package; NPS 'Hwy 17' = Hwy 17 Bridge (Buck Hollow, RM 88), which has no agency coordinate → Attach the time once both endpoints exist.
- **MO-RQ-056** [low] timing-unmatched — Hwy 17 → Rymers: NPS 'Hwy 17' = Hwy 17 Bridge (Buck Hollow, RM 88), which has no agency coordinate → Attach the time once both endpoints exist.
- **MO-RQ-057** [low] timing-unmatched — Deer Leap Recreation Area (Tuber Launch) → Doniphan public boat launch (below the bridge): Deer Leap is not a point in this package (no separate agency coordinate selected); T. L. Wright Memorial Access is the Doniphan endpoint used here. → Attach the time once both endpoints exist.
- **MO-RQ-058** [low] source-unavailable — https://mdc.mo.gov/fishing/where-fish/float-streams: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **MO-RQ-059** [low] source-unavailable — https://mdc.mo.gov/discover-nature/activities/paddling/missouri-river-water-trail: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **MO-RQ-060** [low] source-unavailable — https://mdc.mo.gov/conservation/stash-your-trash: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **MO-RQ-061** [low] source-unavailable — https://www.missouririvertrail.org/: Fetch failed: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1029)> → Retry later; nothing in the catalog depends on it.
- **MO-RQ-062** [low] source-unavailable — https://missouririverwatertrail.org/safety/navigating-river-safely: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **MO-RQ-063** [low] source-unavailable — https://www.mshp.dps.missouri.gov/MSHPWeb/WaterPatrol/BoatingSafety/index.html: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **MO-RQ-064** [low] source-unavailable — https://www.nps.gov/ozar/planyourvisit/boating.htm: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **MO-RQ-065** [low] source-unavailable — https://www.nps.gov/ozar/planyourvisit/canoe-rental.htm: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **MO-RQ-066** [low] source-unavailable — https://www.nps.gov/ozar/getinvolved/commercial-use-authorizations.htm: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **MO-RQ-067** [low] source-unavailable — https://www.nps.gov/ozar/planyourvisit/river-levels.htm: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **MO-RQ-068** [low] source-unavailable — https://www.nps.gov/ozar/planyourvisit/current-river-levels.htm: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **MO-RQ-069** [low] source-unavailable — https://www.nps.gov/ozar/planyourvisit/rules-and-regulations.htm: Fetch failed: HTTP Error 404: Not Found → Retry later; nothing in the catalog depends on it.
- **MO-RQ-070** [low] source-unavailable — https://www.swl.usace.army.mil/Missions/Recreation/Lakes/Norfork-Lake/: Fetch failed: HTTP Error 403: Forbidden → Retry later; nothing in the catalog depends on it.
- **MO-RQ-071** [low] source-unavailable — https://www.nwk.usace.army.mil/Missions/Civil-Works/Navigation/: Fetch failed: HTTP Error 403: Forbidden → Retry later; nothing in the catalog depends on it.
- **MO-RQ-072** [low] source-unavailable — https://www.mvs.usace.army.mil/Missions/Recreation/Wappapello-Lake/: Fetch failed: HTTP Error 403: Forbidden → Retry later; nothing in the catalog depends on it.
- **MO-RQ-073** [high] timing — All catalog rivers: No flow-to-speed calibration; timing.mode is 'unavailable' everywhere. NPS/USFS guideTimes cover the Ozark NSR sections only. → North: decide whether guide ranges alone are enough for visitors.
- **MO-RQ-074** [medium] mileage-preliminary — NLDI-only mileages: 107 sections use NHDPlus V2 routed distance (no agency river miles). → Accept as preliminary or find agency mile tables.
- **MO-RQ-075** [medium] long-sections — Missouri River (MR340) and Osage long reaches: Several big-river sections are longer than 20 miles; barge traffic and wing dams are noted in restrictions. → North: decide whether to show these as day trips or split them.
- **MO-RQ-076** [low] archived-rules — 2020 ONSR rule releases (MO-RES-008/009): Rules from 2020 news releases are stored with currentOperational=false. → Confirm against the current Superintendent's Compendium before showing.

## Proposals
- **MO-RP-001** (alternate-endpoint) Van Buren (Ozark NSR): 'Van Buren Riverfront Park' is 0.82 mi from 'Van Buren (Ozark NSR)' and was merged as an alternate.
- **MO-RP-002** (alternate-endpoint) Turner Mill South River Access (USFS): 'Turner Mill North River Access (USFS)' is 0.06 mi from 'Turner Mill South River Access (USFS)' and was merged as an alternate.
- **MO-RP-003** (alternate-endpoint) Riverton East River Access (USFS): 'Riverton West River Access (USFS)' is 0.1 mi from 'Riverton East River Access (USFS)' and was merged as an alternate.
- **MO-RP-004** (upgrade-to-verified) Baptist (Ozark NSR): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-005** (upgrade-to-verified) Round Spring (Ozark NSR): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-006** (upgrade-to-verified) Jerktail Landing (Ozark NSR): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-007** (upgrade-to-verified) Shawnee Creek (Ozark NSR): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-008** (upgrade-to-verified) Powder Mill (Ozark NSR): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-009** (upgrade-to-verified) Rocky Creek Conservation Area: Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-010** (upgrade-to-verified) Roberts Field (Ozark NSR): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-011** (upgrade-to-verified) Log Yard (Ozark NSR): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-012** (upgrade-to-verified) Big Spring (Ozark NSR): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-013** (upgrade-to-verified) Gooseneck (Ozark NSR): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-014** (upgrade-to-verified) Float Camp Recreation Area (USFS): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-015** (upgrade-to-verified) Greer Crossing (USFS): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-016** (upgrade-to-verified) Highway 142 River Access (The Narrows, USFS): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-017** (upgrade-to-verified) Short Bend Access: Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-018** (upgrade-to-verified) Red Bluff Recreation Area (USFS): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-019** (upgrade-to-verified) Baptist Camp Access: Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-020** (upgrade-to-verified) Slabtown Recreation Area (USFS): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-021** (upgrade-to-verified) East Gate Access (USFS): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-022** (upgrade-to-verified) Crossroads Access (USFS): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-023** (upgrade-to-verified) Lane Spring Recreation Area (USFS): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-024** (upgrade-to-verified) Rader Access: Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-025** (upgrade-to-verified) Williams Ford Access: Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-026** (upgrade-to-verified) Hebron Access: Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-027** (upgrade-to-verified) North Fork Recreation Area (USFS): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-028** (upgrade-to-verified) Flo Cook Access: Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-029** (upgrade-to-verified) Hendrickson Boat Launch (USFS): Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-030** (upgrade-to-verified) Gruner Ford Access: Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-031** (upgrade-to-verified) Tea Access: Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-032** (upgrade-to-verified) Wenkel Ford Access: Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-033** (upgrade-to-verified) Reiker Ford Access: Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-034** (upgrade-to-verified) Bootleg Access: Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-035** (upgrade-to-verified) Leadwood Access: Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.
- **MO-RP-036** (upgrade-to-verified) Delaware Town Access: Find an agency launch-level coordinate (boat-ramp feature or NPS canoe access) to upgrade this approximate endpoint.

## Open questions for North
1. NPS float times on the Current/Jacks Fork are shown as guide ranges (min = max = NPS figure). Is that enough for visitors while live estimates stay off?
2. Missouri River (MR340) and some Osage sections are long (>20 mi). Show them as-is or split them?
3. NPS "Eminence" landing: is it the same as MDC's Joshua T. Chilton Memorial Landing? It's kept separate until confirmed, so the Alley → Eminence and Eminence → Two Rivers NPS times aren't attached.
4. Mississippi River and Fourche Creek stay as drafts. Should a later pass add the Mississippi, which has barges, wing dams and locks?
5. Should Arkansas be the next state so that the Eleven Point and Black River cross-state sections can be completed?

## Notes
- 15 fetches failed (404/403/SSL), for example NPS boating/river-levels pages, MSHP boating, USACE Wappapello/Norfork/NWK and the Missouri River Water Trail. Statutes and the ONSR compendium were used instead.
- The 2020 ONSR rule releases are stored with currentOperational=false.
- NHD HR GeoPackages are not bundled; URLs and zip sha256 are in research/sources.json.
- Validation: RESULT: PASS (0 failures).
