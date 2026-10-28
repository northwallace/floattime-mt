# Float ETA - Utah package v1: final report (2026-10-25)

Built on the box only from public data. No agency was contacted, no permit or form was submitted, nothing was purchased, and no repo or live site was touched. "Verified" applies only to the fact stated.

## Counts

- Rivers in catalog: **10** (audits verified **5/10**), sections **16**.
- Registry points: **25**, of which **16 verified** and 9 pending (pending carry only status+note).
- Research access grades: 16 verified, 7 access-verified (approximate area), 2 pending.
- Candidate inventory: 27 access points with stable ids UT-ACC-0001..0027 (includes 2 points kept out of the registry: Rainbow Park (closed) and North Wash (closure-uncertain)).
- Sections: **10 ready** (both ends verified, map publishes), 4 approximate-area (both ends at least access-verified), 2 blocked.
- Excluded/deferred rivers or sections: 13 (research/excluded.json).

## Section status

| river/section | put-in -> take-out | miles (listed / NHD) | status | why |
|---|---|---|---|---|
| colorado-river-meander/moab-potash | Moab Bridge Boat Ramp -> Potash Boat Ramp | 17.1 / 17.16 | blocked | Moab Bridge Boat Ramp is pending: No current managing-agency page found for the Moab (US-191 bridge) ramp; UGRC 2009 attributes list State Sovereign Land. Coordinate is a candidate only.; Potash Boat Ramp is access-verified: Imagery: the NPS POI is in the river channel about 20 m off the west bank; the ramp/beach seen on imagery is about 110 m south. No BLM (managing-agency) page wa |
| colorado-river-moab/cisco-dewey-bridge | Cisco Takeout -> Dewey Bridge Boat Ramp | 16.0 / 16.04 | ready | - |
| colorado-river-moab/dewey-bridge-hittle-bottom | Dewey Bridge Boat Ramp -> Hittle Bottom Boat Ramp | 6.6 / 6.57 | ready | - |
| colorado-river-moab/moab-daily | Hittle Bottom Boat Ramp -> Takeout Beach Boat Ramp | 13.0 / 14.03 | ready | - |
| colorado-river-westwater/westwater-cisco | Westwater Ranger Station Boat Ramp -> Cisco Takeout | 17.0 / 17.42 | ready | - |
| green-river-desolation/sand-wash-swaseys | Sand Wash Boat Ramp -> Swaseys Boat Ramp | 84.0 / 82.79 | ready | - |
| green-river-desolation/nefertiti-swaseys | Nefertiti Boat Ramp -> Swaseys Boat Ramp | 8.5 / 8.28 | ready | - |
| green-river-dinosaur/lodore-split-mountain | Gates of Lodore Boat Ramp -> Split Mountain Boat Ramp | 44.0 / 43.6 | ready | - |
| green-river-flaming-gorge/flaming-gorge-a | Spillway Boat Launch (Flaming Gorge) -> Little Hole Boat Launch | 7.0 / 6.96 | ready | - |
| green-river-flaming-gorge/flaming-gorge-b | Little Hole Boat Launch -> Indian Crossing Boat Ramp | 8.4 / 8.24 | ready | - |
| green-river-flaming-gorge/flaming-gorge-c | Indian Crossing Boat Ramp -> Swallow Canyon Boat Ramp | 10.8 / 11.52 | ready | - |
| green-river-labyrinth/green-river-sp-mineral-bottom | Green River State Park Boat Ramp -> Mineral Bottom Boat Ramp | 68.0 / 68.19 | approximate-area | Green River State Park Boat Ramp is access-verified: Imagery: the UGRC 2009 point is on the sand ramp beside the dock (looks right), but there is no current agency coordinate. Coordinate comes from the 2009 UGRC b; Mineral Bottom Boat Ramp is access-verified: Imagery: the BLM GIS point is on the access road about 60-70 m south of the launch area, not on the ramp. The NPS POI (38.5249, -109.9933) sits at the launch be |
| san-juan/sand-island-mexican-hat | Sand Island Boat Launch -> Mexican Hat Boat Launch | 27.0 / 26.87 | approximate-area | Sand Island Boat Launch is access-verified: Imagery: the BLM point (and BLM page coordinate) is in the staging lot near the ranger station, about 40 m from the nearest bank and about 75 m from the launch ; Mexican Hat Boat Launch is access-verified: Imagery: the BLM point is at the entrance of the gravel launch area, about 50-55 m from the water. Too far from the water to pass. Official source names boating |
| san-juan/mexican-hat-clay-hills | Mexican Hat Boat Launch -> Clay Hills Boat Ramp | 57.0 / 56.54 | approximate-area | Mexican Hat Boat Launch is access-verified: Imagery: the BLM point is at the entrance of the gravel launch area, about 50-55 m from the water. Too far from the water to pass. Official source names boating; Clay Hills Boat Ramp is access-verified: Imagery: the BLM point is on a dirt track with no river visible; it is 263 m from the NHD centreline. The Clay Hills take-out shifts with Lake Powell sediment.  |
| san-rafael/fuller-bottom-swinging-bridge | Fuller Bottom (San Rafael Put-in) -> San Rafael Swinging Bridge Take-out | 18.0 / 17.37 | approximate-area | San Rafael Swinging Bridge Take-out is access-verified: Imagery: the BLM GIS point is in the campground loop about 50 m south of the river through trees, with no ramp visible. The BLM Swinging Bridge POI is on the ro |
| white-river/bonanza-enron | Bonanza Bridge Boat Launch -> Enron Boat Ramp (White River) | 35.0 / 34.67 | blocked | Bonanza Bridge Boat Launch is pending: BLM's own site record says the launch is on private property and open April 1-October 1 only; access permission/season not confirmable as public. Kept pending. |

