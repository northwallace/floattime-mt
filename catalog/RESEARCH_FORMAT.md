# Float ETA catalog and research contract (local preview, 2026-10-26)

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

Units are `hours` or `days`. Values must be positive finite numbers, min <= max.
Preserve flow-band conditions, craft, source age and whether stops are known.
The app displays guide guidance separately and never adjusts it using craft,
fishing, launch time or today's flow. Minimum planning allowances must be
described as minimums, not promised maximum travel times.

## Access registries

Use `catalog/map_points/STATE.json`, version 2, with `state`, `auditedRivers` and
`points`. Access types and operators are descriptive text, not enumerations.
Point names must exactly match section endpoint names. Stable research IDs and
aliases should also be retained in the research inventory; the production
registry still uses names as keys.

- `pending`: `status` and explanatory `note`; no coordinates. A map stays hidden
  if either endpoint is pending. Confirmed closures, unresolved permissions,
  competing sites and critical take-outs without a dependable location stay
  pending until reviewed.
- `verified`: existing exact facility fields: numeric `lat`/`lon`, `accessType`,
  `operator`, `sourceName`, HTTPS `sourceUrl`, ISO `verifiedOn`, and `note`.
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

- `method`: `agency-mile-markers` (the currently supported method).
- `sourceName`, HTTPS `sourceUrl`, `checkedOn` (`YYYY-MM-DD`), `streamId`, `note`.
- `putIn` and `takeOut`: objects with `name` matching the section label; `lat` and
  `lon` matching the reviewed facility coordinate; `riverMile`; integer `markerId`;
  and `offsetMeters` between that coordinate and the selected marker (0–200).

Use the same agency stream identifier for both endpoints. Confirm the river and
downstream direction using the agency guide; do not select a closer tributary or
silently average conflicting sources. `miles` must equal upstream minus downstream
river mile, rounded to one decimal. The UI labels this approximate and links the
source. A changed endpoint or mileage must be re-reviewed before the build passes.
This method is appropriate only where river measures decrease downstream. Other
measurement conventions need a separately reviewed implementation.

Keep raw responses and exact query URLs in `research/STATE/`, outside the public
catalog. The Montana example is `research/MT/mileage-20261027/fwp-mile-markers.json`.
Do not automatically promote pending coordinates from proximity to a river-mile
marker: measuring distance does not establish a legal access point or exact ramp.


## Optional river-route package (independent of access verification)

Continue delivering river records and access points in the existing format. River lines are an additional layer, not a requirement for adding a river or proof that access is legal. Do not add a line by connecting put-in and take-out with a straight segment, choosing the widest visible channel, or joining unmatched tributaries.

The working example is `catalog/routes/MT/blackfoot--johnsrud-weigh-station.json`; the authoritative validator is `tools/route_catalog.py`, run by `python3 tools/build_catalog.py --check`. Keep a source URL, agency stream identifier, raw dated source snapshot and SHA-256, the geometry in WGS84 `[longitude, latitude]`, exact copies of the catalog endpoint names/coordinates and mileage, and evidence establishing downstream direction. `review.checkedOn` is the date we assessed the record; do not call it the imagery or survey date.

Research deliveries should use `status: candidate` and all four feature flags false: `display`, `landOverlay`, `distanceEstimate`, `remainingTime`. Store candidate geometry and unresolved alternatives under `research/routes/<STATE>/`, outside `public/`. The importer stages candidates there and writes a per-section review queue. A route is not verified simply because a validator passes. Explain endpoint offsets, alternative channels, source discontinuities and mileage disagreements; do not alter a catalog value to make a test pass.

For measured ArcGIS sources, configure a state source record like `catalog/routes/sources/MT.json` (exact layer URL, stream ID field and IDs, CRS and measure direction). Other formats need an explicit adapter with equivalent checks. State registry entries live in `catalog/routes/index.json` → `<STATE>.json` → per-section JSON. New states use the same display format and validator; map JavaScript does not need a new hardcoded river branch.

Only a reviewed record may enable route display. Land shading requires separate sourced polygon data and a corridor tied to the route geometry checksum. Never infer public landing rights from ownership or proximity. Keep `distanceEstimate` and `remainingTime` false: automatically replacing published miles and live GPS ETA are deferred. The original Blackfoot GPS experiment remains archived separately.


## Published river-mile guides and facility coordinates (October 27 follow-up)

A general agency site point is not automatically a ramp coordinate. Check the GIS layer's purpose and compare the point with a ramp-specific plan, published access survey, or landing imagery. Where boat access is documented but the coordinate locates the facility generally, use `access-verified` plus `areaCenter`, directions, and a coordinate source URL. Do not promote an inland facility centroid by snapping it onto the nearest river line. Glen, Black’s Ford and Greycliff are current examples of approximate facility records; Smith River shows how two documented facilities can support a useful approximate map without claiming exact landings.

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
