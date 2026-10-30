# Local expansion — October 29, 2026

This batch stays local at http://127.0.0.1:8780/. It does not change production.
The Greycliff opt-in pilot remains separately configured and still lacks a real
phone field test. The checkpoint before this work is in
`/Users/home/Documents/Codex/FloatETA-before-national-expansion-20261029`.

## Results

- 125 rivers, 342 sections, nine states, 459 permanent access IDs.
- 217 sections have access maps in this local release configuration, up from 200.
- New sections: two Missouri Breaks legs via Coal Banks; two John Day legs via
  Thirtymile; Galice–Grave Creek on the Rogue; Steelhead–Sunset on the Russian.
- New state: California, starting with the Russian River. Summer tube guidance
  is published separately; no invented live timing calibration.
- Reviewed 23 agency GIS feature bindings: 21 Oregon facilities and two Boise
  landings. California's two county park locations and Montana's Coal Banks
  facility add three separately sourced approximate access areas.
- Existing 59 display-only dotted paths remain unchanged. No new dotted route or
  nationwide location-based ETA is claimed by this batch.

Oregon map coverage is now 13 of 15 sections. Both Sandy routes depend on Oxbow,
which Metro reports closed from September 8, 2026 until an expected early-2027
reopening. They have no map button or trip estimate. A calendar date alone must
not reopen them; recheck the managing agency and actual access.

Boise's Ann Morrison–Eagle route stays withheld because it crosses downstream
diversion/whitewater infrastructure without a reviewed through-route and exit.
Cabarton ends at Smiths Ferry, not Banks; private access permission remains
unresolved. Beehive–Horseshoe and Kirkham/Lowman–Deadwood also retain access holds.

Distance corrections use BLM sources: Harpham–Maupin 4.0 mi, Maupin–Sandy Beach
6.4 mi, Banks–Beehive 7.3 mi, Cabarton 9.8 mi, Danskin–Confluence 13 mi via the
contiguous SF04/SF05 guide pages (joining at Alder Creek). John Day uses the BLM
launch table consistently: Clarno 109.2, Thirtymile 84, J.S. Burres 39.6, yielding
69.6, 25.2 and 44.4 mi. These remain approximate published distances.

The old Thirtymile EA link now returns a missing-document page. It is not used
as runtime mileage evidence. The current visitor sheet establishes the usable
primitive launch and seasonal road restrictions; the accessible BLM launch table
supplies mileage. This avoids relying on a proposed project as proof of access.

## Scaling workflow

1. Start with one source-backed cluster of popular floats in a state. Reuse
   existing landing IDs; do not create one duplicate pin per river or section.
2. Register an agency point source under `catalog/agency_sources/`. The agency's
   own website must identify the map/layer. Allowlist only public attributes.
3. Fetch a complete snapshot with `tools/fetch_agency_layer.py`. Partial results
   fail; snapshots are hashed and immutable. Candidate data stays in research.
4. Bind named access sites to stable agency IDs and retain conflicting evidence.
   Distinguish ramp, hand launch, parking and park-area coordinates. Check current
   restrictions and the entire proposed trip, including downstream dams.
5. Review placement against imagery. Exact water-edge evidence is required for
   an exact marker; an approximate park marker can support a clearly labelled
   access map without pretending to be the landing.
6. Add sourced guide mileage and times. Check gauge identity and a recent
   positive discharge response. New rivers have no live ETA until calibrated.
7. Run the source-binding check, catalog build, private queue build and tests.
   Deliberately review section fingerprints after evidence changes. Importing
   and passing a validator do not approve a map or deploy anything.

`catalog/RESEARCH_FORMAT.md` is the assistant handoff contract. Use the Russian
River record as a new-state example and John Day as a multi-section/shared-access
example. `catalog/source-index.json` lists the source and agency-source indexes.
The private queue at `/review` now includes the reviewed agency bindings and
flags changed/disappeared features after a source refresh.

## Follow-up research

- Gauge audit: all 269 local HTML/assets returned HTTP 200. Of 120 distinct
  original station assignments, 110 had recent positive discharge. Encampment
  was corrected from historical 06624500 to active 06625000 and then passed the
  actual app adapter (86.5 cfs, 31.6 minutes old). The river remains uncalibrated;
  its mouth gauge does not describe the North Platte segment after the confluence.
- Nine station gaps remain: eight Wyoming assignments have no recent discharge
  and Arkansas 07091200 returned a null value marked SEASONAL. The correct
  Arkansas station is retained. Tongue 06299980 is marked DISCONTINUED (2018),
  and Glendo 06652800 last returned flow in 2016. No current substitute is
  inferred across reservoir controls. Each affected river now explains the gap.
  `http-audit.json` preserves the initial sweep; `encampment-gauge-audit.json`
  records the corrected station. Use `tools/audit_gauges.py` for later checks.
- Unauthenticated diagnostic queries to the latest-continuous API eventually
  returned 429. No missing response was interpreted as a closed or discontinued
  station. The complete previously saved Wyoming latest snapshot, seasonal
  Arkansas result and actual app audit supply the decisions above.

- California: the lower American and South Fork American have agency pages/maps
  saved here. Resolve exact named launches and source-backed trip lengths before
  adding them. USGS 11446500 has current discharge; 11445500 did not in the checked
  interval, so do not assume a historical station will power live estimates.
- Oregon: Bend's park district has strong access and whitewater-park guidance.
  Source actual river mileage separately from the return walking distance, and
  choose a representative active flow source. The checked 14070500 request had
  no recent discharge. Do not copy that station into a new live model.
- Idaho: work through the remaining access sites using managing-agency GIS and
  current permission. BLM's older Payette guide labels Cabarton access private;
  boatable water is not proof of a public launch.
- Montana/Wyoming: use the existing readiness and route queues. Newly added
  Coal Banks is a facility-area marker and is not sufficient for an exact river
  path endpoint or GPS remaining-time estimate.

## Map configuration and test limits

Imagery uses the existing restricted browser key. Static map labels require a
separate ArcGIS Location Platform privilege; the current local key's label
request returned HTTP 401 / error 498 while imagery worked. Labels now default
off. After separately authorizing the service, set `ARCGIS_LABELS_ENABLED=true`
or local `imageryLabelsEnabled: true`. No account privileges or billing changed.
Official service documentation:
https://developers.arcgis.com/rest/static-basemap-tiles/arcgis-imagery-labels-meta-data-get/

Browser checks cover desktop/mobile layout, imagery, sources, approximate labels,
closed-route withholding and current Russian River gauge data. The in-app browser
does not provide phone geolocation, so that remains a phone field-test item.
Validation results are saved in `validation.json` after the final check.

The initial-load state selector race has a regression test: a late river response
cannot overwrite a newer state choice or reopen the old linked map. SEO pages
now describe per-stretch distance ranges instead of double-counting overlapping
float options as total river mileage. Optional satellite labels default off
without their separate service authorization; imagery remains enabled.