## Shared endpoints (one fix unlocks several sections)

- Cisco Takeout (UT-ACC-0014, verified): colorado-river-moab/cisco-dewey-bridge, colorado-river-westwater/westwater-cisco
- Dewey Bridge Boat Ramp (UT-ACC-0015, verified): colorado-river-moab/cisco-dewey-bridge, colorado-river-moab/dewey-bridge-hittle-bottom
- Hittle Bottom Boat Ramp (UT-ACC-0016, verified): colorado-river-moab/dewey-bridge-hittle-bottom, colorado-river-moab/moab-daily
- Swaseys Boat Ramp (UT-ACC-0010, verified): green-river-desolation/nefertiti-swaseys, green-river-desolation/sand-wash-swaseys
- Little Hole Boat Launch (UT-ACC-0002, verified): green-river-flaming-gorge/flaming-gorge-a, green-river-flaming-gorge/flaming-gorge-b
- Indian Crossing Boat Ramp (UT-ACC-0003, verified): green-river-flaming-gorge/flaming-gorge-b, green-river-flaming-gorge/flaming-gorge-c
- Mexican Hat Boat Launch (UT-ACC-0022, access-verified): san-juan/mexican-hat-clay-hills, san-juan/sand-island-mexican-hat

Unlock candidates: **Mexican Hat Boat Launch** (access-verified) gates both San Juan sections; every other shared endpoint is already verified. Single fixes that would complete a river: Green River State Park + Mineral Bottom (labyrinth), Moab Bridge + Potash (meander), Sand Island + Mexican Hat + Clay Hills (san-juan), Swinging Bridge (san-rafael), Bonanza (white-river).

## Verified points (spot-check links)

