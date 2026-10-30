# Float ETA

## Release candidate — optional gauges and honest availability

LOCAL ONLY, October 30. Gauge handling now supports no assigned station and
explicit same-river/other-river reference roles. No-data responses recover after
cache expiry. The dashboard uses a quiet availability message, retains reviewed
access maps and published guide times, and never enables a new timing model just
because discharge returns. Six existing Wyoming reference sources are explicitly
labelled; no gauge IDs or approved map coordinates were changed. Wisconsin is
not imported. Access/distance holds also withhold published trip durations until
the underlying route issue is resolved; the evidence stays in the catalog.

```sh
python3 tools/build_catalog.py --check
python3 tools/build_review_queue.py --check
python3 tools/check_release.py --output /tmp/floateta-release-readiness.json
python3 -m unittest discover -s tests
node --test tests/*.test.cjs
```

The review includes 170 rivers, 598 sections and 438 local access maps in the
existing 11 states. Four of those maps are for inspecting distance/endpoints under
review, with trip estimates withheld. Other held maps remain unavailable.
The 59 dotted path files and existing Greycliff pilot are preserved.
Validation: 121 Python checks passed (including seven development GIS checks),
45 JavaScript tests passed, 359 public pages/assets returned HTTP 200 and five
private paths returned HTTP 404. Four sampled agency feeds returned current
discharge; the sampled missing gauge returned no discharge without breaking maps.
Evidence is in `research/gauge-release-review-20261030/`.
Preview: **http://127.0.0.1:8784**. The isolated preview uses temporary test data,
not the owner's real reports or correction inbox.

Before an authorized publication, confirm Render's production basemap credential,
existing paid plan and persistent data mount; retain the existing rollback
revision. After deployment verify both HTTPS domains, gauge recovery, mobile
satellite maps/attribution, held-map behavior and a private correction submission.
No deployment, push, new state import or scheduled background job is performed by
this candidate. Production phone GPS still needs a field test.

## Current local review — four states and clearer access pins

LOCAL ONLY, October 30. The local catalog contains **170 rivers, 598 sections,
749 permanent access IDs and 438 access maps** across 11 states. Nothing in
this batch was pushed or deployed.

- Montana: **42/56** access maps; 14 remain held for landing identity, legal
  access, closures or hazard/portage questions. No unsafe exit was substituted.
- Wyoming: **124/149**, up four. Libby Creek, Newton Creek, Mummy Cave and Elk
  Fork Cliffs now have WGFD-supported **approximate access areas**, reviewed
  against imagery and the agency's launch/egress attributes. Twenty-five maps
  remain held. These new maps do not assert surveyed ramps or bank sides.
- Missouri: **111/141** maps enabled locally, with 30 held.
- Arkansas: **98/115** maps enabled locally, with 17 held.
- **59 dotted paths** and the Greycliff pilot geometry/settings are unchanged.
  No additional GPS remaining-time pilot or timing calibration was enabled.

The two new states still require explicit per-section approval fingerprints.
New agency snapshots cover MDC ramps, AGFC boating/canoe accesses, NPS access
features and the relevant Forest Service recreation records. Bindings retain
agency identity and source hashes, so changed coordinates/status trigger review
without silently moving a public pin. The research package's imagery/NHD checks
were reviewed along with independent image samples; this is desktop evidence,
not a field inspection or a guarantee of navigability.

Tyler Bend mileage/landing conflicts, Buffalo Point's carry-only closure,
Saline bridge/spillway/access questions and uncertain highway approaches remain
held. Slabtown and Red Bluff have conflicting Forest Service closure evidence;
their maps remain withheld until reconciled. Two Rivers (MO) and Grinders Ferry
(AR) were lowered to area precision after imagery review. Neither became a new
exact landing by moving its coordinate.

The three original discharge gaps remain Corbett, Laramie/Woods Landing and
Tongue/Ranchester. Their fresh adapter checks returned no discharge. Salida's
Colorado DWR adapter still returns current discharge. Upstream diversion gauges,
stage-only feeds and inaccessible exports were not substituted. Midwest gauge
limitations remain documented separately from map approval.

