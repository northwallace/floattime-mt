# Float ETA catalog and research contract (local preview, 2026-10-30)

This contract matches the current local builder. Deployment is a separate step.
Source files are in `catalog/`; `public/catalog.json` is generated. Run:

```bash
python3 tools/build_catalog.py
python3 tools/build_catalog.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.cjs
```

## New rivers without calibrated timing

The app can show access, gauge readings, daylight and guide times without a live
timing model. Use these fields; never insert dummy 3 mph or today's discharge:

```json
{
  "refFlowCfs": null,
  "refSpeedMph": null,
  "timing": {
    "mode": "unavailable",
    "note": "A reviewed speed/flow calibration has not been established."
  }
}
```

These are fields within an otherwise complete existing river record. Add name,
ID, state, gauge, representative coordinates, timezone, blurb, and sections using
the examples. Unknown bank or absent timing must not become invented facts.

For a newly reviewed flow model use `timing.mode: "model"` and provide `note`,
`sourceName`, HTTPS `sourceUrl`, and ISO `checkedOn`, plus the paired positive
`refFlowCfs` and `refSpeedMph`. The note must explain the derivation and craft/stop
assumptions. Older models without an explicit timing object remain supported;
that compatibility is not a fresh validation of their calibration.

## Published guide times

Optional `guideTimes` belongs to the specific section, not the river. Example:

```json
{
  "guideTimes": [{
    "min": 3,
    "max": 4,
    "unit": "days",
    "conditions": "BLM recommends a minimum planning allowance for this 68-mile trip. Allow longer as needed; this is an itinerary, not hours afloat.",
    "sourceName": "BLM Labyrinth Canyon trip planning",
    "sourceUrl": "https://www.blm.gov/visit/labyrinth-canyon-river",
    "checkedOn": "2026-10-26"
  }]
}
```

Units are `hours` or `days`. Numeric values must be positive and finite, min <= max.
For an explicitly open-ended source such as “6+ hours”, use `min: 6` and
`max: null`. The site displays “6 hours or more”; never invent an upper bound.
The `max` field must still be present. Keep the source's uncertainty in
`conditions`; a general phrase such as “full day” alone does not justify
assigning a numeric duration.
Preserve flow-band conditions, craft, source age and whether stops are known.
The app displays guide guidance separately and never adjusts it using craft,
fishing, launch time or today's flow. Minimum planning allowances must be
described as minimums, not promised maximum travel times.

## Access registries

Use `catalog/map_points/STATE.json`, version 2, with `state`, `auditedRivers` and
`points`. Access types and operators are descriptive text, not enumerations.
Registries use names as object keys, with permanent `acc-...` IDs on every point.
Sections reference those IDs; endpoint labels must match the registry name or a
documented alias. Reuse existing IDs from `catalog/access-index.json`. Do not
create a new landing identity merely because a research package renames it.

- `pending`: `status` and explanatory `note`; no coordinates. A map stays hidden
  if either endpoint is pending. Confirmed closures, unresolved permissions,
  competing sites and critical take-outs without a dependable location stay
  pending until reviewed.
- `verified`: existing exact facility fields: numeric `lat`/`lon`, `accessType`,
  `operator`, `sourceName`, HTTPS `sourceUrl`, ISO `verifiedOn`, and `note`.
  Include optional `directions` as non-empty, source-backed approach text when
  available. These directions appear in map popups and river guides and form
  part of the access review fingerprint; changing them requires map review.
- `access-verified`: boating access documented but landing uncertain. Use
  `areaCenter: {lat, lon, feature}`, `directions`, `sourceName`, HTTPS `sourceUrl`,
  HTTPS `coordinateSourceUrl`, ISO `verifiedOn`, and `note`. `accessType` and
  `operator` may be provided when documented. No top-level lat/lon, bank fields,
  invented radius, or claimed accuracy. The marker is explicitly approximate.

Bank metadata is optional for exact facilities. When provided, the whole group
is required: `riverBank` (`river-left` or `river-right`, facing downstream),
`bankVerifiedOn`, `bankSourceName`, `bankSourceUrl`, `bankNote`. Approximate
locations cannot claim a verified bank. No direction is inferred from the
nearest channel alone.

River audit status remains `verified` or `pending`. A pending river may now
contain independently usable maps: both endpoint records must be verified or
access-verified. A river marked verified must still have exact reviewed
endpoints for every section. Audit status is not a safety or current-opening
certification.

Never add generated fields (`mapPilot`, `mapPrecision`, `mapPendingReason`,
`putInCoords`, `takeOutCoords`, `putInAccess`, `takeOutAccess`) to source sections.
The builder derives them. Exact and approximate directions are displayed
differently; an approximate facility does not get an exact coordinate-based
driving instruction.

## Importing current research packages

The shared importer supports the existing Washington/Utah/Arizona layouts and
one state-entry file or `catalog/state.json`. It never executes package scripts.

```bash
python3 tools/import_state_research.py /path/to/package
python3 tools/import_state_research.py /path/to/package --apply
python3 tools/build_catalog.py
```

Default is dry-run. `--apply` replaces that state's incoming records locally,
after validating a temporary combined catalog. Preserve a backup/diff before
reimporting a reviewed state; curated local edits may otherwise be replaced.
Cross-state river-ID collisions fail. Raw research is retained under
`research/STATE/`, while only reviewed catalog fields reach the app.

Legacy `publish-with-range` and `defer` timing recommendations never authorize
a live speed model. Missing timing assessments also disable the model unless
the incoming record explicitly supplies a complete supported model record.
Do not auto-promote research access grades. Check identity, location sources,
restrictions and critical downstream hazards before promotion.

## Research handoff

Keep reusable agency layers, source snapshots, retrieval dates, guide table
cells, actual trip observations, restrictions, route geometry, candidate
coordinates, conflicting evidence and next actions in research files. Count
guide table rows separately from independent trips. Mark source-fetch failure
separately from access permission or closure. Validate the reconstructed package
and evidence manifest; exclude Python caches and OS metadata.

The current review log is `research/integration-review-20261026.json`. It records
which approximate access records were accepted, which remain pending, and which
guide times/corrections were added during the local integration.

## Shared endpoints and agency notices (2026-10-27)

A section can explicitly reference an existing registry point across states using
`takeOutPoint: {"state":"UT", "name":"Split Mountain Boat Ramp"}`
(or `putInPoint`). Unknown references fail validation; a referenced pending point
still blocks the map. Never infer a match from a similar name. Keep display labels
consistent with the referenced facility. Updates to the original registry carry
through to every section using it.

Optional section `notices` is a list of objects with nonempty `title`, `text`,
`sourceName`, HTTPS `sourceUrl`, and ISO `checkedOn`. These are shown on both
the calculator and river guide. Preserve source dates; an old advisory is not
a real-time closure determination. Research-only restrictions do not display
until reviewed and deliberately added here.

## Mileage audit
Run `python3 tools/audit_map_readiness.py` after a catalog build. A section with
impossible endpoint-to-endpoint mileage must carry a nonempty `distanceReview`
explanation while it is investigated. This disables calculator and SEO time
estimates and marks its map for review. It does not certify the coordinates.
Resolve the actual mileage or endpoint mismatch from source evidence before
removing the flag. Never replace river mileage with straight-line mileage.

The catalog build now enforces this sanity check as well, so skipping the separate
audit command cannot publish a newly impossible mapped distance without a review
flag. A plausible distance still needs research; passing is not verification.

