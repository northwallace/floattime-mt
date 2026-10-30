# Local gauge and map review — October 30, 2026

This batch stays local. It does not publish the other states or change the
published Greycliff field pilot. The preview runs at <http://127.0.0.1:8781/>;
the private review inventory is at <http://127.0.0.1:8781/review>.

## Gauge results

Five of the nine previous discharge gaps now return current observations through
the app's actual HTTP adapter. `nine-gaps-audit.json` records the source IDs,
reading ages and point-in-time results. All five sources are provisional
Reclamation data and remain context only; no Wyoming ETA model is enabled.

| River | Reviewed source | Limitation |
| --- | --- | --- |
| North Platte below Glendo | GLWY Q | Below-dam flow; releases can change. |
| Gray Reef–Casper | GDWY Q_I | Imported dam-release discharge; not local stage or flow at every downstream landing. |
| Bighorn at Thermopolis | WRBD Q | Wind River below Boysen; upstream context for the downstream Bighorn sections. |
| Shoshone at Cody | SRBB Q | Below Buffalo Bill and above Corbett diversion. |
| Shoshone at Willwood | SRBW Q | Below Willwood diversion; not interchangeable with upstream readings. |

Primary station pages: [Glendo](https://www.usbr.gov/gp-bin/hydromet_dayfiles.pl?GLWY),
[Gray Reef](https://www.usbr.gov/gp-bin/hydromet_dayfiles.pl?GDWY),
[Boysen](https://www.usbr.gov/gp-bin/hydromet_dayfiles.pl?WRBD),
[Buffalo Bill](https://www.usbr.gov/gp-bin/hydromet_dayfiles.pl?SRBB) and
[Willwood](https://www.usbr.gov/gp-bin/hydromet_dayfiles.pl?SRBW).
Station identities and available parameters were checked against the official
GP station list, parameter dictionary and current dayfiles; snapshots and SHA256
hashes are in `manifest.json`.

The adapter uses Reclamation's format 2 dayfile table because it retains quality
flags. It rejects flagged/non-numeric readings, missing-value sentinels, negative
discharge, future observations, a wrong station/parameter, and an unexpected
source clock. Real zero remains zero. The generated-at clock was compared with
UTC during retrieval and matched America/Denver; this is an observed convention,
not a claim that the GP documentation guarantees it. The clock guard fails closed
if that convention changes. Ambiguous DST observations are skipped. During a DST
clock transition the source can temporarily be unavailable rather than report
an invented measurement age.

Reclamation results cache for 15 minutes; USGS stays at five minutes. Failed
refreshes may use the previous result for up to one hour with an explicit stale
label and its original measurement timestamp. The existing two-hour freshness
check for positive flow still applies. `tools/flow_sources.py` centralizes source
identifiers, validation and parsing; adding another reviewed station is a catalog
change within this contract. Adding another provider requires an adapter and tests.

Four gaps remain:

- **Arkansas at Salida:** keep the correct seasonal USGS station; no current
  discharge was returned during this check.
- **Shoshone below Corbett:** no suitable maintained source confirmed below the
  diversion. Buffalo Bill upstream and Lovell far downstream are not approved
  replacements.
- **Laramie at Woods Landing:** State Engineer portal metadata identifies a
  current series at 014AWL below Pioneer Canal. Reach suitability and an authorized
  machine-readable feed still need review.
- **Tongue near Ranchester:** portal metadata identifies a current series at
  06298000 near Dayton. This is upstream, so suitability and an authorized feed
  still need review.

The [Wyoming State Engineer](https://seo.wyo.gov/documents-and-data) links to
<https://seoflow.wyo.gov/>. Public search and dataset metadata were readable; the
documented export request returned a No Access page. The app does not use that
export or pretend the metadata is a discharge reading. Exact candidates and next
actions are retained in `remaining-work.json`.

## Four additional Wyoming access-map previews

| Section | Decision |
| --- | --- |
| Bixby → Douglas | Douglas Riverside Park confirmed by the city and WGFD; approximate facility area. |
| Douglas → South Douglas | Reuses the same permanent Douglas access ID and reviewed area. |
| Green River Lake → Roaring Fork | WGFD identifies launch and egress; agency map and imagery corroborate the area. |
| Dubois City Park → Painted Hills | Corrected the park to the town's own facility coordinate; old route mileage withheld. |

The city identifies [Douglas Riverside Park](https://www.cityofdouglas.org/Facilities/Facility/Details/Riverside-Park-22?mobile=ON)
at West Grant Street. The point is inside the facility, not a surveyed ramp.
WGFD's [Green River access map](https://wgfd.wyo.gov/media/27075/download?inline=)
corroborates Roaring Fork and advises experienced floaters, with large-boat and
low-water limitations now retained in the section notes.

The original WGFD Dubois point was roughly 10 km northwest of the actual park.
The [town's facility record](https://www.townofdubois.org/Facilities/Facility/Details/Dubois-Town-Park-15)
and imagery put it beside the river in Dubois. The old candidate is explicitly
rejected in `research/WY/pending-map-points/WY.json`. The corrected point is an
approximate access area; the old 15.9-mile route started at the incorrect point
and is not shown as valid trip distance. New route evidence is still needed.

The three landing identities keep their original stable access IDs. Endpoint
evidence hashes were recalculated from normalized catalog records, and only the
four reviewed sections received new map approvals. These maps add no dotted
route, landing-bank claim or remaining-time estimate.

Montana's 14 held access maps remain held. Reclamation's Clark Canyon material
confirms below-dam access and the Barretts take-out but did not resolve dependable
river-side landing coordinates; reservoir ramps and diversion points must not be
substituted. The recheck is in `research/MT/local-review-20261030/decisions.json`.

## Validation and handoff

- 125 rivers, 342 sections, nine states and 459 permanent access IDs.
- 221 access maps available locally; Wyoming 116/149 and Montana 42/56.
- 59 existing dotted paths unchanged (46 Wyoming, 13 Montana).
- 107 Python tests and 40 JavaScript tests passed, with no skipped tests.
- Catalog and private queue generation checks pass; queue has 970 research items.
- 337 local pages/assets returned HTTP 200.
- Browser checks cover the Reclamation card, all four new map links, and Dubois
  mobile layout. Final map console check reported no errors.
- The 38 checked pilot/Montana source files match the pre-batch checkpoint.

Detailed results are in `validation.json`, with logs and screenshots linked there.
`change-inventory.json` isolates this batch from the pre-existing working changes.
`remaining-work.json` lists the four gauge gaps and all 47 held Montana/Wyoming
access maps. The national readiness files additionally track dotted-path and
timing blockers separately.

```sh
python3 tools/build_catalog.py --check
python3 tools/build_review_queue.py --check
# The existing development GIS environment includes shapely and pyproj.
PYTHONPYCACHEPREFIX=/private/tmp/floateta-pycache \
  /private/tmp/floateta-gis-env/bin/python -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.cjs
python3 tools/audit_gauges.py --base-url http://127.0.0.1:8781 \
  --river north-platte-glendo --river north-platte-gray-reef-casper \
  --river bighorn-river-thermopolis --river shoshone-river-cody \
  --river shoshone-river-willwood --river shoshone-river-corbett \
  --river tongue-river-wy --river laramie-river-woods-landing \
  --river arkansas-river-salida --output /tmp/floateta-nine-gaps-recheck.json
```

The audit intentionally exits nonzero while any of the four gaps remains.
Repeat current-source checks before any eventual publication. Browser testing is
not an on-river GPS or physical-access test.