Map markers now use launch/finish SVG pins, readable labels, keyboard focus and
large tap targets. Approximate markers carry an **Area** badge; Greycliff's
user-confirmed field-test destination retains a distinct **Pilot** badge. Narrow
screen popups stay clear of map controls and scroll when needed.

```sh
python3 tools/fetch_agency_layer.py --source AR-agfc-access
python3 tools/check_agency_bindings.py research/four-state-map-review-20261030/AR-agfc-access-bindings.json
python3 tools/build_catalog.py --check
python3 tools/build_review_queue.py --check
```

The full source/config/binding list is in `catalog/agency_sources/index.json`.
Evidence, decisions and remaining work are in
`research/four-state-map-review-20261030/`. Preview: **http://127.0.0.1:8783**.
Validation results are recorded in that batch's `validation.json`.

## Earlier gauge and map review — October 30, 2026

LOCAL ONLY: five of the nine outstanding gauge gaps now return current discharge
through reviewed Bureau of Reclamation sources. Glendo, Gray Reef–Casper, Bighorn
at Thermopolis, Shoshone at Cody and Shoshone at Willwood show their actual source,
reading age and provisional status. Gray Reef is explicitly a dam-release value.
These sources do not enable uncalibrated float-time estimates. Arkansas at Salida,
Shoshone at Corbett, Laramie at Woods Landing and the Tongue remain unresolved;
their notes explain the limitation rather than substituting a nearby gauge.

Four additional Wyoming access maps are available locally: Bixby–Douglas,
Douglas–South Douglas, Green River Lake–Roaring Fork, and Dubois City Park–Painted
Hills. Dubois's imported agency point was roughly 10 km from the actual park;
the town's facility location replaces it as an approximate access area. That
section's old mileage is held for review. None of these new maps claims an exact
landing or adds a dotted path.

The catalog now has **221 local access-map previews** (Wyoming 116/149, Montana
42/56) and 59 reviewed dotted paths. The 14 Montana map holds remain in place.
All 107 Python and 40 JavaScript tests pass. The nine-gap live audit restored five
readings, and all 337 checked local pages/assets returned HTTP 200. The existing
Greycliff pilot files are unchanged; no deployment or push occurred.

See `research/gauge-map-review-20261030/README.md` and `validation.json` for source
evidence, remaining work and browser checks. The local review is on port 8781.

## Previous local scaling batch — October 29, 2026

The latest expansion is LOCAL ONLY. The previously published Greycliff pilot is
preserved; this batch does not deploy new states or change that live pilot.
The local catalog contains 125 rivers / 342 sections in nine states. Local map
approvals cover MT 42, ID 1, OR 13, WA 12, UT 13, AZ 6, CO 17, WY 112 and CA 1
(217 sections). Compared with the checkpoint before this batch, that is one new
river, six new sections and 17 additional access-map previews.
Wyoming has 24 rivers / 149 sections: 112 access maps are ready for local review,
37 remain withheld, and all Wyoming live timing stays disabled until calibrated.
Montana has 14 held sections. Cinnabar–Carbella and Sha-Ron–Caras Terrace
approximate maps keep distance and timing under review. First Street Gateway in
Casper now supplies approximate access areas for two Wyoming sections.
Validation results and preview limitations are recorded in
`research/expansion-20261029/validation.json`; source decisions remain in the state review folders.
Oregon now has reviewed facility locations from the Marine Board, and Boise's
Barber–Ann Morrison section has reviewed landing markers. California starts with
the Russian River Steelhead–Sunset summer float. Approximate locations stay
labelled as such. Oxbow's temporary closure and unresolved or hazardous Payette
and Boise routes remain withheld. New mileage and guide times have linked sources.
See `research/expansion-20261029/README.md` for the new evidence, validation and
next-state workflow. Historical validation files describe their earlier snapshots.

- 459 permanent access IDs live in state registries. Every source section uses
  `putInAccessId` / `takeOutAccessId`. Names can change without changing IDs.
  Aliases preserve explicit legacy cross-state references. Shared landings have
  one source record; uncertain matches remain separate until reviewed.
- `catalog/access-index.json` and `catalog/source-index.json` are generated
  handoff indexes. Per-state registries remain the authoritative access records.
- `public/catalog-index.json` is about 61 KiB. Planner, feedback and directory
  use it; the planner loads one fingerprinted river asset on selection. The full
  catalog is retained for backend/SEO compatibility, not downloaded at startup.