### Sourced river-mile differences

For a reviewed agency river-mile dataset, a section may include `distanceEvidence`.
See `catalog/rivers/blackfoot.json` for a complete example. Required fields:

- `method`: `agency-mile-markers` for this coordinate-bound method.
- `sourceName`, HTTPS `sourceUrl`, `checkedOn` (`YYYY-MM-DD`), `streamId`, `note`.
- `putIn` and `takeOut`: objects with `name` matching the section label; `lat` and
  `lon` matching the reviewed facility coordinate; `riverMile`; integer `markerId`;
  and `offsetMeters` between that coordinate and the selected marker (0–200).

Use the same agency stream identifier for both endpoints. Confirm the river and
downstream direction using the agency guide; do not select a closer tributary or
silently average conflicting sources. `miles` must equal upstream minus downstream
river mile, rounded to one decimal. The UI labels this approximate and links the
source. A changed endpoint or mileage must be re-reviewed before the build passes.
This method is appropriate only where river measures decrease downstream.

Two published-guide methods are also supported:

- `published-guide-miles`: use the same common source fields above, plus
  `measureDirection` (`increases-downstream` or `decreases-downstream`). Each
  endpoint has `name`, `riverMile` and `sourceLocation` (page/table/row). The
  difference must match `section.miles`. See `rivers/john-day.json` and
  `rivers/missouri-breaks.json`. These are guide measurements, not exact GPS fixes.
- `published-trip-length`: use the common fields above, a positive `miles` equal
  to `section.miles`, and named `putIn`/`takeOut` objects with `sourceLocation`.
  Use this when the source gives a whole-trip distance instead of mile markers.
  Do not invent mile zero and an endpoint marker. See
  `rivers/russian-river-forestville.json`. For summed contiguous guide lengths,
  identify the common join and each source page, as in `rivers/payette-sf.json`.

Neither method enables a live timing model. Keep new rivers at
`timing.mode: unavailable`, `refFlowCfs: null`, `refSpeedMph: null` until there is
separately reviewed calibration. Published `guideTimes` retain the source's
craft, season and conditions; never turn them into an assumed drift speed.

Keep raw responses and exact query URLs in `research/STATE/`, outside the public
catalog. The Montana example is `research/MT/mileage-20261027/fwp-mile-markers.json`.
Do not automatically promote pending coordinates from proximity to a river-mile
marker: measuring distance does not establish a legal access point or exact ramp.

### Reusable agency point sources

The new reference sources are `agency_sources/OR-boating-access.json` and
`agency_sources/ID-boise-access.json`, registered in `agency_sources/index.json`.
Use the agency's own page or web map to establish which service it publishes.
Record the exact layer URL, public field allowlist, public-only filter and stable
feature-ID field. A GlobalID is preferable to a renumberable OBJECTID. Permanent
Float ETA access IDs remain independent of both.

```bash
python3 tools/fetch_agency_layer.py --source OR-boating-access
python3 tools/check_agency_bindings.py research/expansion-20261029/OR-agency-bindings.json
python3 tools/build_catalog.py
python3 tools/build_review_queue.py
python3 tools/build_catalog.py --check
python3 tools/build_review_queue.py --check
```

The downloader refuses truncated, incomplete, duplicate or changing inventories
and invalid coordinates. It saves immutable hashed snapshots under
`research/agency-sources/<source>/`; it does not touch public pins. The binding
checker compares reviewed features with the newest snapshot and returns a failing
exit code for changes, missing features or unfinished review. The review inventory
includes those findings. Refreshes are explicit commands, not a scheduled service.

Research bindings record the canonical `accessId`, snapshot path/hash, source
feature ID/hash, decision, checked date and review note. A downloaded point can be
a park centroid, parking lot, emergency-only site or obsolete access. Confirm the
correct river, facility, permission and restrictions before accepting it. Check
imagery for placement; imagery alone cannot establish legal access. Use
`access-verified` with `areaCenter` for an approximate facility, and `verified`
only for a documented, checked landing. Preserve pending alternatives in
`research/`, never in active `lat`/`lon` fields.

Run the binding check before release and inspect the private queue. A stale or
changed source is a review task; a successful download is not publication approval.

For an access map that has been researched and visually reviewed, obtain its
current evidence fingerprint with the read-only helper:

```bash
python3 tools/map_review.py --river american-river-lower --section lower-sunrise-river-bend
```

`--state CA` lists a whole state. This command uses the same normalized access
records as the catalog builder; hashing raw `map_points` JSON can give a different
signature. It prints current status and fingerprints without granting approval or
changing files. Add the fingerprint to a reviewed map record only after recording
the source evidence, reviewer, date and decision. Pending locations stay pending
regardless of whether a fingerprint can be calculated.


## Optional river-route package (independent of access verification)

Continue delivering river records and access points in the existing format. River lines are an additional layer, not a requirement for adding a river or proof that access is legal. Do not add a line by connecting put-in and take-out with a straight segment, choosing the widest visible channel, or joining unmatched tributaries.

The working example is `catalog/routes/MT/blackfoot--johnsrud-weigh-station.json`; the authoritative validator is `tools/route_catalog.py`, run by `python3 tools/build_catalog.py --check`. Keep a source URL, agency stream identifier, raw dated source snapshot and SHA-256, the geometry in WGS84 `[longitude, latitude]`, exact copies of the catalog endpoint names/coordinates and mileage, and evidence establishing downstream direction. `review.checkedOn` is the date we assessed the record; do not call it the imagery or survey date.

New flow-directed imports record perpendicular source offsets in
`direction.putInOffsetMeters` / `takeOutOffsetMeters`, and positions along their
first/last source features in `putInSourceStationMeters` /
`takeOutSourceStationMeters`. Earlier imports used the offset-named fields for
along-line stations; their authoritative perpendicular distances are in
`checks.metrics.endpointOffsetsMeters`. The validator supports those existing
records and uses explicit station fields for new single-feature direction checks.
Sub-millimetre duplicate source-join vertices are discarded; larger source gaps
and ambiguous branches still require review.

Research deliveries should use `status: candidate` and all four feature flags false: `display`, `landOverlay`, `distanceEstimate`, `remainingTime`. Store candidate geometry and unresolved alternatives under `research/routes/<STATE>/`, outside `public/`. The importer stages candidates there and writes a per-section review queue. A route is not verified simply because a validator passes. Explain endpoint offsets, alternative channels, source discontinuities and mileage disagreements; do not alter a catalog value to make a test pass.

For measured ArcGIS sources, configure a state source record like `catalog/routes/sources/MT.json` (exact layer URL, stream ID field and IDs, CRS and measure direction). Other formats need an explicit adapter with equivalent checks. State registry entries live in `catalog/routes/index.json` → `<STATE>.json` → per-section JSON. New states use the same display format and validator; map JavaScript does not need a new hardcoded river branch.

Only a reviewed record may enable route display. Land shading requires separate sourced polygon data and a corridor tied to the route geometry checksum. Never infer public landing rights from ownership or proximity. Keep `distanceEstimate` and `remainingTime` false: automatically replacing published miles and live GPS ETA are deferred. The original Blackfoot GPS experiment remains archived separately.

### River-course overviews when exact landing connections are uncertain

