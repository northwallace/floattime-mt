# Float ETA local site and map audit — October 27, 2026

> Follow-up: the five mileage conflicts below were resolved locally later on October 27. See [the Montana fixes and launch review](PRELAUNCH_REVIEW_20261027.md) for current status. This file preserves the initial audit findings.

## Decision
Do not launch the entire catalog as verified. The local preview now contains the reviewed Colorado v1.1 catalog plus the existing MT/WA/UT/AZ registries. There are 100 river records and 187 sections. Maps are available for 78 sections; 109 have no eligible map. Five mapped Montana sections have impossible mileage and explicit review warnings, with time estimates disabled. The other 73 maps are candidates for staged release, not individually certified by this audit.

## Coverage
| State | Specific access maps | Approximate access maps | Unavailable |
|---|---:|---:|---:|
| Montana | 30 (5 flagged) | 0 | 24 |
| Idaho | 0 | 0 | 26 |
| Oregon | 0 | 0 | 12 |
| Washington | 10 | 2 | 23 |
| Utah | 10 | 3 | 3 |
| Arizona | 2 | 4 | 13 |
| Colorado | 13 | 4 | 8 |

Idaho and Oregon have no reviewed access registries in the supplied research packages. Draft/candidate coordinates have not been promoted. Approximate markers identify facilities, not exact landings. Montana state trust land is the only public-land overlay currently implemented. Maps do not trace or certify a navigable river channel.

## Changes made
- Imported Colorado v1.1: 10 records, 25 sections. Preserved raw evidence and research separately.
- Reused Utah's authoritative Westwater and Split Mountain points through explicit cross-state references. No silent matching by name. Referenced points becoming pending also disable the dependent map.
- Added validated, dated agency notices to calculator sections and server-rendered river guides. Previously several Colorado updates existed only in research files.
- Added a repeatable mileage sanity audit and disabled estimates for flagged sections.
- Improved homepage wording for rivers without timing models, removed the empty large time display for these sections, added Colorado navigation, and corrected the map heading outside Montana.
- Kept existing corrections and float-request forms/private review queue.

## Blockers and priorities
1. **Resolve five mileage/endpoint conflicts.** Straight-line distance cannot exceed actual river mileage. Blackfoot Roundup→Johnsrud: listed 10 vs 11.76 direct miles; Johnsrud→Weigh Station: 8 vs 8.60; Missouri Holter→Craig: 3.5 vs 5.80; Craig→Mountain Palace: 8 vs 9.05; Stillwater Cliff Swallow→Absarokee: 6 vs 7.98. These could be wrong endpoints, wrong mileage, or both. No replacement values were invented. Inspect the sourced ramp identities and river-route mileage before removing flags.
2. **Satellite production arrangement.** The preview directly uses Esri World Imagery and reference tiles with static attribution. Confirm the production service entitlement and required provider attribution for this exact usage before rollout. No paid account was created. Esri documents service access and attribution at https://developers.arcgis.com/documentation/mapping-and-location-services/mapping/basemaps/introduction-static-basemap-tiles-service/ .
3. **Legacy timing evidence.** 54 river records use legacy reference speeds without the newer explicit timing-source metadata; 46 correctly suppress uncalibrated models. Structural checks do not establish accuracy. Review high-traffic river models against same-section trip observations before advertising precision.
4. **Maps on river-guide pages.** These still use a simple OpenStreetMap overview, while the calculator has labelled satellite access markers. Unifying them would remove an inconsistent experience and make the takeout easier to identify.
5. **Review workflow.** Corrections/requests save privately, but there is no owner dashboard or automatic notification. The review CLI works; an authenticated review inbox is the next practical improvement once submissions increase. Basic abuse guards should be strengthened for public traffic.
6. **Remaining access research.** Missing coordinates, unresolved private access, and vague facility locations remain explicit pending records. The full per-section queue is in site-audit-20261027.json. Prioritize popular missing sections rather than blanket-promoting points.

## Verification evidence
- 117 HTTP requests passed: all 100 river guides, seven state pages, main/static pages, sitemap/robots, health and reports endpoints.
- 28 Python and 18 JavaScript tests pass (46 total), including cross-state reference failures, propagation of pending points, unsafe notice URLs, timing suppression, feedback validation, and cache behavior.
- Catalog rebuild/check and whitespace checks pass.
- Sampled real USGS proxy requests returned readings for MT, ID, OR, WA, UT, AZ, CO. This was seven catalog gauges, not a full gauge availability audit. One initial test used a noncatalog Oregon ID and correctly received 404; the catalog's 14092500 returned data.
- Browser checked Colorado cross-state satellite map with both markers; Montana satellite map with two DNRC tracts; Utah approximate map on a 390px phone viewport. No errors in those sampled browser consoles. Mobile view showed no horizontal overflow.
- Location control exists but this in-app browser reports geolocation unavailable; real-device permission and location accuracy remain untested.
- HTTPS requests to www.floateta.com succeeded; the apex domain redirected to www. This confirms this machine's current connection only, not every device/network from the earlier Safari report.
- Production still returns the older Python version header. Local security/header fixes remain undeployed.
- This audit did not visually inspect every individual access pin or perform on-water verification.

## Commands
```
python3 tools/build_catalog.py --check
python3 tools/audit_map_readiness.py
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.cjs
```

Local preview: http://127.0.0.1:8777/
Backup before changes: /Users/home/Documents/Codex/FloatETA-before-audit-20261027/
Nothing committed, pushed, or deployed.