- `catalog/map_reviews/STATE.json` approves individual sections against hashes
  of endpoint evidence, names, trip notes, restrictions and mileage sources. Changed evidence loses
  release approval. New imports require this review; importing does not publish.
- Private location submissions accept landing, parking or entrance, endpoint,
  coordinates, visit date and firsthand flag. Server validation attaches the
  canonical existing access ID when applicable and forces community-reported
  status. No submitted pin or moderator decision edits the catalog automatically.
- Maps use catalog put-ins and take-outs. Community suggestions remain private
  evidence for review. GPS time remaining and automatic catalog mileage
  replacement remain disabled on normal maps. The separate Greycliff opt-in pilot
  still needs an actual phone field test.
- Agency point layers have allowlisted public fields, complete paginated downloads,
  immutable snapshots and feature bindings. Refreshing a layer never promotes a
  pin. A changed or missing reviewed feature appears in the private review queue.
- Homepage state links and counts are rendered from the catalog before JavaScript
  runs. State descriptions name their rivers, including newly added states.
- The gauge audit found nine remaining discharge gaps after correcting Encampment
  to active USGS 06625000. Seasonal/historical source notes appear on the affected
  pages. `tools/audit_gauges.py` repeats the check through the actual app adapter.
- State and river guides show per-stretch mileage ranges, avoiding inflated river
  coverage when short options overlap a longer float.

### Wyoming dotted paths — local review, October 29

The shared map renderer now draws reviewed paths in any state, independently of
Montana's trust-land layer. Wyoming has **46 display-only dotted paths** across
11 river records: 17 flow-directed high-resolution USGS lines and 29 generalized
USGS downstream-mainstem lines. Existing 13 Montana paths and land corridors
remain unchanged. No GPS remaining-time or automatic mileage adoption is enabled.

Source import stages candidates only. It rejects reversed/disconnected or
ambiguous high-resolution paths, endpoints more than 100 metres from the line,
segments over 1 km, and mileage disagreements above 5%. Generalized candidates
also need a separate, immutable high-resolution comparison and manual display
review. This batch sampled every 25 metres, retained only candidates within
75 metres of the finer network, and reviewed all 46 full-section overlays.
These are approximate reference lines, not surveyed landings or channel advice.

```bash
# Development GIS environment: shapely 2.0.7 and pyproj 3.6.1; not server dependencies.
python3 tools/fetch_nhd_archives.py --manifest research/routes/nhd-archives.json --output /tmp/floateta-nhd --regions 1018 1404 1704 1008 1007
python tools/import_nldi_routes.py --state WY
python tools/import_nhd_routes.py --state WY --gpkg-dir /tmp/floateta-nhd
python tools/compare_route_resolution.py --state WY
# Review candidates first; importing never changes catalog/routes/WY.json.
python3 tools/build_catalog.py
python3 tools/build_review_queue.py
```

`catalog/routes/sources/WY.json` supplies explicit river names, source snapshots,
projected CRS and archive manifest. New states use their own source configuration;
no nearest-river naming guesses or hand-drawn gap connectors are used.
The downloader verifies ZIP hashes before extraction, and the importer checks the
extracted GeoPackage hash. Smaller immutable source extracts accompany each route.
`research/routes/WY/review-queue.json` and `hr-review-queue.json` cover all 149
sections. Readiness files now include a river-path blocker and next action.
`catalog/routes/sources/MT-nhd.json` records the additional Yellowstone/Stillwater
cross-check; those newer lines did not resolve the held endpoint offsets.

Run the local review workspace (loopback only; never launched by Render):

```bash
DATA_DIR=/private/tmp/floateta-scale-preview-data python3 tools/serve_review.py --port 8778
# Open http://127.0.0.1:8778/review
```

Use a DATA_DIR with your actual private feedback to review real submissions.
This preview uses isolated test storage. Decisions append to private
`DATA_DIR/review-decisions.json`. A per-process token, local binding, host check
and origin validation protect the decision API. The production Handler exposes
neither the dashboard nor private-review API.