Precision is the first choice; an approximate area is the fallback. Preserve a
reviewed exact landing when its evidence still supports it. When public boating
access is documented but the precise landing is uncertain, show a sourced
`access-verified` area with directions and a “Help pinpoint” link rather than
hiding the access. Do not invent a likely landing on an unconfirmed property.
User coordinates are evidence for review, never an automatic public pin change.
Assess river-course geometry independently of access-point precision.

The Hell’s Canyon–Silver Star review in
`research/jefferson-course-refinement-20261106/decisions.json` keeps both
approximate access areas and the 4.5-mile planning distance, while displaying a
partial source course that omits the launch/diversion approach. Its six source
forks were compared with imagery; a generalized line through the active river
corridor does not establish a navigable passage around bars. Parsons–Parrot,
Kountz–Mayflower and Mayflower–Cardwell retain access maps while their course
geometry stays under review. Do not hide a documented access area solely because
the route is held, or promote its pin because a river line is available.

Agency-published water-trail lines can also support display-only overviews.
Register the exact layer URL, CRS and field mapping in
`catalog/routes/agency_sources/<STATE>-<source>.json`; the Minnesota DNR example
is `MN-dnr-water-trails.json`. Archive the complete WGS84 ArcGIS response and
bind both the response and registration with SHA-256. With direction method
`agency-published-water-trail`, list each source feature ID, path index and
orientation explicitly, then record start/end segment fractions for trimming.
`tools/agency_courses.py` reconstructs the displayed line from those exact
vertices; gaps, invented connectors, changed vertices, other trails and
reversed trims fail validation. Feature IDs identify parts within that immutable
snapshot, not permanent access identities.

Bind the section's published downstream river-mile evidence separately and
visually review the entire course against imagery. A mechanically valid source
line is still a research candidate until reviewed. Kettle's Musclewood–Highway
23 example keeps its published 16.5-mile planning distance and approximate
access areas; the DNR line is an overview with unmapped landing connections.
It does not enable land-access shading, calculator mileage adoption or GPS ETA.

Rum River's `research/rum-river-20261106/decisions.json` demonstrates mixed
precision and conflicting guide editions. Its North County Park GPS point
matches the visible carry-in approach and retains a sourced downstream-left
bank; four other points remain approximate areas. Do not downgrade the checked
landing merely because the other endpoint or course is approximate. The 2026
DNR PDF distinguishes the Cambridge carry-in (RM 42.6) from the watercraft
campsite (RM 41.0), while the webpage's longer trip uses the campsite mile.
Resolve endpoint identity before choosing mileage; record the discrepancy
instead of mixing river miles across sources. The matching Martins–North
County Park trip retains its published 3.5–5 hour paddling range, with a
reference-only gauge and no flow-to-speed calibration. Do not transfer that
range to adjacent sections or treat general paddling speeds as trip evidence.

Stage the same candidate format for another trip without changing the catalog:

```sh
python3 tools/stage_agency_course.py \
  --river kettle-river-mn --section highway-48-maple-island \
  --adapter MN-dnr-water-trails \
  --evidence research/kettle-course-20261106/sources/dnr-kettle-water-trail.json \
  --parts research/lower-kettle-20261106/source-parts.json \
  --output research/lower-kettle-20261106/new-review-candidate.json
```

The parts file is an array, for example
`[{"featureId":"38","pathIndex":0,"reverse":false}]`. Source part order and
orientation are explicit research inputs. The tool suggests trims near the
existing access coordinates or accepts an explicit `--clip` JSON file. It never
moves access pins, overwrites an existing file, writes into `catalog`/`public`,
or grants approval. Review any suggested trim at a braid, diversion, bridge or
riverbank before accepting it. All staged feature flags remain false.

The normal 1,000 m segment check can flag a genuine straight reach in a sparse
agency source. Do not add interpolated vertices to hide that warning. For a
source-reconstructed `agency-published-water-trail` overview only, an original
segment between 1,000 and 2,000 m may receive explicit `sourceSegmentReview`.
Each entry names the zero-based displayed `segment`, an imagery verdict in
`note`, and saved `imageryEvidence` entries with research `file` and `sha256`.
Review the complete segment against imagery; account for every long segment
exactly once. Bind the review into `overviewReview.signature` and explain the
accepted geometry issue. Duplicate vertices, disconnected source parts, changed
source geometry and segments beyond 2,000 m still fail. The renderer receives
only the validated segment indices; the exception is unavailable for navigation,
GPS time remaining, land corridors or calculator distance adoption. Hokah to
Highway 26 on the Root River is the first example. The presence of a straight
line in an agency file alone is insufficient evidence to approve it.

An agency water-trail map can establish an access area even when a separate
boat-ramp GIS inventory has no matching feature. Preserve the map's coordinate
and publication date; record where the agency currently links that map. Check
the approach separately when needed. For example, Lemanski Road uses the DNR
water-trail coordinate as `areaCenter` and road record 11567 from the DNR
motorized-access inventory as supporting approach evidence. An open road does
not establish an exact launch, a trailer ramp, or a passable side channel.
Road IDs identify roads, not landing identities: keep them in the source
evidence and retain a separate stable access ID. The reviewed example and
source snapshots are in `research/lemanski-access-20261106/`.

Keep the best sourced access position. An agency facility coordinate is not
automatically a water-edge ramp pin: Silver Star now uses `areaCenter` after
imagery review showed that its unchanged agency coordinate sits back from the
channel. Visitors can suggest a more precise landing through the endpoint-specific
“Help pinpoint” link. Suggestions remain private until reviewed.

A separate `scope: river-course-overview` can show reviewed river geometry while
leaving landing connections unmapped. The local example is
`catalog/routes/MT/jefferson-upper--silver-star-parsons.json`. It intentionally
stops before the Waterloo diversion approach. Its mapped length is not the full
trip distance. Keep the published section mileage and its distance evidence.

Deliver research candidates with all feature flags false. With a configured
high-resolution USGS source, `tools/import_nhd_routes.py --state WI
--overview-candidates` can also stage candidates near approximate access areas.
Use the same verified regional archives and `--gpkg-dir` as the ordinary importer
when the online service is unavailable. This option still rejects ambiguous
branches, gaps and reversed flow; it does not clear a `routeReview` or approve
any candidate. For approximate facilities only, staging can inspect river lines
up to 1 km away, matching the overview validator's outer rejection limit.
Offsets over 100 m remain explicit check issues that need a documented review;
all staged feature flags stay false. Ordinary routes retain their 100 m limit.
Do not snap an access marker onto a channel to pass the checks.

An overview review must document both unmapped access connections, any omitted
approach, the source limitations, and the exact outstanding section `routeReview`.
The validator binds the decision to geometry, source evidence, endpoint snapshots
and planning mileage with `overviewReview.signature`. Explicitly explain any
accepted endpoint-offset or mileage-difference check. Other geometry failures
remain blockers; offsets over 1 km or length differences over 20% cannot be
approved by an ordinary overview review. These are outer rejection limits, not accuracy targets.
Inspect channel alternatives and known barriers before approval. A continuous
line must never imply safe passage through an unresolved dam or portage.

Overviews enable display only. They cannot enable land shading, calculator
distance adoption or GPS time remaining. Ordinary route records retain their
existing exact-access, 100 m endpoint and 5% mileage checks. Regenerate and check
the catalog with `python3 tools/build_catalog.py --check`; the authoritative
review rules are in `tools/route_catalog.py`.

