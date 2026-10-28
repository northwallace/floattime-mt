# Local Montana fixes and launch review — October 27, 2026

Nothing was committed, pushed, or deployed. Preview: http://127.0.0.1:8777/ .
The current preview is bound to 127.0.0.1, not all network interfaces.

## Mileage corrections

| Section | Previous miles | Approximate corrected miles |
|---|---:|---:|
| Blackfoot: Roundup Bridge → Johnsrud Park | 10 | 16.5 |
| Blackfoot: Johnsrud Park → Weigh Station | 8 | 10.7 |
| Missouri: Holter Dam → Craig | 3.5 | 7.7 |
| Missouri: Craig → Mountain Palace | 8 | 13.4 |
| Stillwater: Cliff Swallow → Absaroka FAS | 6 | 9.6 |
| Blackfoot: Russell Gates → Roundup Bridge | 9 | 11.1 |
| Stillwater: Absaroka FAS → Whitebird | 7 | 7.9 |

The first five resolve the initial audit flags; the last two were adjacent sections checked with the same sources. Distances are the difference between nearby Montana FWP 0.1-mile markers on the same river, not road distance, straight-line distance, or an inferred navigable channel. Marker-to-facility offsets are preserved in the evidence. Nearest marker selection introduces uncertainty; the UI explicitly displays approximate mileage.

Primary service: https://fwp-gis.mt.gov/arcgis/rest/services/refrnc/riverMiles/MapServer/2 . Exact requests, response features, stream IDs, marker IDs, coordinates and distances are saved in `MT/mileage-20261027/fwp-mile-markers.json`. The stream IDs were deliberately selected for these three rivers; this was not automatic matching across arbitrary waterways. Agency guides corroborate the endpoint order and approximate river miles.

Corroborating access guide: https://fwp.mt.gov/binaries/content/assets/fwp/fish/misc/fas-guide---2017---fullversion.pdf (printed pages 25, 27, 63, 79). This older guide supports names, banks and river-mile order; it does not establish current closures or ramp condition.

Blackfoot rapid guide: https://fwp.mt.gov/binaries/content/assets/fwp/activities/river-recreation/black-foot-river-floaters-guide.pdf . Map 6 (printed pages 24–25) places Thibodeau upstream of Johnsrud and marks Class II/III rapids. Roundup–Johnsrud is now Class II–III and no longer receives tube/SUP estimates. Map 4 shows Bear Creek Rapids on Russell Gates–Roundup. Removed the incorrect Thibodeau statement from Johnsrud–Weigh Station and an unsupported generic rowing instruction from Stillwater.

The Stillwater access label is now **Absaroka FAS**, matching agency naming. Section IDs remain unchanged so existing links and corrections remain associated with the same sections.

## Access precision

Holter Dam's existing BLM source coordinate identifies the campground and boat-ramp facility, not a demonstrated ramp-edge survey. It now uses `access-verified` with an approximate facility marker and explicit directions. No new exact launch coordinate was invented. Its distance can still be estimated approximately from agency river miles. Original BLM source: https://www.blm.gov/visit/holter-dam-campground . That page timed out during this follow-up, so no current closure claim was added.

Coverage remains 78 mapped sections: 64 with specific sourced facilities and 14 with approximate facilities. There are 109 sections without eligible maps, including 24 in Montana. The new geographic check does not certify every access pin, channel, bank, or land parcel. Pending points remain pending.

## Code and presentation fixes

- Added validated `distanceEvidence` to the seven sections. It records endpoint coordinates, source/date, stream identity, river measures and marker offsets. Renaming an endpoint, moving a published pin, or changing mileage without updating the evidence now fails validation.
- Impossible mapped mileage is checked by the catalog build itself. A flagged section can still publish access information only with an explicit review notice and disabled estimates. The separate readiness command reports coverage.
- Source disclosures appear in both calculator cards and river guides.
- River-guide map links open the matching section's satellite/access map. Removed unlabelled overview iframes. Open maps can be shared with their section selected; changing rivers clears the selection.
- Holter's approximate location is labelled in the header, marker and source status. Map fitting leaves space for provider attribution on small phones.
- Original timing models are described as rough planning guidance. Correcting mileage does not validate reference speeds; no calibration numbers were invented.
- HTML automatically fingerprints its local CSS/JS references. Only matching file hashes get immutable caching; changing an asset also changes the static HTML ETag. This fixes returning browsers retaining old calculator code after deployment.
- Updated map credits from current service metadata, including reference-layer credits. This does not settle production licensing.