```bash
python3 tools/import_state_research.py /path/to/package  # dry run
python3 tools/import_state_research.py /path/to/package --apply
# Existing states additionally need --replace-existing after backup/diff review.
python3 tools/build_catalog.py
python3 tools/build_review_queue.py --packages '/path/to/states and rivers'
python3 tools/build_review_queue.py --check
python3 tools/check_access_sources.py --states WA UT AZ CO
python3 tools/build_catalog.py --check
python3 tools/audit_map_readiness.py
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.cjs
```

Source retrieval only archives evidence; it never approves access. Research
imports are normalized under `research/review-imports`, and generated readiness
records cover every current state in `research/readiness`. The original research
is retained, including blocked entries and draft-only Wyoming items. Older
implementation notes below describe their dated milestones.


A river float planner with live USGS flow, river-local daylight, optional fishing time,
community reports, and a searchable river catalog. Python standard library on
the server; HTML, CSS, and JavaScript in the browser.

## Run locally

```sh
python3 tools/build_catalog.py
python3 server.py 8000
```

Open http://localhost:8000. Python 3.9+ with IANA timezone data is required.

## Add a river (daily workflow)

1. Copy a nearby record in `catalog/rivers/` to a new file named after its unique
   URL ID, for example `catalog/rivers/new-river.json`.
2. Set `id` to `new-river`. Keep IDs stable after publishing so existing links work.
3. Fill in the name, state, gauge ID (a quoted string, including leading zeros),
   gauge name, representative river coordinates, **IANA timezone**, reference flow and speed,
   blurb, and sections. Every section needs its own ID, put-in, takeout, miles,
   difficulty, and notes. Use `multiDay: true` for designated overnight routes.
4. Verify gauge coverage, access, distance, difficulty, and calibration. Validation
   catches structural errors; it cannot certify geographic or river information.
5. Build and check:

```sh
python3 tools/build_catalog.py
python3 -m unittest discover -s tests
# Calculator and dashboard regression tests (Node 18+):
node --test tests/*.test.cjs
python3 tools/audit_map_readiness.py
```

6. Commit the source record **and** generated `public/catalog.json`. Deploy as
   usual. The calculator, search, directories, river pages, counts, and sitemap
   all pick up the record. No HTML or application code edits are needed.

### Add a state

Add the state's `id`, `name`, unique `slug`, `agency`, and HTTPS `agencyUrl` to
`catalog/settings.json`, then add its rivers and rebuild. Restart/redeploy the
server to pick up new state routing. The planner and generated state directory
navigation are automatic. About/contact/privacy pages contain editorial coverage
copy and can be updated separately when announcing new state coverage.

### Add verified access maps

Access coordinates live in `catalog/map_points/STATE.json`, separately from the
river descriptions. A state registry uses schema version 2 and records:

- an `auditedRivers` entry with an explicit `verified` or `pending` status;
- one record per put-in and take-out;
- the exact river-side coordinate, ramp or launch type, responsible agency,
  authoritative HTTPS source, verification date, and a short review note;
- when a take-out bank is verified, `riverBank` (`river-left` or `river-right`,
  always facing downstream) plus its source, review date, and note. Omit all
  bank fields when unknown; do not guess.

Maps are eligible per section when both endpoints have reviewed records.
Public display additionally requires that state in `catalog/settings.json` →
`mapRelease.states` (see `catalog/settings.json` for the local reviewed states) and no section `accessReview`.
A `verified` point is shown as a specific access facility. An `access-verified`
point uses an explicitly approximate facility marker with directions and source
links. Pending endpoints still block their section. Bank guidance is optional
and appears only when independently supported; partial bank metadata is rejected.
A fully verified river audit continues to require exact endpoints throughout.

See [the current catalog and research contract](catalog/RESEARCH_FORMAT.md) for
all required fields, unavailable timing, guide ranges, and the shared importer.
Never use guessed speed or a current gauge reading as calibration filler.

Montana currently has 38 access maps across 54 sections, including four newly
reviewed approximate maps on the Bitterroot, Dearborn, and Missouri Breaks.
Thirteen sections also have reviewed dotted river lines. Sixteen maps remain
withheld for unresolved landings, route identity, closures, or hazards. An access
map does not establish reviewed mileage or a calibrated float-time estimate;
those checks remain separate. See the dated section review queues in
`research/MT/` for decisions and outstanding work.

### Catalog validation

