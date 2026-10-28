# Changelog — Float ETA Colorado

## v1.1 — 2026-10-26
Focused fixes from North's v1 review. Built in a copy (`floateta-colorado-v1.1`); v1 is unchanged. Public data only; no agency was contacted, nothing was published, deployed or bought.

- **Deerlodge / Dinosaur permits (CO-RES-013, CO-RES-014, refreshed CO-RES-009).**
  - West Cross Mountain → Deerlodge now carries the NPS rule: "A permit is required to boat into the monument from above Gates of Lodore or Deerlodge". Day floaters taking out at Deerlodge need the free one-day **play permit** ("One play permit per day… arrive after 2 pm").
  - The FAQ and the 2025 guide disagree on who issues it and where (on-site rangers vs. the river office). The record says so and does not pick one.
  - CO-RES-009 (Yampa Canyon) is refreshed from Recreation.gov 250014: lottery Dec 1–Jan 31, results Feb 12 2027, $15 application + $185 fee, high-use season May 10–Jul 10 2027.
  - West Cross Mountain's access text now reflects a source conflict. CPW GIS says it is a BLM ramp managed by CPW. The CPW park page says "Boat Ramp: None" and that NPS manages it. Imagery shows a dirt road to the water and no built ramp, so it is published as "Boat launch". The grade stays verified with a flag (CO-RQ-024).
- **Cross-state endpoints (proposed app feature).** New `research/cross-state-references.json` records the exact UT registry entries:
  - Westwater Ranger Station Boat Ramp (BLM 69678) would unlock loma-to-westwater and the colorado-river-ruby-horsethief audit.
  - Split Mountain Boat Ramp (NPS POI 4808) would unlock yampa-canyon-deerlodge-to-split-mountain and the yampa-river-dinosaur audit.
  - The Utah points were **not** copied into CO.json.
- **Arkansas re-assessment.**
  - A seasonal gauge now hides only live estimates; it no longer blocks access info. The new blocker code `live-estimates-hidden` is informational, and sections carry a `liveEstimates` field.
  - Promoted one section: new river `arkansas-river-salida` with **stone-bridge-to-rincon**. It is 19.5 mi (CPW AHRA safety map), Class II–III, and covers AW 4348 + 6769.
  - Both CPW ramps passed the imagery check and are within 34 m of the NLDI/HR centreline. Gauge 07091200 (Nathrop) is attached with live estimates hidden.
  - New restrictions: the AHRA pass (CO-RES-015), Salida low-head dam (016), the Stone Bridge portage above 4,000 cfs (017) and Salida Whitewater Park congestion (018).
  - The rest of the Arkansas stays draft with reasons (`exact-location`, `route-geometry`, `live-estimates-hidden`). Salida East was downgraded by the imagery check.
- **Targeted pin review.**
  - All 48 agency pins were checked against Esri World Imagery z18 and USGS NHDPlus HR (now reachable). Images are in `research/raw/imagery/` and metrics in `research/geo-checks-hr-CO.json`.
  - Verdicts are recorded in `research/access-grades/CO.json`: 36 pass, 3 pass-ramp-head, 7 flag and 2 downgrade.
  - The 2 downgrades (Salida East, Wingo) are both research points, so no catalog point lost its grade.
- **Readiness labels.** New `research/readiness-status.json` separates "research delivered" from "ready for visitors" for every section and river.
- **Counts (v1 → v1.1):**
  - Catalog: 9→10 rivers and 24→25 sections.
  - Map: exact 10→11, approximate 4, pending 10.
  - Registry: verified 22→24, access-verified 3, pending 7.
  - Audited rivers verified: 2/9→3/10.
  - Draft sections: 55→53, because the two AW reaches are now in the catalog.
  - Restrictions: 12→18, and sections with a current restriction 13→15.
  - Review items: 24→27.
  - Ready for visitors: 11 of 25 catalog sections.
- Validation: PASS (0 failures).

## v1 — 2026-10-26
First Colorado package. This is new work: no earlier Colorado package existed under /workspace/colorado.

- **Reference used:** the 20261026 reference, `ref1026/`, extracted from `FloatETA-research-reference-20261026.zip`, which was copied from North's Mac. It was used **instead of** the Utah package's `reference/` folder, as ASSISTANT-BRIEF.md §1 requires.
  - Builder `tools/build_catalog.py` sha256 b620933a6a48ed148461c37d5448bd4075549a6b2cce11413a966b4a0f57dd6d.
  - It was not modified, and validation ran only on temp copies.
- **Catalog:** 9 rivers and 24 sections, all with timing `unavailable`. 12 sections have BLM/NPS `guideTimes`.
- **Map registry:** CO.json, version 2, with 22 verified, 3 access-verified and 7 pending points. 2 audited rivers are verified.
- **Drafts:** 16 draft rivers and 55 draft sections, plus an inventory of 270 AW reaches.
- **Geometry:** the NHD MapServer/6 and NHDPlus_HR query endpoints timed out repeatedly, so geometry checks use USGS NLDI (NHDPlus V2). This is logged as CO-RQ-020.
- **Decisions:**
  - Lake Fork of the Gunnison (red-bridge-to-gateview) was moved to drafts. AW gives 4.9 mi, but the NLDI path between the BLM points is 1.07 mi, and permission at both BLM sites is still unresolved.
  - juniper-to-maybell-bridge was moved to drafts because CPW gives 13 mi and NLDI gives 6.0 mi (CO-PRO-006).
  - pumphouse-to-radium keeps the guide's stated 4 mi. Guide river miles give 4.5 and NLDI gives 5.0 (CO-PRO-005).
  - chukar-to-gunnison-forks mileage now comes from the BLM brochure's river-mile table (14 mi), not the "14-mile" jeep-loop text.
  - Rancho del Rio (private fee site), Lake Fork BLM sites and the Yampa River SWA ramp stay pending because permission is unresolved.
  - Westwater and Split Mountain stay pending in CO, because the app looks up points by the river's state (CO-PRO-001/002).
  - The CPW Yampa River State Park low-water advisory (as of 6-23-2026, still posted on 2026-10-26) is added to the notes for the Hayden, Craig and Maybell sections.
  - The City of Durango Animas access PDF (HTTP 202, 225 bytes, tourism host) was not used.
