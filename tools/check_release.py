#!/usr/bin/env python3
"""Validate and inventory a local release candidate. Never publish or change approvals."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.build_catalog import build, ROOT
from tools.catalog_assets import write_or_check
from tools.route_catalog import write_or_check as check_routes
from tools.flow_sources import gauge_relationship, supports_live_timing


def review(root=ROOT):
    catalog = build(root)
    expected = json.dumps(catalog, indent=2, ensure_ascii=False) + '\n'
    if (root/'public/catalog.json').read_text() != expected:
        raise ValueError('Public catalog is stale; run tools/build_catalog.py')
    write_or_check(root, catalog, check=True)
    check_routes(root, catalog, check=True)
    states = {}; held = []; inspection = []
    for state in catalog['states']:
        rivers = [r for r in catalog['rivers'] if r['state'] == state['id']]
        sections = [(r, s) for r in rivers for s in r['sections']]
        states[state['id']] = {'rivers': len(rivers), 'sections': len(sections),
            'accessMaps': sum(bool(s.get('mapReleased')) for _, s in sections),
            'inspectionOnlyMaps': sum(bool(s.get('mapReleased') and s.get('distanceReview')) for _, s in sections),
            'heldMaps': sum(not s.get('mapReleased') for _, s in sections),
            'sectionsWithPublishedGuideTimes': sum(bool(s.get('guideTimes') and not s.get('accessReview') and not s.get('distanceReview')) for _, s in sections)}
        for river, section in sections:
            row = {'river': river['id'], 'section': section['id'], 'state': state['id']}
            if section.get('mapReleased'):
                if section.get('accessReview') or section.get('mapReleaseNote'):
                    raise ValueError('Unreviewed access map in release: ' + str(row))
                if not all(section.get(k, {}).get('status') in ('verified','access-verified') for k in ('putInAccess','takeOutAccess')):
                    raise ValueError('Map lacks reviewed endpoints: ' + str(row))
                if section.get('distanceReview'):
                    inspection.append({**row,'reason':section['distanceReview']})
            else:
                held.append({**row,'reason':section.get('mapPendingReason') or section.get('mapReleaseNote') or 'No reviewed map yet'})
    return {'checkedAt':datetime.now(timezone.utc).isoformat(), 'localOnly':True,
        'catalogRivers':len(catalog['rivers']), 'states':states,
        'gaugeRelationships':dict(Counter(gauge_relationship(r) for r in catalog['rivers'])),
        'riversWithTimingModel':sum(supports_live_timing(r) for r in catalog['rivers']),
        'note':'Map availability, current discharge and timing-model support are separate. This check makes no network requests and does not certify current access conditions.',
        'inspectionOnlyMaps':inspection,'heldMaps':held,
        'deploymentChecksStillRequired':['Confirm Render production basemap credential and persistent data mount without changing the hosting plan.','After an authorized deployment, verify both HTTPS domains, a satellite map, a current gauge, a withheld map, and a private correction submission.','Ordinary GPS time remaining stays disabled; the existing Greycliff pilot is unchanged and still needs a phone field test.']}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=review();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(f"Release checks passed: {result['catalogRivers']} rivers, {sum(s['accessMaps'] for s in result['states'].values())} access maps; nothing published.")