The build rejects malformed/duplicate IDs, filename/ID mismatches, unknown
states, invalid gauge strings or timezones, missing sections, duplicate section
IDs, and invalid coordinates, mileage or calibration values. JSON parsing safely
preserves quotes/braces in names and notes. `--check` also rejects stale generated
output; the Render build runs this check and Python tests before starting.

`public/catalog.json` is generated. Edit `catalog/`, not the generated file.
The legacy `public/rivers.js` has been replaced by the catalog source files.

## How growth is handled

- One small source file per river; independent additions are easy to review.
- One shared, generated catalog drives browser and SEO content.
- New reports reference stable river IDs, so similarly named rivers remain distinct.
- Search covers names, states and access points; results render 12 at a time.
- Only the selected river loads gauge and weather data. Requests share a short
  cache and in-flight promise. Search is debounced; outdated responses cannot
  replace the newly selected river.
- SEO parses JSON, caches by modification time, and renders route pages on demand.
- The full catalog is downloaded once. This is suitable for hundreds to low
  thousands of records; for much larger datasets, move search to a paginated API
  rather than loading the entire catalog. This is not an unlimited-scale claim.

## Planning behavior

Flow readings older than two hours, nonpositive flow, and missing flow do not
produce a current estimate. Cached requests refresh after five minutes, and
visible-page results refresh periodically. Temperature freshness is independent.
All launch/arrival/sunset times use the river's timezone. Launch times refer to
**today**, including when opening a shared link. Shared links preserve river,
craft, fishing preference and optional launch time.

Trips are rounded to five minutes; fishing adds 25 minutes per mile. Multi-day
results show total water time and minimum days at seven hours/day, without a
fabricated arrival time. Tubes and recreational SUPs do not receive an estimate
for Class III+ sections. No flow badge claims a route is safe.

Existing timezone records were initialized from the rivers' regions; verify
boundary rivers and put-in locations when reviewing or adding records.

## Reports, storage and production

Reports and contact submissions remain JSON files. Set `DATA_DIR` to durable
storage in production (the default is `./data`). Back up that directory. The
Render disk was verified on October 27, 2026: 1 GB mounted at
`/opt/render/project/src/data`, with daily snapshots visible in the dashboard.

Clear votes are advisory and no longer automatically hide hazards. Repeated
votes are deduplicated by connection address per report; this is a basic guard,
not identity verification. A reverse proxy or shared network can group users
under one address. Configure a trusted proxy/identity strategy and rate limiting
at the hosting boundary before relying on voting at scale. Report submission
moderation and robust anti-spam controls remain follow-up work. Reports still
expire after 45 days without activity. No reports never means no hazards.

## Project layout

- `catalog/rivers/*.json` — editable river records
- `catalog/settings.json` — states and craft multipliers
- `catalog/map_points/*.json` — sourced access-point audits and coordinates
- `tools/build_catalog.py` — catalog validator/builder
- `public/catalog.json` — generated shared data
- `public/planner.js` — pure date/time and float calculation functions
- `public/app.js` — data fetching, search and interface
- `public/styles.css` — shared responsive design
- `seo.py` — state pages, river pages and sitemap
- `server.py` — static pages, reports and contact API
- `tests/` — catalog/SEO and calculator regressions

## Release and hosting

Production is the existing Render `floattime-mt` service in Oregon, on the
existing `0.5c-512mb` plan. The blueprint explicitly preserves that plan.
Pushes to `main` auto-deploy. Do not push until deployment is explicitly authorized.

The Blueprint provisions a 1 GB persistent disk named `floattime-data` at
`/opt/render/project/src/data`, which is the server's default `DATA_DIR`. Back up
that directory periodically and never commit private submissions to Git.

For each rollout, run the catalog validator, Python tests, and Node calculator/UI
tests locally. After publishing, check health, the homepage, directory, river
links, reports, contact page, and mobile layout on `floateta.com`.

The home page deliberately starts with no state or river selected. A `?river=`
link selects that river. At most four popular rivers appear for the chosen state;
the separate directory searches the catalog and displays 12 results at a time.
The original gauges, seven-day graph, fishing toggle, and stretch cards remain.

## Local state integration (2026-10-26)