## Verification

- 38 Python tests and 18 JavaScript tests pass (56 total).
- Catalog rebuild/check passes for 100 rivers and 187 sections.
- No impossible mapped-distance flags remain. Snapshot: `map-readiness-after-mt-20261027.json`.
- 115 HTTP page checks passed, including all 100 river guides and all seven state pages. No Python version header on these local responses.
- All three affected gauges returned recent positive readings through the server's USGS Water Data API proxy: Blackfoot 690 cfs, Missouri 2,700 cfs, Stillwater 451 cfs at the time of the check. These are test observations, not persistent trip advice. Evidence: `MT/mileage-20261027/local-checks.json`.
- Browser checked the Blackfoot section link, labelled satellite map and Montana land layer; current-flow raft estimate; and Class III tube suppression. Holter checked at 390px phone width with approximate location text and no horizontal overflow. Both markers remain clear of expanded credits; the tapped source card fits inside the map. Preview screenshot: `/Users/home/Documents/Codex/FloatETA-Montana-corrections-20261027.png`.
- Real-phone GPS permission and accuracy have not been tested; the in-app browser has no working location fix.
- `git diff --check` passes. Backup: `/Users/home/Documents/Codex/FloatETA-before-mt-fixes-20261027/`.

## What remains before public map rollout

1. **Set up or confirm satellite service access.** The anonymous World Imagery endpoint loading successfully is not proof that this application has production entitlement. Its item links to Esri's terms: https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9 . The associated summary (https://goto.arcgis.com/termsofuse/viewsummary) describes account/software conditions. The documented Location Platform basemap service requires an account/token: https://developers.arcgis.com/documentation/mapping-and-location-services/mapping/basemaps/introduction-static-basemap-tiles-service/ . No account, purchase, or contract was created. Confirm the appropriate service plan, restrict its browser key to Float ETA, and configure/test it before release.
2. **Phone smoke test.** Check a supported HTTPS test deployment in Safari/Chrome for location permission, denied permission, approximate GPS circle, map interaction and share-link restoration. This needs a real phone; local responsive testing cannot establish GPS behavior. Do this before enabling location publicly.
3. **Release only the supported coverage.** Missing maps need not block publishing already-reviewed information, but do not advertise complete map coverage or certify remaining pins from this audit. Holter must retain its approximate status unless better evidence is supplied.
4. **Operate the feedback queue.** Use `python3 tools/review_feedback.py` in the environment that holds submissions. The private queue and basic per-page throttling work; a larger public rollout should add stronger abuse protection and an owner notification/review workflow. Submissions never change the catalog automatically. Confirm the existing Render persistent data directory before deployment so submissions survive restarts.

Measured trip observations are the next accuracy improvement. The legacy reference-speed models remain provisional; the 46 rivers without timing models still do not manufacture live estimates.


## ArcGIS local integration follow-up

Created the Float ETA Location Platform public-app credential on October 27, 2026. It has Static basemap tiles permission only, no item/general/admin privileges, the referrer `http://127.0.0.1:8777`, and expiration January 25, 2027. The dashboard explicitly showed pay-as-you-go disabled and $0.00 owed. The key value is only in ignored `map-config.local.json`, with filesystem mode 0600; it is not in this report or committed source.

Local maps now request World Imagery from `ibasemaps-api.arcgis.com` and labels from `static-map-tiles-api.arcgis.com`, both with the public token. Both returned image tiles successfully. Label tiles rejected a mismatched referrer (401). The imagery tile endpoint returned a cached image for that mismatched referrer as well, so do not describe referrer restrictions as guaranteed protection. PAYG remains disabled. Current source credits were taken from service metadata. Distinct 256px imagery / 512px label grid sizes are preserved.

Browser verification: satellite image and road labels rendered; Blackfoot map loaded 32 DNRC tracts; zoom worked; Roundup take-out popup showed source links and river-right guidance. Expanded attribution initially covered a landing on a narrow screen; increased fit padding and adjusted popup panning now keep the marker above credits. No browser errors were observed. Native phone GPS remains untested. No site deployment occurred.