| id | label | lat, lon | bank | coordinate source |
|---|---|---|---|---|
| UT-ACC-0001 | Spillway Boat Launch (Flaming Gorge) | [40.908759, -109.422174](https://www.google.com/maps?q=40.908759,-109.422174&t=k) | river-left | USFS EDW Recreation Opportunities, recareaid 72385 'Spillway Boat Launch Area' |
| UT-ACC-0002 | Little Hole Boat Launch | [40.910732, -109.315146](https://www.google.com/maps?q=40.910732,-109.315146&t=k) | river-left | USFS EDW Recreation Opportunities, recareaid 72387 'Little Hole Boat Launch Area' |
| UT-ACC-0003 | Indian Crossing Boat Ramp | [40.89699, -109.185357](https://www.google.com/maps?q=40.89699,-109.185357&t=k) | river-left | BLM National Recreation Site Points, OBJECTID 71216 'Indian Crossing Boat Ramp' (Boat Ramp |
| UT-ACC-0004 | Swallow Canyon Boat Ramp | [40.844332, -109.082401](https://www.google.com/maps?q=40.844332,-109.082401&t=k) | river-left | BLM National Recreation Site Points, OBJECTID 71219 'Swallow Canyon Boat Ramp' (Boat Ramp, |
| UT-ACC-0005 | Gates of Lodore Boat Ramp | [40.727114, -108.887881](https://www.google.com/maps?q=40.727114,-108.887881&t=k) | river-left | NPS Public POIs, OBJECTID 10790 'Lodore Boat Launch' (DINO) |
| UT-ACC-0007 | Split Mountain Boat Ramp | [40.44544, -109.252588](https://www.google.com/maps?q=40.44544,-109.252588&t=k) | river-right | NPS Public POIs, OBJECTID 4808 'Split Mountain Boat Launch' (DINO) |
| UT-ACC-0008 | Sand Wash Boat Ramp | [39.840465, -109.913676](https://www.google.com/maps?q=39.840465,-109.913676&t=k) | river-right | BLM National Recreation Site Points, OBJECTID 88966 'Sand Wash' (Boat Ramp, UTG02000 Price |
| UT-ACC-0009 | Nefertiti Boat Ramp | [39.195482, -110.077861](https://www.google.com/maps?q=39.195482,-110.077861&t=k) | river-left | BLM National Recreation Site Points, OBJECTID 69391 'Nefertiti Rapid Recreation Site' (Boa |
| UT-ACC-0010 | Swaseys Boat Ramp | [39.112376, -110.109071](https://www.google.com/maps?q=39.112376,-110.109071&t=k) | river-left | BLM National Recreation Site Points, OBJECTID 77691 'Swasey Rapid Boat Ramp Site' (Boat Ra |
| UT-ACC-0013 | Westwater Ranger Station Boat Ramp | [39.086657, -109.101309](https://www.google.com/maps?q=39.086657,-109.101309&t=k) | river-right | BLM National Recreation Site Points, OBJECTID 69678 'Westwater Ranger Station' (Boat Ramp, |
| UT-ACC-0014 | Cisco Takeout | [38.970407, -109.2506984](https://www.google.com/maps?q=38.970407,-109.2506984&t=k) | river-right | BLM Moab FO Cisco Takeout page, 'Geographic Coordinates 38.970407, -109.2506984' (the BLM  |
| UT-ACC-0015 | Dewey Bridge Boat Ramp | [38.811242, -109.308154](https://www.google.com/maps?q=38.811242,-109.308154&t=k) | river-left | BLM National Recreation Site Points, OBJECTID 68394 'Dewey Bridge Recreation Site' (Boat R |
| UT-ACC-0016 | Hittle Bottom Boat Ramp | [38.760191, -109.325455](https://www.google.com/maps?q=38.760191,-109.325455&t=k) | river-left | BLM National Recreation Site Points, OBJECTID 71172 'Hittle Bottom Recreation Site' (Boat  |
| UT-ACC-0017 | Takeout Beach Boat Ramp | [38.661778, -109.500696](https://www.google.com/maps?q=38.661778,-109.500696&t=k) | river-left | BLM National Recreation Site Points, OBJECTID 68336 'Takeout Beach' (Boat Ramp, 'Concrete  |
| UT-ACC-0024 | Fuller Bottom (San Rafael Put-in) | [39.118617, -110.855529](https://www.google.com/maps?q=39.118617,-110.855529&t=k) | river-left | BLM National Recreation Site Points, OBJECTID 68553 'San Rafael River Put In' (Boat Launch |
| UT-ACC-0027 | Enron Boat Ramp (White River) | [40.010178, -109.445989](https://www.google.com/maps?q=40.010178,-109.445989&t=k) | river-right | BLM National Recreation Site Points, OBJECTID 67149 'White River Enron Boat Ramp' (Boat Ra |

Spot-check first: Gates of Lodore Boat Ramp (point ~35-40 m from the launch beach; in Colorado); Hittle Bottom Boat Ramp (open launch area, not a paved ramp); Swallow Canyon Boat Ramp (dirt ramp road); Cisco Takeout (coordinate from BLM page, not GIS).

## Not verified (what each still needs)

- **Green River State Park Boat Ramp** (UT-ACC-0011, access-verified): Imagery: the UGRC 2009 point is on the sand ramp beside the dock (looks right), but there is no current agency coordinate. Coordinate comes from the 2009 UGRC boat-ramp layer, not from a Utah State Parks page; State Parks ramp-status page was blocked (403) so current ramp status not confirmed.
- **Mineral Bottom Boat Ramp** (UT-ACC-0012, access-verified): Imagery: the BLM GIS point is on the access road about 60-70 m south of the launch area, not on the ramp. The NPS POI (38.5249, -109.9933) sits at the launch beside the water: see research/replacement-proposals-UT.json. NHD is 111 m away. Official source names boating access, but the exact water-entry point is not pinned by an agency coordinate confirmed on imagery.
- **Moab Bridge Boat Ramp** (UT-ACC-0018, pending): No current managing-agency page found for the Moab (US-191 bridge) ramp; UGRC 2009 attributes list State Sovereign Land. Coordinate is a candidate only.
- **Potash Boat Ramp** (UT-ACC-0019, access-verified): Imagery: the NPS POI is in the river channel about 20 m off the west bank; the ramp/beach seen on imagery is about 110 m south. No BLM (managing-agency) page was found. Site lies outside Canyonlands NP; NPS POI and NPS flatwater page name it as a launch but no BLM (managing agency) page was found, so not verified.
- **Sand Island Boat Launch** (UT-ACC-0021, access-verified): Imagery: the BLM point (and BLM page coordinate) is in the staging lot near the ranger station, about 40 m from the nearest bank and about 75 m from the launch beach. Too far from the water to pass the imagery check. Official source names boating access, but the exact water-entry point is not pinned by an agency coordinate confirmed on imagery.
- **Mexican Hat Boat Launch** (UT-ACC-0022, access-verified): Imagery: the BLM point is at the entrance of the gravel launch area, about 50-55 m from the water. Too far from the water to pass. Official source names boating access, but the exact water-entry point is not pinned by an agency coordinate confirmed on imagery.
- **Clay Hills Boat Ramp** (UT-ACC-0023, access-verified): Imagery: the BLM point is on a dirt track with no river visible; it is 263 m from the NHD centreline. The Clay Hills take-out shifts with Lake Powell sediment. Official source names boating access, but the exact water-entry point is not pinned by an agency coordinate confirmed on imagery.
- **San Rafael Swinging Bridge Take-out** (UT-ACC-0025, access-verified): Imagery: the BLM GIS point is in the campground loop about 50 m south of the river through trees, with no ramp visible. The BLM Swinging Bridge POI is on the road at the north end of the bridge, and the BLM trailhead page coordinate is about 1.6 km away. Exact take-out is unresolved. Official source names boating access, but the exact water-entry point is not pinned by an agency coordinate confirmed on imagery.
- **Bonanza Bridge Boat Launch** (UT-ACC-0026, pending): BLM's own site record says the launch is on private property and open April 1-October 1 only; access permission/season not confirmable as public. Kept pending.

## Gauges and timing (kept separate from map points)

| river | gauge | reading at check (UTC) | refFlowCfs | timing grade |
|---|---|---|---|---|
| colorado-river-meander | USGS 09185600 Colorado River at Potash, UT | 11600.0 cfs @ 2026-10-25T19:45:00+00:00 | 11600 | unsourced / defer |
| colorado-river-moab | USGS 09180500 Colorado River near Cisco, UT | 7560.0 cfs @ 2026-10-25T19:00:00+00:00 | 7560 | unsourced / defer |
| colorado-river-westwater | USGS 09163500 Colorado River near Colorado-Utah state line | 5540.0 cfs @ 2026-10-25T19:45:00+00:00 | 5540 | unsourced / defer |
| green-river-desolation | USGS 09315000 Green River at Green River, UT | 5190.0 cfs @ 2026-10-25T20:00:00+00:00 | 5190 | unsourced / defer |
| green-river-dinosaur | USGS 09261000 Green River near Jensen, UT | 2710.0 cfs @ 2026-10-25T20:00:00+00:00 | 2710 | loosely-supported / defer |
| green-river-flaming-gorge | USGS 09234500 Green River near Greendale, UT | 1880.0 cfs @ 2026-10-25T19:30:00+00:00 | 1880 | unsourced / defer |
| green-river-labyrinth | USGS 09315000 Green River at Green River, UT | 5190.0 cfs @ 2026-10-25T20:00:00+00:00 | 5190 | loosely-supported / defer |
| san-juan | USGS 09379500 San Juan River near Bluff, UT | 19500.0 cfs @ 2026-10-25T20:00:00+00:00 | 19500 | loosely-supported / defer |
| san-rafael | USGS 09328500 San Rafael River near Green River, UT | 995.0 cfs @ 2026-10-25T20:00:00+00:00 | 995 | unsourced / defer |
| white-river | USGS 09306500 White River near Watson, UT | 316.0 cfs @ 2026-10-25T19:45:00+00:00 | 316 | loosely-supported / defer |

All 10 catalog gauges returned current discharge. 30 gauges checked in total; no current discharge from: 10159500, 10161000, 10133500, 10167000, 10167230, 10118000, 09328100, 09328060, 09235000 (none used in the catalog).
refFlowCfs is the reading at check time, not a typical-season value. refSpeedMph 3.0 is a schema-required placeholder with no source. research/trip-times/UT.json is empty (no dated trip with hours on a catalog section was found); agency multi-day durations (DINO, Desolation, Labyrinth, San Juan, White) are recorded in timing-status-UT.json only. Recommendation: hide float-time estimates for Utah until real trips are logged.

## Cross-state reaches

- Gates of Lodore Boat Ramp is in **Colorado** (NPS DINO); green-river-dinosaur crosses CO -> UT. Kept with state UT because the take-out and most of the reach is in Utah; review whether the app expects in-state points only.
- Westwater gauge 09163500 is at the Colorado-Utah state line; the Ruby-Horsethief reach (CO) is excluded and belongs in a CO package.
- White River and the Colorado (Westwater/Moab) flow in from Colorado; the San Juan enters from New Mexico/Colorado, and the BLM permit zone starts at Montezuma Creek. Only Utah sections are catalogued.
- Yampa (mostly CO) and Dolores (mostly CO) are excluded.

## Flags

- **Permits**: green-river-dinosaur: True; green-river-desolation: sand-wash-swaseys only; green-river-labyrinth: True; colorado-river-westwater: True; colorado-river-moab: False; colorado-river-meander: only for nights inside Canyonlands NP; san-juan: True; san-rafael: False; green-river-flaming-gorge: False; white-river: False. Statewide: [{'fact': 'Inflatable PFDs are not allowed on any rivers in Utah (quoted on the NPS Canyonlands river page).', 'source': 'https://www.nps.gov/cany/planyourvisit/boatinginfo.htm', 'quote': 'Inflatable PFDs are not allowed on any rivers in Utah.', 'rawFile': 'research/raw/agency/nps_cany_boatinfo.txt'
- **Closures**: green-river-dinosaur ['rainbow-park-split-mountain']: closed; (excluded) colorado-river-cataract ['(not in catalog) potash-north-wash']: closure-uncertain. Rainbow Park is excluded until NPS reopens it; North Wash/Cataract not added.
- **Advisories**: BLM: the Bonanza Bridge launch is on private property and is open Apr 1-Oct 1 only (closed today, 2026-10-25). | USGS 09379500 read 19,500 cfs at check time (2026-10-25 20:00 UTC; 14:00 MDT). No historical/typical-flow statistics were pulled, so this package only notes it as a high reading to re-check before any trip; it is also used as refFlowCfs, which is therefore not a typical-season value. | BLM: the Mineral Bottom road 'can be very slick and impassible when wet... Four wheel drive vehicles are recommended.' | BLM: 'There is a dangerous waterfall downstream from Clay Hills.' Clay Hills is the only viable take-out below Mexican Hat.
- **Dangerous rapids / hazards**: Red Creek Rapids (flaming-gorge-b; USFS: 'Class III – IV'); Joe Hutch Rapid on Desolation (BLM: can elevate to Class IV-V- at high water); Westwater Canyon (BLM: 'includes Class IV rapids... challenging at all water levels... experienced boaters'); Moab Daily rapids Class I to III depending on season and water level (BLM).
- **Take-outs above falls**: Clay Hills is the only viable take-out below Mexican Hat and BLM warns of a dangerous waterfall downstream of it. Enron is the last public take-out before the Uintah & Ouray Reservation on the White River (tribal permits beyond). The Desolation east bank is also reservation land (tribal permit to camp/hike).
- Mexican Hat: BLM reports vehicle break-ins. Mineral Bottom: steep switchbacks, 4WD, impassable when wet. Bonanza: private, open Apr 1-Oct 1 (closed now).

## Geo checks

33 points and 16 sections checked against NHD High Resolution flowlines and TIGERweb roads. Flagged points: 2 (Clay Hills 263 m from centreline, inside its 400 m approximate radius). Flagged sections: 0; every take-out routes downstream of its put-in and all listed miles are within 8% of the centreline.

## Replacement proposals (none applied except Cisco, noted for review)

- Mineral Bottom Boat Ramp (UT-ACC-0012): proposal. Imagery (research/raw/imagery/mineral_bottom_boat_ramp.png): the NPS point is at the launch beside the water, while the BLM point is on the access road 60-70 m south. The NPS is not the managing agency (the site is BLM), so a human must decide whether an NPS coordinate is acceptable.
- Cisco Takeout (UT-ACC-0014): applied-in-package (review). Imagery: the GIS point is on the access loop about 150 m from the river; the BLM page coordinate is at the head of the concrete ramp. Both are BLM. Recorded here for review even though it is already in the data.
- San Rafael Swinging Bridge Take-out (UT-ACC-0025): needs-decision. Three BLM coordinates disagree: GIS 71217 in the campground loop, the Swinging Bridge POI at the north end of the bridge, and the trailhead page about 1.6 km away. A human should mark the real take-out on imagery (research/raw/imagery/san_rafael_swinging_bridge_take_out_z17.png).
- Potash Boat Ramp (UT-ACC-0019): needs-decision. The NPS POI is in the river. The ramp seen on imagery is about 110 m south (research/raw/imagery/potash_boat_ramp.png). There is no agency coordinate for the ramp itself.

## Honesty notes / not done

- Many Utah rivers were not researched (see research/excluded.json: Ouray-Sand Wash, Provo, Weber, Bear, Jordan, Logan, Price, Virgin, Escalante, Muddy, Black Boxes, Dolores in UT, Cataract). They are listed so they are not mistaken for checked-and-rejected.
- Blocked fetches (research/raw/agency/BLOCKED_FETCHES.md): Utah State Parks Green River pages (404/403), Jordan River pages (403/406), BLM Rocky Rapid and Westwater Ranger Station pages (404), a Utah DOR North Wash page (403).
- Imagery review used Esri World Imagery tiles (dates unknown). Verified points rely on agency GIS/page coordinates plus that check; none is IMAGERY-PLACED.
- The access-verified boating word list includes 'take-out', 'take out' and 'boat ramp' (added for Utah). This is a deliberate widening and is also in tools/validate_ut.py.
- Mileage for cisco-dewey-bridge, dewey-bridge-hittle-bottom and moab-potash came from NHD routing because no agency mileage was found; the notes say so.
- The validator proves structure and the package rules only, not that the facts are true.

## Validator output (python3 tools/validate_ut.py)

```
Builder: reference/schema/tools/build_catalog.py (sha256 f8fed0f6e8510ad2…)
Base catalog: /workspace/floateta-utah-v1/reference/examples/catalog
  (default mode) MT.json: ignoring 23 audits for MT rivers not included in the reference export
Catalog valid: 11 rivers total (10 UT, 1 other)
UT: 16 sections, 25 registry points (16 verified, 9 pending), rivers verified 5/10
Access grades (research-only): 16 verified, 7 access-verified, 2 pending
UT sections that would publish a map: 10
UT checks passed: pending points have only status+note; every section label is a registry key; audits consistent; research files match templates; access grades complete, access-verified entries have official source + centre, verified grades match the registry, closure-uncertain points not promoted.
EXIT=0
```