Washington final4, Utah v1 and Arizona v1.4 are staged locally. The catalog has
90 rivers and 162 sections across six states. Utah and Arizona live timing
models are unavailable while calibration is reviewed; supported published guide
times remain visible. Sixteen Washington timing models are also withheld based
on the research recommendations. The existing six Washington modeled records
remain compatible; this is not a new certification of their calibration.

Research/evidence snapshots live in `research/WA`, `research/UT`, `research/AZ`.
These images and raw files are authoring evidence and are not served by the app.
The machine-readable review log is `research/integration-review-20261026.json`.
Do not rerun a legacy package validator against these new fields; use the current
shared builder and tests. New import drafts should follow `catalog/RESEARCH_FORMAT.md`.

## Private corrections and missing-float requests

Every calculator section and river-page section has a correction link that
preselects its stable river/section IDs. `/feedback.html?type=float-request`
accepts proposed floats in any state, including states outside current coverage.
Names, email and source links are optional; descriptions and request endpoints
are required. New hazards still belong in the public river-report feed.

`POST /api/feedback` validates correction IDs against the current catalog and
stores canonical route names, preventing a submitted name from changing the
reported section. Suggestions are saved privately in `DATA_DIR/feedback.json`
with pending status and a reference ID. They do not alter the catalog or public
reports. There is no public listing API and no automatic email notification.
Storage failure and full queues return errors rather than discarding old entries.

Review from the project folder (use the hosting data directory when appropriate):

```bash
python3 tools/review_feedback.py
python3 tools/review_feedback.py --id SUBMISSION_ID
```

The review command is read-only. Research each correction/request, then edit the
source catalog using the normal build/review process. Keep name/email out of any
public change. Do not publish or fetch submitted supporting links automatically.
Raw feedback is ignored by Git and is covered by the existing persistent data
directory on Render. Back up that directory alongside reports/contact data.

## Asset caching

The Python server fingerprints local CSS and JavaScript references when it serves
HTML (including generated river/state guides). Changing a file changes its URL
automatically; no manual version bump is needed. Only a matching content hash
receives a one-year immutable cache policy. An HTML ETag also changes when one of
its referenced assets changes. Serve previews through `server.py`, not a generic
static server, to exercise the same behavior.


### Satellite map configuration

Maps use authenticated ArcGIS Location Platform World Imagery tiles (256px) and static imagery-label tiles (512px). No map requests are made until a section map is opened. Access points retain their catalog evidence; the local route registry below narrows eligible Montana DNRC overlays.

For local development, create `map-config.local.json` in the project root with `{"arcgisApiKey":"YOUR_PUBLIC_BASEMAP_KEY"}`. This file is ignored by Git and is outside the served `public/` directory. For deployment, set `ARCGIS_BASEMAP_API_KEY` in the hosting environment; it takes precedence. `/api/map-config` deliberately exposes this browser-safe key and the reviewed route index for states enabled in `mapRelease`, with `Cache-Control: no-store`. Never supply a client secret, account password, or private-app credential.

Use a public-application credential with no item or admin privileges, limited to basemap services, with explicit HTTP referrers and an expiration date. The current local credential is restricted to `http://127.0.0.1:8777` and expires January 25, 2027. A separate production credential for `https://floateta.com` and `https://www.floateta.com` was generated on October 27, 2026, expires October 26, 2027, and is staged in Render with **Save only**. It has not been deployed or exercised on the live site. Do not ship the local configuration file. Keep pay-as-you-go disabled unless the owner explicitly enables it. Browser keys are visible to visitors; referrers are an abuse deterrent, not a secret or guaranteed spending cap.

When no key is configured, maps show an unavailable message; the app does not silently use anonymous imagery. Test a map, zoom, access popup, Montana overlay and denied/missing-key behavior after changing credentials. Provider credits must stay visible. Esri service references: https://developers.arcgis.com/documentation/mapping-and-location-services/service-endpoints/ and https://developers.arcgis.com/documentation/mapping-and-location-services/mapping/basemaps/arcgis-styles-tiles/ .


### Local Blackfoot time-remaining pilot

Local configuration can additionally contain `"routePilotEnabled":true`. This experiment is now **disabled** in the ignored development config, at the owner’s request to defer live ETA. The prototype remains available for later work on Blackfoot `johnsrud-weigh-station`. An environment-provided production key never enables the pilot. No production deployment was performed.