Validation: 40 Python and 19 JavaScript tests pass, including map-config allowlisting, no-store responses, absent/malformed configuration, private config-file URL returning 404, authenticated tile templates, and tile-grid sizes. Before production, create a separate domain-restricted key and put it in the hosting environment as `ARCGIS_BASEMAP_API_KEY`; do not deploy the local key/file. Complete the remaining release checklist above.


## Production key staged and local progress pilot (October 27 follow-up)

Generated a separate public Static basemap tiles credential for the two Float ETA HTTPS domains. Expires October 26, 2027 at 11:59 PM MDT. Saved `ARCGIS_BASEMAP_API_KEY` to Render using **Save only**, verified the success alert and masked environment row. No deploy, commit, push, plan change, or PAYG activation. The live service remains on commit `f96509158c938372727952b1ab4a5c606ea9a4b3`. Production tile rendering still requires a future authorized deployment check. No credential value is stored in this report or source control.

Implemented a local-only Johnsrud Park → Weigh Station progress pilot using official FWP PNW hydrography, not an invented straight line. Route and raw DNRC evidence are under `research/MT/route-pilot-20261027/`; reusable geometry/projection helpers are in `public/route-progress.js`. The local index gates just this section. Measurements: 10.7328 miles, 175 vertices, endpoint offsets 37.5/56.9 metres. The agency line is approximate and has not been field validated as the navigable channel. The new near-river display clips DNRC polygons to 150 metres, 13 source candidates → 8 visible tracts. It does not establish legal or physical access and does not change other river maps.

Browser verified midpoint demo (5.4 miles, 1 hr 30 min at example 1,200 cfs), fishing adjustment (3 hr 45 min), weak/off-route/stale GPS suppression, near-take-out wording, leaving demo and switching to a nonpilot map. Actual device GPS cannot be tested in this in-app browser. Automated tests cover curved routes, ambiguous hairpins, GPS freshness/accuracy, data-to-catalog consistency, controller estimates, unavailable flow, cleanup and production-disable behavior. Existing Python and JavaScript regression checks and catalog/readiness checks passed. Readiness coverage remains 78 of 187 sections; this pilot does not certify new access points.

Saved proof: `/Users/home/Documents/Codex/FloatETA-production-key-staged.png` and `/Users/home/Documents/Codex/FloatETA-time-remaining-pilot.png`. Next step is owner review of the local sample, then a separately authorized HTTPS phone/field test before any public progress feature.


## Reusable route foundation; live ETA deferred

At the owner's request to defer winter field work, disabled the local GPS ETA experiment and separated reviewed map routes from it. Generated a Montana source-import/review queue for all 54 sections. Thirty have existing eligible maps and received candidate geometry from nine explicitly identified FWP stream records. Ten passed the 100 m endpoint, 5% mileage, 1 km maximum segment, downstream-measure and non-self-intersection checks, and were accepted for approximate map display after desktop source review. Twenty remain candidates. Twenty-four additional sections lack eligible access points and received no invented line.

Enabled sections: Bitterroot Darby–Wally; Blackfoot Roundup–Johnsrud and Johnsrud–Weigh Station; Jefferson Cardwell–Sappington and Williams–Drouillard; Upper Madison Lyons–Palisades and McAtee–Varney; Stillwater Cliff Swallow–Absaroka and Absaroka–Whitebird; Yellowstone Emigrant–Mallard's Rest. Source snapshots are immutable/checksummed, with stored source stream IDs and endpoint snapshots. No field/navigability or actual trip-time accuracy claim is made.

Nine narrow DNRC corridors built successfully. McAtee–Varney has an invalid agency polygon, recorded in `research/routes/MT/land-review-queue.json`; its land overlay is withheld rather than guessed. Nine valid overlays contain 14 visible tracts in total (8 Blackfoot, 6 Yellowstone); the seven empty results concern DNRC trust lands only, not all public land. Route display, land overlay, calculator distance adoption and GPS ETA are independently gated; the last two remain false. There were no new access-point promotions and no changed calculator mileages.

