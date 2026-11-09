#!/usr/bin/env python3
"""Stage an agency river-course candidate in research. Never approve or publish."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.agency_courses import METHOD, nearest_position, registered_source, signature, source_chain, trim_chain
from tools.build_catalog import ROOT, build
from tools.route_catalog import geometry_checks, safe_file, validate


def stage_record(root, river_id, section_id, adapter_id, evidence_file, parts, clip=None):
    catalog = build(root)
    river = next((r for r in catalog['rivers'] if r['id'] == river_id), None)
    if river is None:
        raise ValueError('Unknown river')
    section = next((s for s in river['sections'] if s['id'] == section_id), None)
    if section is None:
        raise ValueError('Unknown section')
    if not re.fullmatch(r'[A-Z]{2}-[a-z0-9-]+', adapter_id):
        raise ValueError('Invalid agency course source ID')
    path = root / 'catalog/routes/agency_sources' / (adapter_id + '.json')
    raw = path.read_bytes()
    config = json.loads(raw)
    evidence = safe_file(root, evidence_file, 'research')
    record = dict(version=1, state=river['state'], riverId=river_id, sectionId=section_id,
        status='candidate', scope='river-course-overview', catalogMiles=section['miles'],
        source=dict(name=config.get('name') or config['agency'], url=config['url'], checkedOn=date.today().isoformat(),
            adapterId=adapter_id, adapterSha256=hashlib.sha256(raw).hexdigest(),
            evidenceFile=evidence_file, sha256=hashlib.sha256(evidence.read_bytes()).hexdigest()),
        features=dict(display=False, landOverlay=False, distanceEstimate=False, remainingTime=False),
        note='Unreviewed source-derived course. Access connections, obstacles, imagery and source limitations still require review.')
    registered_source(record, root)
    for end in ('putIn', 'takeOut'):
        coords = section.get(end + 'Coords')
        if not coords:
            raise ValueError('Both endpoints need sourced access coordinates before course staging')
        record[end] = dict(name=section[end], lat=coords['lat'], lon=coords['lon'])
    payload = json.loads(evidence.read_text())
    # The chosen source parts must all name one water trail; never select an
    # arbitrary nearby river or hide disagreements by taking the first match.
    ids = {p['featureId'] for p in parts}
    streams = {str(f['attributes'][config['streamField']]) for f in payload.get('features', [])
               if str(f['attributes'][config['featureIdField']]) in ids}
    if len(streams) != 1:
        raise ValueError('Selected source parts must identify one water trail')
    record['source']['streamId'] = next(iter(streams))
    chain = source_chain(payload, config, record['source']['streamId'], parts)
    if clip is None:
        clip = {side: nearest_position(chain, record[end]) for side, end in [('start', 'putIn'), ('end', 'takeOut')]}
    record['direction'] = dict(method=METHOD, parts=parts, clip=clip, tripEvidenceSha256=signature(section.get('distanceEvidence', {})))
    record['geometry'] = trim_chain(chain, clip)
    metrics, issues = geometry_checks(record)
    record['checks'] = dict(metrics=metrics, issues=issues)
    validate(record, catalog, root)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--river', required=True)
    parser.add_argument('--section', required=True)
    parser.add_argument('--adapter', required=True)
    parser.add_argument('--evidence', required=True, help='Immutable response path under research/')
    parser.add_argument('--parts', required=True, type=Path, help='JSON array of explicit featureId, pathIndex and reverse values')
    parser.add_argument('--clip', type=Path, help='Optional explicit source segment/fraction trims; otherwise suggested near current access coordinates')
    parser.add_argument('--output', required=True, type=Path, help='New JSON file under research/; never a catalog or public path')
    args = parser.parse_args()
    try:
        output = (ROOT / args.output).resolve()
        if not output.is_relative_to((ROOT / 'research').resolve()) or output.suffix != '.json' or output.exists():
            raise ValueError('Output must be a new JSON file under research/')
        record = stage_record(ROOT, args.river, args.section, args.adapter, args.evidence,
            json.loads(args.parts.read_text()), json.loads(args.clip.read_text()) if args.clip else None)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(json.dumps(dict(candidate=str(output.relative_to(ROOT)), approved=False, features=record['features'], checks=record['checks'])))


if __name__ == '__main__':
    main()