`catalog/route_pilots/index.json` lists the approved local experiment and its static asset. `tools/build_route_pilot.py` builds it from archived Montana FWP centerline and DNRC polygons in `research/MT/route-pilot-20261027/`. It uses development-only `shapely==2.0.7` and `pyproj==3.6.1`; the production server needs neither. Run `python tools/build_route_pilot.py` in that development environment (`--refresh-land` refreshes DNRC evidence). The builder checks stream identity, continuity assumptions, downstream ordering, endpoint offsets and mileage agreement. Adding routes requires source review; this is not an automatic nationwide routing service.

The 10.73-mile approximate centerline agrees with the catalog's 10.7 miles. Pins are 38–57 metres from that line. The clipped land layer shows only portions within 150 metres, reducing 13 bounding-box candidates to 8 tracts. Clipped edges are display boundaries, not legal parcel boundaries. Nearby ownership does not prove a usable or unrestricted landing. Other maps show access markers without land shading until a reviewed corridor is available.

Time remaining uses along-river distance and the existing provisional flow/craft model; future fishing adds 25 minutes per remaining mile. It is not observed GPS speed. Fixes older than 30 seconds, accuracy worse than 50 metres, positions more than 75 metres from the line, ambiguous bends, and missing/stale gauge readings withhold estimates. Near the endpoint the UI asks the user to confirm the landing, rather than declaring arrival. Coordinates stay in browser memory and are cleared on map close; imagery requests necessarily reveal the viewed map area to Esri.

To revisit the archived experiment, in a separate local experiment, turn `mapRelease.reviewedRoutes` off, `routeMapsEnabled` off and `routePilotEnabled` on in the ignored local config, then open the local Blackfoot Johnsrud-to-Weigh-Station map and choose **Try a sample position → Start demo**. Sample mode is explicitly labelled and uses 1,200 cfs. It can simulate bad/old GPS or off-river positions without requesting location permission. Real GPS, actual timing accuracy and mobile permission behavior still require a phone field test on a separately authorized HTTPS preview. Localhost on this computer is not accessible as localhost on a phone. Do not enable this pilot publicly based only on simulated tests.

Regression checks: `node --test tests/*.test.cjs`, `python3 -m unittest discover -s tests -p 'test_*.py'`, `python3 tools/build_catalog.py --check`.


### Reusable river routes (local preview, October 27)

Current local flags are `routeMapsEnabled: true`, `routePilotEnabled: false`. `mapRelease.reviewedRoutes` enables reviewed display paths in the states listed in catalog settings. A production key does not enable the old Blackfoot GPS experiment. The later Greycliff pilot is separately allowlisted; new state work remains local.

The registry is independent of the map provider and browser layout:

- `catalog/routes/index.json` lists state registries; `catalog/routes/MT.json` lists section records in `catalog/routes/MT/`.
- Each record includes its source snapshot/checksum, named endpoint coordinates, downstream measures, geometry, calculated checks, review status, and separate `display`, `landOverlay`, `distanceEstimate`, `remainingTime` switches. The last two are reserved and must remain false until their separate rollout is implemented.
- `tools/route_catalog.py` is the standard-library validator/exporter, integrated into the existing catalog build and `--check`. Only reviewed, enabled records export to `public/routes/`. Withdrawn assets are removed on rebuild. Source or endpoint changes require review; passing automated checks alone does not change status.
- `public/river-route.js` contains shared geometry functions. `public/route-progress.js` is the deferred GPS experiment. These do not depend on Google or Esri for river-distance measurement.

The current Montana release has 34 eligible maps out of 54 sections (28 specific access maps and 6 approximate facility maps), 13 reviewed river paths and 13 validated 150-metre land corridors. Twenty section maps remain withheld. Thirteen sections now have `accessReview` holds, and Gallatin Valley remains timing-unavailable. Missing land shading does not mean there is no federal, county or other public land. Review status is based on desktop sources, not field verification.

Commands (from project root):

```bash
# Development GIS environment only, with shapely==2.0.7 and pyproj==3.6.1:
python tools/import_river_routes.py --state MT
# --refresh obtains fresh source snapshots; never auto-approves or changes reviewed records.
python tools/build_route_land.py --state MT

# No GIS packages or network needed for publication checks:
python3 tools/build_catalog.py
python3 tools/build_catalog.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.cjs
```