The biggest discrepancy flagged is Lower Madison Blacks Ford–Greycliff (source path about 4.37 mi vs catalog 9 mi, offsets 150/308 m). This needs endpoint/source research, not automatic correction. Full actionable queue: `research/routes/MT/review-queue.json`. New imports stage candidates and cannot overwrite reviewed records. Existing catalog `--check` now validates review/geometry/evidence consistency and detects stale public route assets; builds remove withdrawn generated routes. GIS dependencies are only needed for importing and clipping, not serving the app or CI checks.

Browser checked Blackfoot route display and near-river land, Upper Madison route bends, McAtee–Varney withheld land, and Yellowstone land clipping. ETA panel stays hidden on reviewed route maps. Failed route loading retains ordinary access markers. The existing production key remains staged only; Render, deployment settings and live site were not changed during this work. All changes remain local.

Validation completed: 49 Python tests and 26 JavaScript tests passed; catalog and generated-route freshness checks and `git diff --check` passed. A repeated cached agency import left every registered route and public asset hash unchanged. A browser test with a temporarily unavailable route asset retained both access markers, displayed an unavailable-line message, and kept GPS ETA hidden; the asset was restored and build checks passed. Preview screenshot: `/Users/home/Documents/Codex/FloatETA-route-foundation-20261027.png`.


## Montana follow-up — local access and route fixes (2026-10-27)

This section supersedes the counts and the McAtee–Varney limitation in the previous route-foundation entry. Production, Render settings and deployment keys were not changed.

### Corrections and new coverage

- Lower Madison Black’s Ford–Greycliff: **9 → about 4 miles**. FWP's 2017 Fishing Access Site Guide identifies Black’s Ford at river mile 24 (printed p. 51) and Greycliff at mile 20 (p. 49). These are rounded guide values, not a newly measured GPS distance. The independent staged centerline is roughly 4.37 miles, reinforcing that 9 miles was wrong; it remains unapproved because endpoint positions are only facility-level.
- Missouri Breaks: **149 → 88.5 miles**, with the start explicitly renamed **Fort Benton (Canoe Launch)**. BLM lists that launch at mile 0 and Judith Landing at 88.5; 149 is James Kipp. Removed the unsupported 3–4-day promise. The canoe launch must not be substituted with the downstream motorboat launch. A map is still withheld while the starting coordinate is unresolved.
- Smith: **58.8 miles**, following the 2026 FWP management plan p. 19. Camp Baker and Eden Bridge now have **approximate facility markers** from the actual geometry in the current FWP State Parks GIS response. The attribute-table latitude/longitude disagree with geometry for Camp Baker; the coordinate-source distinction is retained in the research. No exact landing or bank claim is published.
- North Fork Flathead: three new access maps and three approximate river-bend routes. Published April 2026 Flathead Rivers Alliance / DREAM surveys give coordinates, photographs and river miles for Polebridge **Downstream**, Coal Creek, Big Creek and Glacier Rim. Planning distances are 9.3, 9.2 and 11.5 miles. The independent FWP centerline cuts measure about 9.18, 9.33 and 11.39 miles; offsets are 46–80 m. Coal Creek's side-channel/wood/low-water caveat and Big Creek's fee are visible. Bank metadata is deliberately absent. Big Creek–Glacier Rim now says Class II–III and links a firsthand Rocky Mountain Canoe Club trip report describing the lower canyon Class III rapids; recreational tube/SUP estimates are suppressed by the existing craft guard.
- Glen FAS, Black’s Ford and Greycliff: retained their agency coordinates as approximate facility locations rather than falsely precise ramps. Removed unsupported bank metadata from those approximate records. All four affected section maps remain available. Exact landing coordinates are still unresolved.
- Judith Landing and Carbella: added BLM-supported approximate facility records and access directions. These do not open a section map while its other endpoint remains unresolved. Carbella's current hard-sided-camping restriction is included as a dated BLM notice.
- Gallatin Valley: disabled the time model while Shedd's Bridge is an unresolved take-out. The old closure note now cannot coexist with a reassuring calculated trip time. This does not claim a newly confirmed closure; it explains the historical FWP warning and lack of current replacement evidence.

### Land, validation and scalability

McAtee–Varney's DNRC tract 11955 has a self-touching ring with a zero-area line artifact. Conservative normalization preserves its area (difference under 0.000000001 square metre) and introduces no new boundary. Raw geometry remains saved. One near-river tract can now display. Area-changing repairs remain rejected and are covered by a bow-tie regression test.