When the planning distance itself is disputed, keep a nonempty section
`distanceReview` and withhold estimates. A separately reviewed orientation line
may use `distanceDiscrepancyReview`, as in
the held-distance record in `tests/fixtures/distance-review-overview.json`.
The Beaverhead distance has since been corrected from FWP mile markers.
This exception requires an
ordered high-resolution USGS downstream source chain, reconstruction from its
original vertices (only endpoint clipping is allowed), saved imagery files with
SHA-256 hashes, an explanation, and the exact current `planningDistanceReview`
text. Bind this evidence into `overviewReview.signature`. Endpoint, gap, flow
direction, source, access and barrier checks still apply. The client labels the
planning distance as under review and rejects a mismatch with the section.
Display is the only allowed feature; this does not adopt the mapped length as
the trip distance or enable timing. Changing the planning-distance hold requires
a new course review. Do not add this exception merely to make a candidate pass.


## Published river-mile guides and facility coordinates (October 27 follow-up)

A general agency site point is not automatically a ramp coordinate. Check the GIS layer's purpose and compare the point with a ramp-specific plan, published access survey, or landing imagery. Where boat access is documented but the coordinate locates the facility generally, use `access-verified` plus `areaCenter`, directions, and a coordinate source URL. Do not promote an inland facility centroid by snapping it onto the nearest river line. Black’s Ford and Greycliff are current examples of approximate facility records; Smith River shows how two documented facilities can support a useful approximate map without claiming exact landings.

Named river-mile markers in an agency or firsthand access guide can establish approximate trip distance independently of GPS pins. Use `distanceEvidence.method: published-guide-miles`, the source name/URL/check date, stream identity, and an explicit `measureDirection` (`increases-downstream` or `decreases-downstream`). Each `putIn` and `takeOut` contains `name` exactly matching the section, `riverMile`, and `sourceLocation` identifying the printed page/table/heading. The validator requires the downstream difference, rounded to one decimal place, to equal `miles`. Describe source rounding and channel uncertainty in `note`. Do not invent GIS marker IDs, offsets or survey coordinates for a printed guide. Current examples: Lower Madison Black’s Ford–Greycliff; Missouri Breaks; Smith; North Fork Flathead.

Published landing surveys with photographs, explicit coordinates, and access descriptions are useful primary evidence even when the publisher is a river partnership rather than a state GIS department. Attribute that publisher honestly; do not relabel its work as agency or field verification by Float ETA. The April 2026 Flathead Rivers Alliance / DREAM surveys distinguish the two Polebridge accesses and explain Coal Creek’s changing side-channel landing. A landing review does not automatically establish a downstream bank, navigable channel, or calibrated travel time.

All Montana land overlays now require a reviewed route corridor; the browser no longer downloads all tracts in a broad endpoint rectangle. The build tool can normalize a self-touching source polygon only if area changes by at most 0.001 square metre and no new boundary longer than 0.01 metre is introduced. The immutable raw source and normalization evidence are retained; other invalid polygons still fail review. This is geometry cleanup, never permission to enter land.


## State release gates and unresolved access (Montana-first release)

The research catalog and the public map rollout are separate. In
`catalog/settings.json`, `mapRelease.states` lists states approved for map display
and `mapRelease.reviewedRoutes` controls reviewed line exports in runtime config.
Currently only Montana is enabled. New research must not change these flags.
`mapReleased` is generated per section; never write it in a source river record.

Use a nonempty section `accessReview` string when a usable launch/exit or route
identity remains unresolved, including a hazard that invalidates the advertised
trip. It suppresses map eligibility and all calculated/SEO reference times.
Explain the particular problem rather than saying the whole river is closed.
Attach dated `notices` with primary sources for known restrictions or hazards.
Remove the hold only after resolving the named endpoint and route issue. Missing
precise coordinates alone do not automatically imply illegal access or require a
hold; a documented facility can support an approximate map under existing rules.

Each state delivery should include: a section inventory; the source operator for
each endpoint (search federal/city/county sources as well as state FWP equivalents);
point precision; bank evidence only where known; permits and dated restrictions;
distance provenance; source trip times separately from the app model; and a short
queue naming exactly what remains unresolved. Barretts Station Park illustrates
why an absent FWP record does not mean no public take-out exists. Do not replace
a take-out upstream of a dam with the dam coordinate itself.

After integration run the catalog builder, freshness check, geographic audit and
Python/Node tests. Then check eligible maps in a browser before proposing a state
release. Keep GPS time remaining and automatic centerline-based distance adoption
disabled. No changes to research data publish automatically.

## Access identity and conflicting coordinates (October 28 follow-up)

Before promoting an access point, join aliases using an agency site ID and the
facility description, not only a similar name. Keep the current name, historic
names, source dates and conflicting attributes in the research package. An old
PDF title can point to a renamed site whose current detail page carries a closure
(Corwin Springs / Brogan’s Landing, ID 39753522). Conversely, a newer facility
announcement can document a launch missing from an older GIS attribute (John &
Nancy Owen FAS, ID 91552932). Neither case permits automatic coordinate promotion.

Check a proposed facility marker against nearby dams, bridges, road approaches
and the documented landing. Official provenance alone does not establish that a
coordinate is a launch. Reject inconsistent coordinates into a research-only
conflict record; never silently repair a digit, snap to water, or use a dam point
for a take-out. A published coordinate near a critical hazard may be unsuitable
even for an approximate marker. The Barretts and Fort Benton decisions in
`research/MT/access-review-20261028/coordinate-conflicts.json` illustrate this.

Deliver a section-level decision queue with `riverId`, `sectionId`, `status`,
`decision`, `nextAction`, and `sourceUrls`, plus a dated source-download manifest.
Distinguish a usable approximate access map from an approved river line, verified
mileage, calibrated timing, and current opening status. The October 28 queue
covers every previously withheld Montana section, including unresolved ones.
Keep uncertain route geometry in research with all feature flags false; keep
closed/ambiguous access pending. Save dated restrictions as section notices so
research findings reach both the calculator and guide pages.


## Permanent identity and national handoff (October 28)

New packages should include `id: "acc-..."` on each point and `aliases: []`.
Treat the ID as opaque and permanent. Copy existing IDs from
`catalog/access-index.json`; do not regenerate them from a changed name or
coordinate. New IDs are assigned by `tools/access_registry.py` during import.
Every section references `putInAccessId` and `takeOutAccessId`, including pending
endpoints. A cross-state endpoint references the original access ID. Do not
copy its coordinates into another state's registry or merge similar names
without identity evidence. Keep aliases unique within a registry. Existing
`putInPoint`/`takeOutPoint` references remain supported and must agree with IDs.

The source index lists every river and map-point file. Submit research separately
from reviewed catalog data. Do not copy `public/` generated assets, generated
readiness judgments, or map release approvals from an assistant package into the
application. The importer preserves known IDs and refuses cross-state river-ID
collisions. Replacing an existing state requires an explicit replacement flag.

Private user evidence uses `location` with finite numeric `lat` (-85..85), `lon`
(-180..180), `endpoint` (`putIn`, `takeOut`, `other`), `pinType` (`landing`,
`parking`, `entrance`), `method` (`manual`, `map`, `gps`), optional `observedOn`
(YYYY-MM-DD, no future date) and boolean `firsthand`. The server forces
`status: community-reported`; this is not a catalog access status. Evidence stays
in DATA_DIR/feedback.json, outside Git and public assets. A new landing remains a
candidate until normal source and access review is complete.