The importer only stages `research/routes/MT/candidates.json` and `review-queue.json`. Review the relevant source, named access, geometry and discrepancies before copying a candidate to the state registry with `status: reviewed`, a dated review note, and `display: true`. Unresolved candidates stay private with all switches false. The first importer supports measured ArcGIS river lines; another state may need a different source adapter. Do not guess stream identity or join disconnected source paths to force a match.

Raw route snapshots are immutable and checksummed. Land snapshots and clipped outputs are also versioned by content; refreshes cannot overwrite older approved evidence. `land-review-queue.json` records data failures. The land builder refuses invalid polygons and truncated responses rather than silently repairing or treating them as empty results. A failed route/land request does not remove the ordinary access markers. Approximate agency lines may omit current side channels, and checked-on dates describe the review, not the age of the underlying survey.

Current exception priority: Lower Madison Blacks Ford → Greycliff measures about 4.37 miles on this source line versus 9 in the catalog, with endpoint offsets of about 150/308 m. That is a **research flag**, not an authorized distance correction or proof the current pin is wrong. Resolve its endpoint identity and agency mileage before enabling its route. Gallatin Canyon and Valley still await eligible access coordinates, so this batch does not invent maps for them.


### Montana-first release workflow

`catalog/settings.json` contains the map rollout allowlist. The builder emits
`mapReleased` for eligible sections in those states. Both calculator buttons,
direct map links and river guide links honor it. Other states remain in the
river catalog; adding a state to the rollout does not automatically approve its
pending points or routes. The production map config returns reviewed routes
only for the allowed states. GPS remaining-time and automatic distance adoption
remain off independently.

For the next state: research named usable endpoints, retain candidate coordinates
in research, add sourced exact or explicitly approximate access records, resolve
hazards and mileage conflicts, build/validate, browser-check the eligible maps,
then add the state to the allowlist. A daily review cadence is useful; it does not
require claiming a whole state is verified in one day. Unresolved entries stay
withheld while the reviewed subset can launch.

Storage reads fail with HTTP 503 on corrupt files; failed writes never return
success. Private contacts and suggestions stay in the persistent data directory.
The empty legacy `data/reports.json` seed has been removed from Git tracking
while preserving the local file. The index-only deletion is staged; no commit
or push has occurred. All runtime submission files are ignored.

Final production checks after an authorized deployment: HTTPS on both domains;
`/api/health`; a Montana satellite map with credits, markers and reviewed line;
an unreleased-state link stays closed; a correction reaches the private queue;
and a current USGS reading. Verify location permission on an actual phone before
advertising phone GPS as tested. GPS time remaining is not part of this release.

## Greycliff opt-in field test (2026-10-29)

Only `?fieldtest=greycliff&river=madison-lower&section=blacks-ford-greycliff&map=1`
enables the checked Blacks Ford–Greycliff pilot. Ordinary visitors and other sections
retain existing behavior. `catalog/field_pilots.json` allowlists the exact public
asset SHA-256; the server and browser both check it. Disable its `enabled` flag and
redeploy to withdraw the pilot. Never promote other route candidates by enabling
this registry wholesale.

The destination is the owner-supplied public ramp at 45.704500, -111.516139,
corroborated against imagery, **not agency verified**. The start remains an approximate
facility area. USGS NHDPlus HR supplies eight connected primary downstream reaches,
clipped at projections of those endpoints; no straight connector is invented.
The 4.5686-mile mapped line is used only for this field test. The normal calculator
retains the rounded 4-mile agency-guide distance. Side channels and actual travel
speed remain uncertain. The pilot requires fresh accurate GPS, a position near the
line, and fresh flow; it withholds estimates otherwise. GPS stays in the browser.

Reproduce source geometry with `python tools/check_greycliff_geometry.py`
(development-only Shapely 2.0.7 and pyproj 3.6.1). Run
`python -m unittest discover -s tests` and `node --test tests/*.test.cjs`.
Evidence and the imagery review are recorded in
`research/MT/greycliff-pilot-20261029/route-checks.json`.
Phone GPS still needs the user's real field test; simulated checks are not field validation.