All map land shading now comes from reviewed 150 m river corridors. Broad endpoint-rectangle queries were removed, avoiding unrelated inland properties and large Smith River requests. Missing/unreviewed corridors still show the satellite map and access markers, with an explanation instead of guessed land shading. DNRC trust-land coverage is not all public land and does not establish landing rights.

Current Montana coverage: **34 of 54 sections have access maps** (28 specific sourced access maps, 6 approximate facility maps); **20 still lack eligible endpoint pairs**. **13** reviewed centerlines and **13** checked land-corridor assets are available; the corridors contain **18** clipped features total, with some empty DNRC results. Calculator mileage adoption from lines and live GPS time remaining remain disabled. Standard catalog validation covers `published-guide-miles` in either downstream measure direction, named endpoint changes and mileage edits. New imports keep approved routes intact and now include the specific missing-access reason in every blocked queue row.

Evidence is in `research/MT/access-review-20261027/`; the current actionable route queue is `research/routes/MT/review-queue.json`. Existing remaining blockers are route-definition and access-evidence issues, including Rock Creek's ambiguous labels, Shedd's Bridge, Barretts Dam, unnamed confluence exits, and exact landing offsets. Passing the automated tests is not field verification.


Follow-up verification: 55 Python tests passed in the GIS development environment (the three GIS-only tests also run separately; standard-library Python passes the other 52). All 26 JavaScript tests passed. Catalog/route freshness and geographic-readiness checks passed with no impossible-distance flags, and `git diff --check` passed. Browser checks confirmed the three new North Fork routes, Smith's approximate markers and source popup, corrected Lower Madison distance/labels, McAtee–Varney's restored clipped tract, and Class III tube-estimate suppression. The local map configuration returns 13 reviewed routes and no GPS experiment entries. Source descriptions and timing reasons appear on server-rendered river pages. No on-water GPS or travel-time accuracy was tested.

The restarted local server returned successful USGS proxy responses for Lower Madison and North Fork Flathead; the browser showed a recent North Fork reading and a calculated raft estimate. Final preview: `http://127.0.0.1:8777/?river=flathead-north&state=MT&craft=raft&section=coal-big-creek&map=1#calculator`. Saved screenshot: `/Users/home/Documents/Codex/FloatETA-Montana-followup-20261027.png`.


## Montana-first release candidate — final local checks (October 27)

**Recommendation: ready for a limited Montana map launch once publication is explicitly authorized.** This does not certify every Montana section or claim field-tested navigation. Nothing was committed, pushed or deployed; the local preview remains on port 8777. Other states retain their river guides and source research, with interactive maps withheld by the state rollout allowlist.

The release contains **34 Montana section maps out of 54**: 28 specific sourced access maps and 6 approximate facility maps. **13** reviewed approximate river paths and their 150-metre land corridors display. The remaining **20** maps stay withheld. Of these, **13 sections now have explicit access/route holds** that suppress calculated time, map eligibility, SEO reference times and generic tube recommendations. Gallatin Valley already had an unavailable timing model for the unresolved Shedd's Bridge take-out. The research queue distinguishes 13 access/route issues from 7 remaining endpoint-coordinate issues. No pending point was promoted just to increase coverage.

### Fixes in this candidate