Each source snapshot must keep its retrieval date, URL and checksum. Failed
retrieval is a research issue, not proof of closure. The review dashboard's
`reviewed` decision records work performed; publication still requires editing
source records, passing validation, a dated section map approval, a browser
check, and deployment. Keep route display, land overlays, measured mileage,
and model timing distinct in readiness records.

## Current gauge check for every state package

Do not select a gauge solely because its name resembles the river. Confirm the
station is on the intended reach, upstream/downstream of relevant dams and
diversions, and currently supplies discharge (`00060`). A temperature reading,
historical daily value, or null/seasonal latest value is not current discharge.
Keep location/weather coordinates separate from gauge coordinates.

Run the actual app adapter against a running local preview:

```sh
python3 tools/audit_gauges.py --base-url http://127.0.0.1:8780 --state WY --output research/WY/gauge-audit.json
```

The tool checks each assigned station once, spaces requests, records failures,
and exits nonzero if any lacks a current reading. It never replaces gauges or
changes timing. `meetsFlowFreshnessCheck` only concerns the measurement; it does
not certify a calibration or suitability for the section. Do not retry a whole
state repeatedly when USGS is rate limited. Save the failed result and recheck
the affected stations later.

Optional river `gaugeContext` fields: `status` (`context-only`, `seasonal-gap`,
`unresolved`), `note`, `sourceName`, HTTPS `sourceUrl`, and ISO `checkedOn`.
These source notes appear in both the dashboard and the river guide. They do not
turn off current-data requests or mark a transient outage permanent. Use them
for a known seasonal gap, historical station awaiting replacement, or limits of
a representative gauge. New packages retain `timing.mode: unavailable` until a
separate timing calibration is reviewed.

### Reviewed alternative discharge sources

USGS remains the default. A historical or seasonal USGS station is not a reason
to silently select a different reach. Review the replacement's position, dams,
diversions, parameter, units, timestamps and current readings first. Preserve
the legacy `gauge` / `gaugeName` for source history; the app uses `flowSource`
when present. The five reviewed Wyoming examples are in the October 30 batch.

```json
{
  "flowSource": {
    "provider": "usbr-gp",
    "station": "GLWY",
    "parameter": "Q",
    "timeZone": "America/Denver",
    "kind": "streamflow",
    "name": "North Platte River below Glendo Dam",
    "note": "Replaces historical USGS 06652800 for displayed discharge only. No timing calibration is added.",
    "sourceUrl": "https://www.usbr.gov/gp-bin/hydromet_dayfiles.pl?GLWY",
    "checkedOn": "2026-10-30"
  }
}
```

`tools/flow_sources.py` validates this contract. For `usbr-gp`, `Q` requires `kind: streamflow` and `Q_I` requires
`kind: dam-release`. `GH` (stage), daily means and missing/flagged values cannot
substitute for instantaneous discharge. Require `gaugeContext.status:
context-only`, a reach-specific note, and `timing.mode: unavailable`. Do not
infer a new speed calibration from a replacement source.

The browser requests `/api/gauge?site=USBR%3AGLWY%3AQ`; the server allows only
sources present in the catalog. It requests the latest seven days from:

```text
https://www.usbr.gov/gp-bin/webdaycsv.pl?parameter=GLWY+Q&syer=2026&smnth=10&sdy=23&eyer=2026&emnth=10&edy=30&format=2
```

Dates are generated at request time. Format 2 retains quality flags; the parser
accepts only plain numeric readings, preserves true zero, rejects sentinels and
future timestamps, and skips ambiguous DST times. The source's generated-at
clock is checked against the expected Mountain timezone; unexpected conventions
fail closed. Reclamation results cache for 15 minutes; USGS results for five.
An upstream failure can reuse a cached response for up to one hour, explicitly
marked stale without changing the measurement timestamp. This does not extend
the app's two-hour freshness requirement for positive flow.

For a targeted recheck, repeat `--river` instead of auditing a whole state:

```sh
python3 tools/audit_gauges.py --base-url http://127.0.0.1:8781 \
  --river north-platte-glendo --river shoshone-river-cody \
  --output /tmp/floateta-targeted-gauges.json
```

Adding another provider requires an explicit adapter, validation and tests.
Public agency portal metadata can identify promising candidates, but a blocked
export is not a working feed. Keep those candidates in research with the exact
station, reach limitations and next action; do not mark them current in the app.


The reviewed Salida replacement uses `provider: colorado-dwr`, `station:
ARKSALCO`, `parameter: DISCHRG`, `kind: streamflow` and `timeZone:
America/Denver`. Its official source URL is
`https://dwr.state.co.us/Tools/Stations/ARKSALCO`. It has the same context-only,
unavailable-timing requirements as Reclamation. Salida discharge must not be
used with the Stone Bridge hazard threshold specified for upstream Nathrop.

The browser calls `/api/gauge?site=CDWR%3AARKSALCO%3ADISCHRG`. The server uses:

```text
https://dwr.state.co.us/Rest/GET/api/v2/telemetrystations/telemetrystation?abbrev=ARKSALCO
https://dwr.state.co.us/Rest/GET/api/v2/telemetrystations/telemetrytimeseriesraw?abbrev=ARKSALCO&parameter=DISCHRG&startDate=2026-10-23&endDate=2026-10-31&pageSize=2000
```

Dates advance with the request. Both calls share a 15-minute cache. With one
station and one continuously running service process, this is at most 192
successful upstream requests per day, below DWR's published anonymous quota of
1,000 calls/day. Adding stations or service replicas requires reviewing that
quota. Latest timestamps must include the expected Mountain UTC offset; raw
local history skips ambiguous DST times. Only DWR-origin, active, CFS discharge
with A/O/P quality and no secondary flag is accepted. Ice, backwater, estimated,
seasonal and equipment flags are not numeric flow. Partial paginated responses
fail closed. Missing values never become zero.

Review-queue generation now discovers each imported state's local
`research/<ST>/review-queue*.json`, `readiness-status.json`, `access-grades/`,
and `pending-map-points/` automatically. Original evidence stays private.
Research readiness labels do not approve maps: section fingerprints and the
map release configuration remain independent requirements.

Failed provider requests also back off for 15 minutes (USGS: one minute), including when no successful cache exists. This prevents visitor traffic from exhausting an unavailable agency feed. Cached values retain their original measurement and fetch timestamps.


### Agency status and access-role checks (October 30 review)

Deliver the agency feature ID (prefer GlobalID, GEOMETRYID or stable facility ID),
source URL, fetch date, immutable source hash, original coordinates, feature type,
public-access/operator fields, launch/egress flags and open/closed/seasonal status.
Do not discard null or unknown status. A launch-only site cannot silently become
a take-out. A recreation area, parking polygon or right-of-way record does not
by itself identify a usable boat landing. Preserve conflicting records and dates
in the research review queue; do not resolve them by picking the closer point.

Supply an imagery verdict with a specific observation, source/capture-date
limitations and file reference. Distinguish a visible ramp from a parking/ramp
head and from a general access area. Use `areaCenter` for approximate facilities;
do not move a point to water from imagery and call that agency verified. Include
known road closures, carry distances, bridge/dam/portage questions and access
restrictions. Published float times must match the exact endpoint pair; NPS Tyler
Bend's two launches demonstrate why a familiar place name is not enough.

