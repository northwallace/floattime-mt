# Local integration completed — 2026-10-26

Preview: http://127.0.0.1:8777/?state=UT&river=green-river-labyrinth&craft=raft#calculator

No deployment or Git push was performed. A source backup is in /Users/home/Documents/Codex/FloatETA-backup-before-state-support-20261026.

## Results

- Catalog: 90 rivers, 162 sections, six states.
- Existing Montana: 30 section maps.
- Washington: 12 section maps (2 approximate).
- Utah: 13 section maps (3 approximate).
- Arizona: 6 section maps (4 approximate).
- Ten sections display sourced guide times; 36 incoming rivers have unavailable live calibration rather than placeholder numbers.
- Per-section map eligibility and optional independently sourced bank metadata.
- 20 Python tests + 17 JavaScript tests passed.
- Actual local proxy requests to USGS 06041000, 09234500 and 09506000 returned HTTP 200 with positive recent readings.
- Browser checked Utah approximate map, Arizona guide ranges and existing Montana modeled times.
- Export reconstructed in a fresh temporary directory; shared builder --check passed.

## Evidence and handoff

- Research snapshots: research/WA, research/UT, research/AZ (raw imagery/cache retained locally and ignored by Git).
- Detailed data decisions: research/integration-review-20261026.json.
- Current contract: catalog/RESEARCH_FORMAT.md.
- Assistant reference: /Users/home/Documents/Codex/FloatETA-research-reference-20261026.zip.
- Revised assistant brief: /Users/home/Documents/Codex/FloatETA-research-review-2026-10-26/ASSISTANT-BRIEF.md.

## Limits

An access map does not certify current opening, boating suitability, or a navigable channel. No river-route line was added. Critical/unresolved locations such as Husum, Clay Hills and Blue Point remain pending. New guide times are not treated as flow-calibrated speeds. Six Washington models retained from the research baseline are not newly certified by this integration. Legacy Montana/Idaho/Oregon models remain compatible and have not all been recalibrated.

## Sources checked for corrections/guidance

- https://www.blm.gov/sites/default/files/documents/files/floating_the_green_river_brochure.pdf — Red Creek Rapids Class III–IV; Section B rating corrected.
- https://www.blm.gov/visit/labyrinth-canyon-river — minimum trip-planning allowance.
- https://arizona-content.usedirect.com/storage1/gallery/downloads/VERI_Paddle_Map_3.pdf — section guide categories and times.
- https://redcanyonlodge.com/flaming-gorge-rafting/ — approximate visitor guidance for Section A, not model calibration.