- Added `mapRelease.states` and `mapRelease.reviewedRoutes` to catalog settings. Generated `mapReleased` is enforced by map buttons, direct links, map-opening code and server-rendered guides. Production configuration can now return the reviewed Montana route index; the prior implementation enabled lines only through the local key file. GPS time remaining and automatic distance adoption stay disabled independently.
- Added `accessReview` as a per-section hold, separate from missing coordinates or distance review. Held cards identify the route and mileage as unverified rather than showing reassuring times or difficulty badges. Source details and correction links remain available.
- Corrected the Caras Park–Kelly Island description. The [City of Missoula](https://www.ci.missoula.mt.us/1227/Silver-Park-Boat-Landing) identifies Silver Park as the last public exit before the Grass Valley diversion dam, with Kelly Island below it. The old mellow/Class I description is not offered as trip guidance. Sha-Ron–Caras also needs a specific confirmed landing; no substitute endpoint or mileage was invented.
- Renamed the Beaverhead take-out to **Barretts Station Park (above dam)**. [Visit Montana](https://visitmt.com/listing/barretts-station-park-campground-1984) and Bureau of Reclamation material document a take-out before the diversion dam. An absent FWP record was not evidence of no public access. The exact landing coordinate remains pending, and the map stays closed.
- Corrected Rock Creek's seasonal wording using [2026 FWP fishing regulations, printed/PDF page 40](https://fwp.mt.gov/binaries/content/assets/fwp/fish/regulations/2026-fishing-regulations-final-for-web.pdf): July 1–November 30 restricts fishing from boats/vessels, not all floating. A dated source notice appears on all three sections. Ambiguous endpoints remain held.
- Corrupt report/contact/suggestion files now fail with HTTP 503 instead of being treated as empty arrays. Atomic saves flush the file before replacement; write failures cannot report success. Regression checks preserve corrupt files and reject failed writes.
- Concurrent requests for one USGS site share one upstream download. Nonfinite readings are filtered, and fallback cached readings explicitly say the USGS refresh was unavailable. Original observation timestamps still control eligibility for estimates.
- Updated the researcher contract, rollout instructions and inaccurate hosting documentation. Bulky downloaded source PDFs remain local caches; reviewed JSON source snapshots/checksums remain part of the release. A clean release snapshot is about 11 MB and excludes private data and local credentials.

### Verification and hosting evidence

- **61 Python tests passed**, including GIS checks in the development environment; the standard-library production run passes with its 3 GIS-only checks skipped. **29 JavaScript tests passed.** Catalog/route freshness, geographic sanity and `git diff --check` passed. A clean copied release snapshot also passed the standard-library catalog/build tests without the private key file or local submission data.
- Opened **all 34 released maps** in the browser: all had both markers; all 13 reviewed lines displayed. Checked mobile popup/zoom and provider attribution. Direct Washington `map=1` URLs did not open an unreleased map. Held Missoula sections did not offer estimates; their correction link preselected the right river and section.
- Tested calculator, guide, directory and request pages at 320, 390, 768 and 1280 pixel viewport widths; no document-level horizontal overflow. Browser tests submitted a correction and float request to a separate temporary data directory on port 8778; both persisted privately with `pending` status and did not alter catalog data. That test server was stopped.
- All **24 Montana USGS sites** returned positive recent readings through the local server's new Water Data API proxy. Observation ages were roughly 20–80 minutes at the check. See `research/MT/access-review-20261027/release-gauges.json`.
- Read-only Render check confirmed the existing paid `0.5c-512mb` service, **1 GB persistent disk** mounted at `/opt/render/project/src/data`, daily snapshots, and masked `ARCGIS_BASEMAP_API_KEY`. The last deployed commit remains `f96509158c938372727952b1ab4a5c606ea9a4b3`.
- Read-only ArcGIS check confirmed the production credential is active, expires **October 26, 2027**, allows only `https://floateta.com` and `https://www.floateta.com`, and has static-basemap-tile privileges with zero item/admin access. Pay-as-you-go remains disabled. No credential was regenerated or changed.
- TLS validation and HTTPS requests passed for both domains, with certificates expiring January 11, 2027. The earlier visitor certificate warning was not reproducible in these checks; this does not diagnose that visitor's original cause.

### Release boundary

After authorization to publish, check the actual production credential on the live origin, one satellite map/line/land overlay, a recent gauge response and private correction delivery. Do not claim these post-deployment checks have happened yet. Native phone GPS permissions/location accuracy and on-water trip-time accuracy remain untested; GPS remaining-time is excluded from the release.

The empty legacy `data/reports.json` seed was removed from Git tracking after the user granted the required Git-metadata permission. The local file is preserved, its ignore rule is active, and the index-only deletion is staged. No commit or push occurred; no live data was touched.

Next states can use the same sources → review → validator → browser check → state allowlist process. A daily work cadence should release a reviewed subset when ready, not automatically mark every river verified after a day.

Detailed readiness: `research/MT/access-review-20261027/release-readiness.json`. Browser map and responsive checks are beside it. Preview screenshot: `/Users/home/Documents/Codex/FloatETA-Montana-release-preview-20261027.png`.