A state package is research evidence, not an automatic map or ETA release.
`catalog/map_reviews/<ST>.json` holds explicit section approvals; changing a
section or either normalized access record invalidates its fingerprint. Live
flow, map access, dotted geometry and timing calibration remain separate checks.
Use the configured sources and bindings in `catalog/agency_sources/index.json`
to refresh evidence. Never automatically promote changed source records.

## Optional gauges and reference stations (October 30 release candidate)

A gauge is no longer required. Do not insert the nearest station just to pass
validation. Use `"gauge": null`, `"gaugeName": null`,
`"gaugeRelationship": "none"`, `timing.mode: "unavailable"`, null calibration
numbers, and a sourced `gaugeContext` explaining the search/limitation. Known
historical or intermittently reporting stations can remain assigned: no-data
responses are retried, not treated as permanent closures.

`gaugeRelationship` accepts:
- `representative`: an assigned, reviewed station for the river's displayed flow.
  This is the backwards-compatible default for existing assigned gauges. It does
  not create a timing model or certify a measurement at every section.
- `same-river-reference`: contextual flow elsewhere on the same river. Displayed
  as **Reference gauge flow**, without flow-based trip estimates, reference-flow
  condition comparisons, or water-temperature clothing advice.
- `other-river-reference`: an informational station reference on another river.
  Its readings are not requested or used for this river's flow, temperature or
  timing. Keep the station name/link and the reason in `gaugeContext`.
- `none`: no assigned usable source. No gauge request is made.

The last three require `timing.mode: unavailable` and sourced `gaugeContext`
(`status`, `note`, `sourceName`, HTTPS `sourceUrl`, `checkedOn`). For reference
stations explain upstream/downstream position, confluences, dams and diversions;
do not infer representativeness from straight-line proximity. Candidate gauges
and rejected alternatives stay in `research/gauge-checks.json`. Returning flow
restores only the reading unless a separate timing model is already supported.

The visible dashboard refreshes every five minutes and when the tab is resumed.
Server responses cache for five minutes (USGS) or fifteen (USBR/Colorado DWR).
The on-demand cache retries missing data after expiry; API failures back off.
This is not an always-running background audit. `tools/audit_gauges.py` can be
run periodically by an operator; unassigned and other-river references are
reported without making meaningless requests. No scheduled job is installed.

## River-course evidence when adding accesses (November 5 review)

The NHD importer now includes both the named river and unnamed flowlines in
its bounded query, matching the archive workflow. A query using only the river
name can omit a side channel and falsely suggest there is a single route.
`queryPolicy` and `queryScope` record the selection method, stream name and
bounding box. Changing the query or expanding the access envelope refreshes the
working cache while preserving the previous bytes in a hash-named snapshot.
Network candidates still require review; neither a matching distance nor a
single remaining graph path proves the line follows the present river.

For a new access within an already reviewed course, retain its own stable access
ID and agency binding. Compare its coordinates with the visible landing before
using `verified`; use `access-verified` and `areaCenter` when only the facility
area is supported. Do not replace an agency landing coordinate with an offshore
guide coordinate. Preserve aliases and conflicting source locations as evidence.

Shorter course views may reuse reviewed geometry when their source feature IDs
and geographic containment have been checked, their new endpoints have been
reviewed, and all barrier/omitted-approach limits are retained. They still need
their own section fingerprints and route approvals. Published mile markers and
exact-pair guide times remain separate evidence; do not extrapolate a guide time
onto neighboring sections or convert it into a flow-speed calibration.

## County access sources and mixed precision (November 5 expansion)

Prefer a reviewed landing coordinate. When the evidence supports only the access
facility, retain a source-backed approximate area and explain the uncertainty;
do not suppress an otherwise useful access map solely for lack of landing
precision. Use `access-verified` with `areaCenter` for these areas. The public
map labels them Area and offers Help pinpoint links. User coordinates remain
private evidence until reviewed; they do not automatically move published pins.

County facility layers can fill gaps in state datasets. Register the query and
public field allowlist in `catalog/agency_sources/`, save its immutable response,
and bind each selected feature to a stable access ID. A record captured as
Placed on Map establishes an agency facility location, not landing precision.
Check the visible landing and guide endpoint before approving a precise pin.
Waupaca County's nearby Norrin access is distinct from the Wolf River Road
bridge access named in its paddling guide; proximity is not a name match.

Keep dotted course evidence independent of access precision. A reviewed main
river course may be shown as a `river-course-overview` while shoreline
connections remain unresolved. Document omitted approaches and source geometry
limitations, preserve published trip mileage separately, and leave distance
estimation and GPS remaining-time features disabled for these overviews.

Recheck older guide descriptions against later agency updates about barriers
and facilities. The Little Wolf's Manawa millpond changed after the 2024 breach;
the county's older route description does not resolve present landing usability
or passage through the dam site. Approximate placement resolves a precision gap,
not a known barrier or unresolved access-permission issue.

### County trips missed by statewide access inventories

A river draft with too few statewide boat-access records may still have useful
county or municipal launches. Crystal River is an example: the county guide and
facility layer support Rural, Nelson Park and Shadow Lake trips that the original
statewide-only import omitted. Preserve the original draft as historical
evidence and record the later source review separately. Extend the existing
county source query and bindings; do not create duplicate access IDs for the same
facility in a second source pipeline.

Check dam records by geographic envelope as well as name. Joined agency fields
may use different casing, so an empty text query alone is not evidence that no
dam exists. Record physical and legal status separately, and compare dates with
older plans. Current DNR records mark Little Hope/Crystal Dam removed while
Rural and Felt Mill remain on the landscape.

A published trip may leave the downstream river for a lake through its outlet.
Do not flip river-network edges automatically or invent a straight line to the
lake ramp. Keep the documented access map and exact-pair guide mileage/time,
save alternative geometry as research, and withhold the dotted route until its
full course and direction have been reviewed. A known-good access map does not
require a guessed gauge or an approved dotted line.
### Permanent evidence links and reach-specific warnings

Use the stable agency document viewer or the agency page that links to the
document. Do not put a temporary signed download URL in a river, access or state
record. The catalog builder rejects common expiring download credentials; keep
the downloaded document, checked date and hash in the research evidence instead.
For example, use the DNR Flambeau booklet's `widnr.widen.net/view/pdf/...` link,
not the underlying `previews...widencdn.net` link with `sig.expires` parameters.
Page fragments can identify the relevant PDF page without adding credentials.

Match warnings to the chosen reach. A warning about a distant rapid must not
appear as though it sits between every pair of access points. If exact hazard
locations remain uncertain, explicitly name the broader guide segment and keep
the detailed river/portage review open. Preserve real dam holds and distinguish
rapids above the launch, within the trip and beyond the takeout.

Agency narrative distances may be rough or incomplete. Do not turn intermediate
phrases into a precise trip length when they disagree materially with geometry.
The Smith Rapids–Cedar Rapids bridge example keeps the access map available while
withholding disputed distance, time and dotted-path output. New aliases such as
Smith Rapids retain the existing stable access ID, coordinates and precision.

### Approximate access areas and town-to-town guides

Prefer a reviewed landing coordinate. When the documented access exists but its
water edge is uncertain, retain a useful `access-verified` area and explain what
the marker locates. An imagery refinement of an agency facility point must keep
the original source snapshot, old coordinate and review image; describe the
refinement rather than calling it an agency-surveyed coordinate. The November 6
Lower Wisconsin review has examples at Arena and Bridgeport North.

