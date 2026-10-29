# Float ETA

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
`mapRelease.states` (currently only `MT`) and no section `accessReview`.
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

Current local flags are `routeMapsEnabled: true`, `routePilotEnabled: false`. The reviewed route index is also enabled for a future production release by `mapRelease: {"states":["MT"],"reviewedRoutes":true}` in catalog settings. A production key does not enable the local GPS experiment. No deployment was made.

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
