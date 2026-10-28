# Colorado — final report v1.1 (2026-10-26, America/Denver)

## Status: research delivered vs. ready for visitors
These are two different labels (full detail in `research/readiness-status.json`).

- **Research delivered:** 78 sections on 26 rivers. That is 10 catalog rivers with 25 sections, plus 16 draft rivers with 53 draft sections. Every one has sources, evidence and open questions recorded.
- **Importable:** 25 catalog sections pass the builder and importer on an isolated copy (`validation-results.txt`, PASS).
- **Ready for visitors:** 11 of the 25 catalog sections. Each one imports, both endpoints are verified and passed the imagery check, all known restrictions are attached, permission is resolved and no app feature is missing. They are:
  - pumphouse-to-radium, state-bridge-to-two-bridges, two-bridges-to-catamount and catamount-to-pinball
  - chukar-to-gunnison-forks and escalante-to-whitewater
  - south-beach-to-duffy\*, duffy-to-juniper\* and sunbeam-to-east-cross-mountain\*
  - west-cross-mountain-to-deerlodge† and stone-bridge-to-rincon

  \* The CPW Yampa low-water advisory is still posted; show it prominently.
  † West Cross Mountain is flagged because sources conflict over who manages the facility. Location and boating access are confirmed.
- **Rivers:** 3 fully ready (gunnison-river-gorge, yampa-river-maybell, arkansas-river-salida). 5 partly ready. 2 not ready: colorado-river-ruby-horsethief, which needs the cross-state feature, and yampa-river-hayden. 14 draft-only river ids remain.
- **Not ready (14 catalog sections). Some have more than one reason:**
  - All 14 have at least one endpoint that is not verified. The causes are no official coordinate (Horse Creek, Loudy Simpson, Confluence Park), area-only features (Cottonwood Island, Lyons Gulch, Bridgeport, Headquarters), permission (Rancho del Rio, Yampa SWA) and Utah endpoints (Westwater, Split Mountain).
  - 3 of them also have unresolved permission.
  - 2 of them (loma-to-westwater and yampa-canyon-deerlodge-to-split-mountain) also need the proposed cross-state lookup.

## Counts (v1 → v1.1)
| | v1 | v1.1 |
|---|---|---|
| Catalog rivers / sections | 9 / 24 | 10 / 25 |
| Map exact / approximate / pending | 10 / 4 / 10 | 11 / 4 / 10 |
| Registry verified / access-verified / pending | 22 / 3 / 7 | 24 / 3 / 7 |
| Audited rivers verified | 2 / 9 | 3 / 10 |
| Draft rivers / draft sections | 16 / 55 | 16 / 53 |
| Restrictions / sections with current restriction | 12 / 13 | 18 / 15 |
| Unresolved permission | 3 | 3 |
| Guide ranges / calibrated estimates | 12 / 0 | 12 / 0 |
| Review items | 24 | 27 |
| Agency pins imagery-checked | 0 | 48 (36 pass, 3 ramp-head, 7 flag, 2 downgrade) |
| Ready for visitors | (not labelled) | 11 |

## Timing
- Unchanged: 3 independent sources, 13 rows, 0 trip observations, 0 calibrations.
- stone-bridge-to-rincon has no guide range, so no trip time is shown.
- Gauge 07091200 is seasonal (no values on 2026-10-26), so live estimates are hidden. Access info is unaffected.

## Blocked or not used
- The City of Durango Animas PDF is still not used (HTTP 202, 225 bytes).
- NHDPlus HR now answered. Earlier 502/504 errors were retried, and 0 errors remained.
- Nothing needed an agency contact. Every permit question was answered from public NPS, CPW and Recreation.gov pages, and the conflicts are recorded rather than resolved.

See `research/review-queue.json` (27 items) and `CLAUDE_INSTRUCTIONS.md` → Next work.