Town names in a canoe-time table can refer to several nearby landings. Match the
guide extent to a named landing using the detailed agency map, and describe
rounded town-to-town mileage in `distanceEvidence.note` and the trip notes. Keep
it separate from measured river geometry and live timing. Do not copy a guide
time onto every existing section near the town. If the intended launch remains
ambiguous, defer that trip and use another explicit landing-to-landing source.
The Lower Wisconsin review defers Sauk City–Arena while adding the board's named
Mazomanie–Arena trip. Separate east/west landings retain separate stable IDs.

### Separate an access listing from a coordinate anchor

A current agency guide may establish that a public landing exists while a second agency dataset only locates a nearby bridge. Keep those claims separate: use the access guide as `sourceUrl`, the bridge record as `coordinateSourceUrl`, and an `areaCenter` with `status: access-verified`. A monitoring station is not a boat-ramp survey. Describe the landmark, required carry and remaining uncertainty; retain the exact-landing correction link. Never promote the station to a precise landing merely because it sits near the water. See Landing 18 in `research/kickapoo-review-20261106/decisions.json`.

When a later imagery review contradicts an existing river line, preserve its source and geometry in the research/catalog record, disable its public feature flags and remove the generated public route. Retain independently supported access markers and guide times. Record the dated withdrawal explicitly so historical preservation checks do not silently restore the older approval. A current blockage notice is a separate fact from whether a line follows the river; do not turn a lack of later reports into proof that passage has reopened.

### Local names and unresolved candidate landings

Research the names people actually search for, especially when an inventory says
only “Village Park Access.” Add documented local names to that existing point's
`aliases` and its `catalog/access-index.json` entry. Preserve the permanent ID,
coordinates and precision unless separate location evidence supports a change.
Search uses these aliases automatically and explains alias-only matches; no
per-state search code is needed. Re-review affected map fingerprints when access
metadata changes. Soldiers Grove / Beauford T. Anderson Park is an example in
`research/middle-kickapoo-expansion-20261106/point-changes.json`.

Keep unresolved new locations in
`research/STATE/local-review-BATCH/decisions.json`, using a top-level `state` and
`points` object. Each point should have `status: "research-only"`, a specific
`blocker`, source URLs, `evidenceSummary`, and an actionable `nextAction`. Use
`candidateCoordinates: null` when no supported candidate has been found. If
coordinates are supplied, retain their source and explain whether they locate a
landing, entrance, parking area or other landmark. `tools/build_review_queue.py`
discovers these records automatically; they do not become public access pins.

A current park page plus an older paddling account is a research lead, not proof
of a current designated launch. Inspect the current owner map for boundaries
and the intended water approach. Keep differences between an account's headline
distance and its overview table in the review queue; do not silently select the
more convenient number. A PDF's upload directory or search-result publication
date is not its revision date—read the date printed in the document.

### Shared advisories on longer river listings

Keep notices attached to the affected sections in the catalog. The planner and
server-rendered guide automatically show a notice once when its title, text,
source URL, source name and checked date match across at least three sections.
Every affected section retains a visible title and link to the full advisory;
the advisory also lists links back to those stretches. Unique notices and access
or distance holds remain fully visible on the individual section. Do not remove
section notices, broaden their scope or change evidence dates just to group
them. No state-specific display configuration is needed.

### Same-name rivers and future access plans

Disambiguate a river by town, watershed and gauge before matching access features.
Wisconsin has Kinnickinnic rivers near both River Falls and Milwaukee. A name-only
GIS match must not move a launch, assign a gauge or create a new stable access ID
on the wrong waterway. Keep this context in the river name and source review.

Concept plans are evidence of proposed facilities, not existing launches or dam
removal. Compare them with the current agency inventory, municipal access page
and present-day imagery. Retain a supported approximate access area when the
facility is established but its exact landing is uncertain; explain carries and
separate parking from the water edge. Community corrections remain reviewable
evidence rather than automatic pin changes.

If the live hydrography service is unavailable, use the official downloadable
archive through `tools/fetch_nhd_archives.py`. Record its upstream URL, size,
checksum verification and dated receipt in `research/routes/nhd-archives.json`.
Older source geometry still needs imagery review: passing connectivity checks
does not prove that a line follows today's bends. Approve a supported shorter
course independently and hold a discrepant extension. Keep published trip
mileage and trip-specific guide times independent of any trimmed overview.

When a later agency inventory identifies the actual launch, promote that access
without changing its stable ID. Use the coordinate from the launch row, not the
nearby fishing area, trail reference point, bench or parking row. Keep the dated
table, source image and previous pin in the review ledger. Glen Park's launch
below Powell Falls is an example in `research/upper-kinni-20261106/decisions.json`.
If an approved course references that access, recompute its endpoint snapshot,
source station and offset, then re-review its signature and affected map
fingerprints. A better pin does not authorize a new connector or remove an
existing dam-approach omission. Preserve the reviewed geometry and independent
trip mileage unless separate evidence supports changing them.


### Minnesota water-trail source pipeline

Use `catalog/agency_sources/MN-dnr-water-trail-access.json` with `python3 tools/fetch_agency_layer.py --source MN-dnr-water-trail-access`. The source filters to agency water-trail sites and archives a complete, hashed snapshot; it does not promote points. Bind reviewed accesses using `unique_swas_id`, not a mutable object ID or name. Retain Float ETA access IDs across source-name changes. The November 6 snapshot has 643 source candidates.

A GPS collection method does not prove the coordinate marks the water edge. For the Kettle starter trip, both original site coordinates remain approximate areas, with independent published-trip mileage and correction links. Reconcile river-mile discrepancies explicitly and check current park/agency notices: an empty GIS alerts field is not proof a facility is open. Keep suspect operator names in research until resolved.

Minnesota also publishes water-trail and major-river line layers. Use the registered `MN-dnr-water-trails` source with `tools/stage_agency_course.py`; the validator reconstructs each displayed segment and endpoint trim from the saved source and checks the documented downstream trip order. Staged geometry stays in research until the course and access limitations are reviewed. Do not reuse USGS feature IDs or source claims for a DNR line. Kettle review evidence starts under `research/minnesota-kettle-20261106/`; the Root and lower Root examples are under `research/root-river-20261106/` and `research/lower-root-20261106/`.

### Reviewing hydrography forks without automatic channel selection

`tools/inspect_route_branches.py` produces a downstream branch inventory and a
GeoJSON network in a local research directory. It intersects forward and reverse
reachability, so it scales without enumerating every possible route. Use a
projected CRS in metres, the current generated catalog, and a saved USGS source:

```sh
python tools/inspect_route_branches.py --river beaverhead --section pipe-organ-grasshopper --source research/routes/MT/hr-sources/beaverhead-3d806a325f7cdba7.json --output research/branch-review-example --projected-crs EPSG:32612
```

After inspecting the alternatives against imagery, supply `--choices` with a
JSON list of `{node: [longitude, latitude], featureId, reason}` records. Use exact
junction coordinates and feature IDs from the inventory. Every encountered fork
needs a decision; duplicate, unrelated and unused decisions are rejected. The
result remains a candidate with all display/timing flags false. It must still
pass source, geometry, access, distance and independent imagery review. Neither
shortest-path selection nor apparent channel width grants approval. Keep wet
side-channel alternatives documented. An inventory-only rerun archives any old
candidate, and failed choices leave the previous inspection untouched.

