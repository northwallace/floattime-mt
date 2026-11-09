#!/usr/bin/env python3
"""Check whether a section has newer USGS hydrography; research only.

Never approves a path, changes access precision, or treats a service refresh as
a survey date. Uses an explicit GNIS ID and complete, twice-checked inventories.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_catalog import build
from tools.fetch_agency_layer import get

SERVICE = 'https://3dhp.nationalmap.gov/arcgis/rest/services/usgs_3dhp_all/FeatureServer'
FLOW_FIELDS = ['id3dhp', 'featuredate', 'mainstemid', 'gnisid', 'gnisidlabel',
               'featuretype', 'featuretypelabel', 'flowdirection', 'workunitid']
UNIT_FIELDS = ['ptsid', 'workunitid', 'edhspecversion', 'edhschemaversion', 'workunit_edh']


def bounded_inventory(layer, fields, bounds, where, request=get):
    """Read attributes, not a navigation network; fail closed on partial data."""
    url = SERVICE + '/' + str(layer)
    metadata = request(url, {})
    available = {f['name'] for f in metadata.get('fields', [])}
    oid = metadata.get('objectIdField') or next(
        (f['name'] for f in metadata.get('fields', []) if f.get('type') == 'esriFieldTypeOID'), None)
    if not oid or not set(fields).issubset(available):
        raise ValueError('USGS layer schema changed; review field mapping')
    scope = dict(where=where, geometry=','.join(map(str, bounds)),
                 geometryType='esriGeometryEnvelope', inSR=4326,
                 spatialRel='esriSpatialRelIntersects')

    def inventory():
        data = request(url + '/query', {**scope, 'returnIdsOnly': 'true'})
        ids = data.get('objectIds')
        # ArcGIS can represent a genuinely empty selection as explicit null.
        # Confirm it independently instead of treating missing/failed data as
        # evidence that no newer hydrography exists.
        if ('objectIds' in data and ids is None and not data.get('error')
                and not data.get('exceededTransferLimit')):
            count = request(url + '/query', {**scope, 'returnCountOnly': 'true'})
            if (not count.get('error') and not count.get('exceededTransferLimit')
                    and type(count.get('count')) is int and count['count'] == 0):
                ids = []
        if (data.get('error') or data.get('exceededTransferLimit') or not isinstance(ids, list)
                or any(type(i) is not int for i in ids) or len(ids) != len(set(ids)) or len(ids) > 10000):
            raise ValueError('USGS inventory incomplete, duplicated or too broad; choose a smaller section')
        return sorted(ids)

    ids = inventory()
    allowlist = [oid, *fields]
    rows = {}
    for offset in range(0, len(ids), 200):
        batch = ids[offset:offset + 200]
        data = request(url + '/query', dict(objectIds=','.join(map(str, batch)),
                       outFields=','.join(allowlist), returnGeometry='false'))
        if data.get('error') or data.get('exceededTransferLimit') or not isinstance(data.get('features'), list):
            raise ValueError('USGS feature response incomplete')
        received = set()
        for feature in data['features']:
            attrs = feature.get('attributes', {})
            identifier = attrs.get(oid)
            if identifier not in batch or identifier in received or identifier in rows:
                raise ValueError('Unexpected or duplicate USGS feature')
            if not set(allowlist).issubset(attrs):
                raise ValueError('USGS feature omitted requested attributes')
            received.add(identifier)
            rows[identifier] = {k: attrs[k] for k in allowlist}
        if received != set(batch):
            raise ValueError('USGS omitted requested features')
    if ids != inventory():
        raise ValueError('USGS inventory changed during download; retry')
    return dict(url=url, query=scope, objectIdField=oid,
                metadata={k: metadata[k] for k in ('name', 'description', 'copyrightText', 'editingInfo') if k in metadata},
                features=[dict(attributes=rows[i]) for i in ids])


def summarize(flowlines, workunits, gnis_id):
    units = {str(f['attributes'].get('workunitid', '')).strip()
             for f in workunits['features'] if f['attributes'].get('workunitid')}
    counts = Counter()
    names, mainstems, loaded_dates = set(), set(), set()
    for feature in flowlines['features']:
        a = feature['attributes']
        if a.get('gnisid') != gnis_id:
            raise ValueError('USGS returned a different GNIS river identity')
        unit = str(a.get('workunitid') or '').strip()
        if unit.upper() == 'NHD':
            counts['legacyNhd'] += 1
        elif unit and unit in units:
            counts['associatedEdhWorkunit'] += 1
        elif unit:
            counts['unmatchedWorkunit'] += 1
        else:
            counts['unknownProvenance'] += 1
        if a.get('gnisidlabel'): names.add(a['gnisidlabel'])
        if a.get('mainstemid'): mainstems.add(a['mainstemid'])
        if a.get('featuredate') is not None: loaded_dates.add(a['featuredate'])
    total = sum(counts.values())
    if not total:
        status = 'no-matching-flowlines'
    elif counts['legacyNhd'] == total:
        status = 'legacy-only'
    elif counts['associatedEdhWorkunit']:
        status = 'edh-data-to-inspect'
    else:
        status = 'provenance-needs-review'
    return dict(status=status, flowlines=total, provenanceCounts=dict(counts),
                intersectingEdhWorkunits=sorted(units), riverNames=sorted(names), mainstemIds=sorted(mainstems),
                featureLoadedTimestamps=sorted(loaded_dates), approved=False,
                note='Coverage check only. Feature dates are database load dates, not imagery or survey dates. '
                     'EDH workunits intersecting the search envelope do not prove complete route coverage, '
                     'accurate landing connections, current channel alignment or navigability.')


def section_bounds(section, route=None, margin=.02):
    points = []
    for side in ('putIn', 'takeOut'):
        p = section.get(side + 'Coords')
        if not p: raise ValueError('Section needs sourced endpoint coordinates')
        points.append([p['lon'], p['lat']])
    if route is not None:
        if route.get('sectionId') != section['id'] or route.get('geometry', {}).get('type') != 'LineString':
            raise ValueError('Source course does not match the section')
        points += route['geometry']['coordinates']
    if not points or any(not isinstance(p, (list, tuple)) or len(p) != 2 or
                         any(type(v) not in (int, float) or not math.isfinite(v) for v in p) or
                         not -180 <= p[0] <= 180 or not -85 <= p[1] <= 85 for p in points):
        raise ValueError('Invalid source coordinates')
    return [max(-180, min(p[0] for p in points) - margin), max(-85, min(p[1] for p in points) - margin),
            min(180, max(p[0] for p in points) + margin), min(85, max(p[1] for p in points) + margin)]


def run(river_id, section_id, gnis_id, output, route_path=None, *, root=ROOT, request=get):
    output = output.resolve()
    if output.exists() or not output.is_relative_to((root / 'research').resolve()):
        raise ValueError('Choose a new output folder under research/')
    if type(gnis_id) is not int or gnis_id <= 0:
        raise ValueError('An explicit positive GNIS river ID is required')
    catalog = build(root)
    river = next((r for r in catalog['rivers'] if r['id'] == river_id), None)
    if not river: raise ValueError('Unknown river')
    section = next((s for s in river['sections'] if s['id'] == section_id), None)
    if not section: raise ValueError('Unknown section')
    course = None
    if route_path:
        route_path = route_path.resolve()
        if not route_path.is_relative_to((root / 'research').resolve()):
            raise ValueError('Comparison course must be saved research evidence')
        course = json.loads(route_path.read_text())
        if course.get('riverId') != river_id: raise ValueError('Source course belongs to a different river')
    bounds = section_bounds(section, course)
    flowlines = bounded_inventory(50, FLOW_FIELDS, bounds, f'gnisid={gnis_id}', request)
    workunits = bounded_inventory(90, UNIT_FIELDS, bounds, '1=1', request)
    report = dict(version=1, localOnly=True, checkedAt=datetime.now(timezone.utc).isoformat(),
                  riverId=river_id, sectionId=section_id, gnisId=gnis_id, bounds=bounds,
                  envelopeBasis='saved-course-and-accesses' if course else 'access-endpoints-only',
                  result=summarize(flowlines, workunits, gnis_id),
                  sourceDocumentation='https://www.usgs.gov/3d-hydrography-program/access-3dhp-data-products')
    # No catalog/public mutation. Materialize only after every inventory passed.
    output.mkdir(parents=True)
    evidence = []
    for name, data in [('flowlines', flowlines), ('workunits', workunits)]:
        content = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()
        path = output / (name + '.json')
        path.write_bytes(content)
        evidence.append(dict(file=str(path.relative_to(root)), sha256=hashlib.sha256(content).hexdigest()))
    if route_path:
        evidence.append(dict(file=str(route_path.relative_to(root)), sha256=hashlib.sha256(route_path.read_bytes()).hexdigest()))
    report['evidence'] = evidence
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--river', required=True)
    parser.add_argument('--section', required=True)
    parser.add_argument('--gnis-id', required=True, type=int)
    parser.add_argument('--course', type=Path, help='Optional source course JSON under research/ for a better search envelope')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = run(args.river, args.section, args.gnis_id, args.output, args.course)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(json.dumps(result['result'], indent=2))
