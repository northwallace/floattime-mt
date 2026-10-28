#!/usr/bin/env python3
"""Check all mapped sections for impossible mileage; never edits or certifies pins."""
import json
from collections import Counter
from build_catalog import build, distance_conflict, straight_line_miles

def audit(catalog):
    flags=[]
    for river in catalog['rivers']:
        for section in river['sections']:
            if not section.get('mapPilot'): continue
            direct=straight_line_miles(section['putInCoords'],section['takeOutCoords'])
            if distance_conflict(section):
                flags.append({'river':river['id'],'section':section['id'],'listedMiles':section['miles'],'straightLineMiles':round(direct,2),'acknowledged':bool(section.get('distanceReview'))})
    return flags

if __name__=='__main__':
    c=build();flags=audit(c)
    print(json.dumps({'coverage':{st['id']:dict(Counter(s.get('mapPrecision','unavailable') for r in c['rivers'] if r['state']==st['id'] for s in r['sections'])) for st in c['states']},'distanceFlags':flags},indent=2))
    raise SystemExit(1 if any(not f['acknowledged'] for f in flags) else 0)