The Beaverhead example and reviewed branch images are in
`research/beaverhead-branches-20261106`. For its planning mileage, the separately
saved FWP 0.1-mile markers supersede older rounded guide numbers. A mapped course
length and nearby agency mile-marker distance can differ; preserve their source
and purpose, and keep precision labels and source limitations visible.

### Check whether newer national river geometry actually exists

Before retrying a held river course with another USGS service, run a coverage
audit. A newly refreshed 3DHP service can still contain legacy NHD geometry.
`featuredate` is a database load date, not a new imagery or river-survey date.
Find the river's explicit GNIS ID in the USGS flowline attributes; do not guess
it from a nearby stream or reuse the USGS gauge number.

```sh
python tools/audit_hydro_coverage.py --river zumbro-river-mn --section hammond-theilman --gnis-id 654509 --course research/zumbro-expansion-20261106/zumbro-river-mn--hammond-theilman-candidate.json --output research/zumbro-coverage-next-check
```

Use a new research output folder each time. The optional saved course expands
the search envelope to include its bends; without it, the envelope includes
only the access points and a margin. The tool checks complete feature inventories
twice, archives allowlisted attributes and hashes, and records `legacy-only`,
`edh-data-to-inspect`, `provenance-needs-review`, or `no-matching-flowlines`.
An EDH workunit intersecting the envelope does not prove that the whole float
has new geometry. Inspect the actual flowlines and imagery before any course
approval. Unknown source lineage stays unknown. Never translate this report
into verified landings, live timing, navigation approval or an automatic route
release. The tool writes only research files and leaves catalog/public data
unchanged. See `research/zumbro-course-refinement-20261106/coverage-audit/`.

### Keep the landing distinct from its namesake park

A named picnic park or campground does not establish where boats can land.
Read the managing agency's approach instructions and retain its stable access
ID. At Nimrod on the Crow Wing, the county explicitly places the carry-in
across the river from Stigman's Mound picnic park. The agency point supports an
approximate access area on the launch side, not an exact water-edge pin or a
landing at the picnic park. Preserve checked exact pins elsewhere; use Area
and Help pinpoint only where the evidence remains approximate.

When a current map's route table, recommendation panel and GIS inventory use
different river miles, record the disagreement and use one consistent set of
endpoints. Do not silently mix them or label the derived distance exact. The
Crow Wing review retains approximately 9.2 miles for Little White Dog–Cottingham
and explains the panel's 9.8-mile figure. Its source course is independently
reviewed for display; that does not calibrate paddling speed. Recent same-river
discharge can remain reference information with live timing unavailable.
See `research/crow-wing-expansion-20261106/decisions.json`.

### Match published trip times to the actual access pair

One park can contain several distinct boating facilities. Crow Wing State
Park's Mississippi carry-in (`WAS00990`, river mile 990.4) and upstream trailer
ramp (`WAS02297`) are different access identities. The Headwaters Board's
Kiwanis excursion ends at the carry-in. Do not attach its duration to the
trailer ramp, interpolate it onto shorter trips, or use the park's full
river-mile extent as a landing coordinate.

Store an explicitly published duration in that section's `guideTimes`, with
the source, conditions and check date. Keep independently sourced planning
mileage in `distanceEvidence`; explain rounding differences instead of
changing either value to fit the other. A current same-river gauge can provide
reference context while `timing.mode` remains `unavailable`. If dams or major
tributaries separate the gauge from the trip, say so. This does not justify a
new live speed model.

The Mississippi review adds seven trips across two geographic listings with
seven stable access identities. LeBourget's agency point matches the visible
public ramp and remains precise; six less-resolved landings retain original
agency coordinates as Area markers. Its dotted course stops upstream of Little
Falls Dam. Each base leg has a complete imagery review; combined trips are
checked against the geometric union of those legs. Public ramp verification
does not establish a ramp-to-centerline connector. See
`research/mississippi-brainerd-20261106/decisions.json` and
`tests/test_mississippi_brainerd.py`.

### Agency sites with missing water-trail join fields

A documented access can be absent from an otherwise complete water-trail query.
Check the agency's full access inventory before concluding the site is missing.
For Pine River's Rock Dam, DNR recommends the launch but its inventory row has
blank water-trail fields. The MN source adds stable ID `WAS02986` as an explicit
query exception. Save the complete refreshed snapshot and compare additions,
removals and changed features; retain existing reviewed bindings. This discovers
source evidence only. Landing precision, public approach, river-course geometry
and timing still need separate decisions. See
`research/pine-river-expansion-20261106/decisions.json`.

### Resolve guide totals against named endpoint labels

Do not use a water trail's headline mileage for an arbitrary pair of accesses.
Check the printed map's landing labels separately from nearby historical markers.
For Eau Claire, the Phoenix Park carry-in is at mile 58.1, while its historical
landmark is 58.2. Forest Street (the guide's Maintenance carry-in) is 58.9 and
Hobbs is 56.1. Their differences support 0.8-, 2.0- and 2.8-mile planning trips,
despite inconsistent overall 2.7-/4.2-mile descriptions. Record the discrepancy;
do not silently select a headline that matches a measured line.

Cross-check older access guides against current operator listings and imagery.
A current facility-page coordinate can still mark a building: Forest Street
keeps the guide's bank-side area instead. Hobbs retains its existing DNR
coordinate and stable ID, with landing precision supported by the visible shore
approach and managing-city listing. Its precise takeout does not make the other
endpoint or the dotted river course precise. Keep upstream dam holds when adding
separate below-dam trips. See `research/eau-claire-water-trail-20261106/decisions.json`.

## Mileage measured from a published route map

When a responsible agency or firsthand trip publisher provides a line but no
numeric trip length, use `distanceEvidence.method: mapped-course-length`.
Do not call a computed number a published trip length or invent endpoint river
miles. The first example is `eau-claire-river-lower / river-prairie-phoenix`.

Keep the usual `sourceName`, public HTTPS `sourceUrl`, `checkedOn`, `streamId`
and `note`. Each endpoint needs the matching section `name`, reviewed `lat` and
`lon`, and a `sourceLocation` identifying its map label. Access areas are valid
endpoints; this does not promote them to precise landings.

The `measurement` object contains `format: kml`,
`algorithm: haversine-6371008.8m`, a local `research/` `evidenceFile`, its SHA-256
`sha256`, one unique `featureName`, unrounded `measuredMiles` and a `reviewNote`.
Archive the original KML, including provenance from the publishing page; do not
redraw it to fit a desired distance. Inspect the whole course, both endpoints
and important bends against imagery, and record unresolved hazards separately.
The current adapter accepts one downstream LineString and checks that its ends
are within 250 metres of the named access locations. That tolerance is a
mismatched-endpoint check, not a claim of landing accuracy. Changed evidence or
endpoint coordinates require re-review. Section `miles` is the measured value
rounded to one decimal place. Explain shoreline gaps and generalization in the
note. Another source format needs an explicit adapter and tests; never relabel
it KML merely to pass validation.

Both planner and river guide label this **Measured from published map**. This
establishes approximate planning distance only. Course display, precise access
pins, river-bank claims, land overlays, live estimates and GPS time remaining
keep their separate review requirements. Validate with:

```
python3 tools/build_catalog.py --check
python3 -m unittest discover -s tests -p 'test_mapped_distance.py'
```
