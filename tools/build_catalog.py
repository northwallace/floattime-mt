#!/usr/bin/env python3
"""Validate source records and build the shared browser/SEO catalog. No packages required."""
import argparse
import json
import math
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import re
try:
    from tools.route_catalog import build_outputs, write_or_check
    from tools.map_review import fingerprint
    from tools.catalog_assets import write_or_check as write_catalog_assets
    from tools.flow_sources import validate_source, validate_gauge
except ModuleNotFoundError:
    from route_catalog import build_outputs, write_or_check
    from map_review import fingerprint
    from catalog_assets import write_or_check as write_catalog_assets
    from flow_sources import validate_source, validate_gauge

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')

def require(ok, message):
    if not ok:
        raise ValueError(message)

def straight_line_miles(a, b):
    x, y = math.radians(a['lat']), math.radians(b['lat'])
    dl = math.radians(b['lon'] - a['lon'])
    return 7917.6 * math.asin(min(1, math.sqrt(math.sin((y-x)/2)**2 + math.cos(x)*math.cos(y)*math.sin(dl/2)**2)))

def distance_conflict(section):
    if not section.get('mapPilot'):
        return False
    direct = straight_line_miles(section['putInCoords'], section['takeOutCoords'])
    return direct > section['miles'] * 1.05 or direct < .02

def validate_distance_evidence(section, prefix):
    evidence = section.get('distanceEvidence')
    if evidence is None:
        return
    require(isinstance(evidence, dict) and evidence.get('method') in ('agency-mile-markers', 'published-guide-miles', 'published-trip-length'), prefix + 'Invalid distance evidence method')
    for field in ('sourceName', 'sourceUrl', 'checkedOn', 'streamId', 'note'):
        require(isinstance(evidence.get(field), str) and evidence[field].strip(), prefix + 'Distance evidence ' + field + ' required')
    require(evidence['sourceUrl'].startswith('https://'), prefix + 'Distance source must use HTTPS')
    try: date.fromisoformat(evidence['checkedOn'])
    except ValueError: raise ValueError(prefix + 'Invalid distance evidence date')
    if evidence['method'] == 'published-trip-length':
        # Some agencies publish a whole-trip distance, not endpoint mile markers.
        # Preserve that distinction rather than inventing two river-mile readings.
        miles = evidence.get('miles')
        require(type(miles) in (int, float) and math.isfinite(miles) and miles > 0 and abs(section['miles'] - miles) < .00001, prefix + 'Mileage disagrees with published trip length')
        for end in ('putIn', 'takeOut'):
            record = evidence.get(end)
            require(isinstance(record, dict) and record.get('name') == section[end], prefix + 'Distance evidence endpoint name changed')
            require(isinstance(record.get('sourceLocation'), str) and record['sourceLocation'].strip(), prefix + 'Published trip source location required')
        return
    if evidence['method'] == 'published-guide-miles':
        # Named access sites in a published guide are distance evidence, not GPS
        # measurements or confirmation of an exact ramp location.
        require(evidence.get('measureDirection') in ('increases-downstream', 'decreases-downstream'), prefix + 'Guide mile direction required')
        for end in ('putIn', 'takeOut'):
            record = evidence.get(end)
            require(isinstance(record, dict) and record.get('name') == section[end], prefix + 'Distance evidence endpoint name changed')
            mile = record.get('riverMile')
            require(type(mile) in (int, float) and math.isfinite(mile) and 0 <= mile <= 10000, prefix + 'Invalid guide river mile')
            require(isinstance(record.get('sourceLocation'), str) and record['sourceLocation'].strip(), prefix + 'Guide source location required')
        delta = evidence['takeOut']['riverMile'] - evidence['putIn']['riverMile']
        if evidence['measureDirection'] == 'decreases-downstream': delta = -delta
        require(delta > 0 and abs(section['miles'] - round(delta, 1)) < .00001, prefix + 'Mileage disagrees with distance evidence')
        return
    for end in ('putIn', 'takeOut'):
        record = evidence.get(end)
        require(isinstance(record, dict) and record.get('name') == section[end], prefix + 'Distance evidence endpoint name changed')
        for key, lo, hi in [('lat', -90, 90), ('lon', -180, 180), ('riverMile', 0, 10000), ('offsetMeters', 0, 200)]:
            value = record.get(key)
            require(type(value) in (int, float) and math.isfinite(value) and lo <= value <= hi, prefix + 'Invalid distance evidence ' + key)
        require(type(record.get('markerId')) is int and record['markerId'] >= 0, prefix + 'Distance marker ID required')
        coords = section.get(end + 'Coords')
        if coords:
            require(all(abs(coords[k] - record[k]) < .000001 for k in ('lat', 'lon')), prefix + 'Access coordinates changed; recheck distance evidence')
    delta = evidence['putIn']['riverMile'] - evidence['takeOut']['riverMile']
    require(delta > 0 and abs(section['miles'] - round(delta, 1)) < .00001, prefix + 'Mileage disagrees with distance evidence')

def build(root=ROOT):
    settings = json.loads((root / 'catalog/settings.json').read_text())
    states = settings['states']
    codes, slugs = set(), set()
    for st in states:
        require(re.fullmatch('[A-Z]{2}', st['id']) and st['id'] not in codes, 'Invalid/duplicate state ID')
        require(SLUG.fullmatch(st['slug']) and st['slug'] not in slugs, 'Invalid/duplicate state slug')
        require(st['name'] and st['agency'] and st['agencyUrl'].startswith('https://'), 'State metadata missing')
        if 'permitNotice' in st or 'permitUrl' in st:
            require(isinstance(st.get('permitNotice'), str) and st['permitNotice'].strip(), 'State permit notice missing')
            require(isinstance(st.get('permitUrl'), str) and st['permitUrl'].startswith('https://'), 'State permit URL missing')
        codes.add(st['id']); slugs.add(st['slug'])
    release = settings.get('mapRelease', {'states': [], 'reviewedRoutes': False})
    require(isinstance(release, dict) and set(release) == {'states', 'reviewedRoutes'}, 'Invalid map release configuration')
    require(isinstance(release['states'], list) and all(isinstance(code, str) and code in codes for code in release['states']), 'Unknown map release state')
    require(len(set(release['states'])) == len(release['states']) and type(release['reviewedRoutes']) is bool, 'Invalid map release flags')
    review_required = settings.get('mapReviewRequiredStates', [])
    require(isinstance(review_required, list) and all(code in codes for code in review_required), 'Invalid map review states')
    map_reviews = {}
    for code in review_required:
        file = root / f'catalog/map_reviews/{code}.json'
        if file.exists():
            review = json.loads(file.read_text())
            require(review.get('state') == code and review.get('version') == 1 and isinstance(review.get('sections'), dict), 'Invalid map review registry')
            for key, record in review['sections'].items():
                require(record.get('status') in ('reviewed', 'hold'), 'Invalid section map review')
                require(isinstance(record.get('note'), str) and record['note'].strip(), 'Map review note required')
                if record['status'] == 'reviewed':
                    require(isinstance(record.get('fingerprint'), str) and re.fullmatch('[a-f0-9]{64}', record['fingerprint']), 'Map review fingerprint required')
                    require(date.fromisoformat(record['checkedOn']) <= date.today(), 'Invalid map review date')
            map_reviews[code] = review['sections']
    craft_ids = set()
    for c in settings['craft']:
        require(SLUG.fullmatch(c['id']) and c['id'] not in craft_ids and c['label'], 'Invalid/duplicate craft')
        require(isinstance(c['mult'], (int, float)) and 0 < c['mult'] <= 3, 'Invalid craft multiplier')
        craft_ids.add(c['id'])
    require(bool(craft_ids), 'At least one craft is required')
    map_points = {}
    map_audits = {}
    for path in sorted((root / 'catalog/map_points').glob('*.json')):
        payload = json.loads(path.read_text())
        prefix = path.name + ': '
        require(path.stem in codes and payload.get('state') == path.stem, prefix + 'State must match filename and settings')
        require(payload.get('version') == 2 and isinstance(payload.get('points'), dict), prefix + 'Invalid point registry')
        audits = payload.get('auditedRivers')
        require(isinstance(audits, dict), prefix + 'auditedRivers must be an object')
        for river_id, audit in audits.items():
            require(SLUG.fullmatch(river_id), prefix + 'Invalid audited river ID')
            require(isinstance(audit, dict) and audit.get('status') in ('verified', 'pending'), prefix + river_id + ' audit status must be verified or pending')
            require(isinstance(audit.get('note'), str) and audit['note'].strip(), prefix + river_id + ' audit note required')
        map_audits[path.stem] = audits
        points = {}
        for label, record in payload['points'].items():
            require(isinstance(label, str) and label.strip(), prefix + 'Point names must be non-empty strings')
            require(isinstance(record, dict), prefix + label + ' must be an object')
            require(record.get('status') in ('verified', 'access-verified', 'pending'), prefix + label + ' invalid access status')
            require(isinstance(record.get('note'), str) and record['note'].strip(), prefix + label + ' note required')
            if record['status'] == 'pending':
                require('lat' not in record and 'lon' not in record, prefix + label + ' pending points cannot publish coordinates')
                points[label] = {'status': 'pending', 'note': record['note']}
                continue
            if record['status'] == 'access-verified':
                require('lat' not in record and 'lon' not in record, prefix + label + ' approximate access cannot contain exact pin coordinates')
                center = record.get('areaCenter', {})
                require(isinstance(center, dict) and isinstance(center.get('feature'), str) and center['feature'].strip(), prefix + label + ' areaCenter must identify the facility feature')
                for axis, low, high in [('lat', -90, 90), ('lon', -180, 180)]:
                    value = center.get(axis)
                    require(type(value) in (int, float) and math.isfinite(value) and low <= value <= high, prefix + label + ' invalid areaCenter ' + axis)
                for field in ('directions', 'sourceName', 'sourceUrl', 'verifiedOn', 'coordinateSourceUrl'):
                    require(isinstance(record.get(field), str) and record[field].strip(), prefix + label + ' ' + field + ' required')
                require(record['sourceUrl'].startswith('https://') and record['coordinateSourceUrl'].startswith('https://'), prefix + label + ' access sources must use HTTPS')
                try:
                    date.fromisoformat(record['verifiedOn'])
                except ValueError:
                    raise ValueError(prefix + label + ' verifiedOn must use YYYY-MM-DD')
                require(not any(key.startswith('bank') or key == 'riverBank' for key in record), prefix + label + ' approximate access cannot claim a verified bank')
                points[label] = record
                continue
            for field in ('accessType', 'operator', 'sourceName', 'sourceUrl', 'verifiedOn'):
                require(isinstance(record.get(field), str) and record[field].strip(), prefix + label + ' ' + field + ' required')
            require(record['sourceUrl'].startswith('https://'), prefix + label + ' sourceUrl must use HTTPS')
            try:
                verified_on = date.fromisoformat(record['verifiedOn'])
            except ValueError:
                raise ValueError(prefix + label + ' verifiedOn must use YYYY-MM-DD')
            require(verified_on.year >= 2000, prefix + label + ' verifiedOn is invalid')
            lat, lon = record.get('lat'), record.get('lon')
            require(type(lat) in (int, float) and math.isfinite(lat) and -90 <= lat <= 90, prefix + 'Invalid latitude for ' + label)
            require(type(lon) in (int, float) and math.isfinite(lon) and -180 <= lon <= 180, prefix + 'Invalid longitude for ' + label)
            bank_fields = ('riverBank', 'bankVerifiedOn', 'bankSourceName', 'bankSourceUrl', 'bankNote')
            bank_values = [field in record for field in bank_fields]
            require(all(bank_values) or not any(bank_values), prefix + label + ' bank metadata must be complete')
            if all(bank_values):
                require(record['riverBank'] in ('river-left', 'river-right'), prefix + label + ' riverBank must be river-left or river-right')
                for field in ('bankSourceName', 'bankNote'):
                    require(isinstance(record[field], str) and record[field].strip(), prefix + label + ' ' + field + ' required')
                require(isinstance(record['bankSourceUrl'], str) and record['bankSourceUrl'].startswith('https://'), prefix + label + ' bankSourceUrl must use HTTPS')
                try:
                    bank_verified_on = date.fromisoformat(record['bankVerifiedOn'])
                except (TypeError, ValueError):
                    raise ValueError(prefix + label + ' bankVerifiedOn must use YYYY-MM-DD')
                require(bank_verified_on.year >= 2000, prefix + label + ' bankVerifiedOn is invalid')
            point = {
                'status': 'verified', 'lat': lat, 'lon': lon,
                'accessType': record['accessType'], 'operator': record['operator'],
                'sourceName': record['sourceName'], 'sourceUrl': record['sourceUrl'],
                'verifiedOn': record['verifiedOn'], 'note': record['note'],
            }
            point.update({field: record[field] for field in bank_fields if field in record})
            points[label] = point
        map_points[path.stem] = points
    access_by_id = {}
    for code, points in map_points.items():
        raw = json.loads((root / f'catalog/map_points/{code}.json').read_text())['points']
        for name, point in points.items():
            identity = raw[name].get('id')
            if identity is None:  # Legacy research package, before ID migration.
                continue
            require(isinstance(identity, str) and re.fullmatch(r'acc-[a-z0-9-]+', identity), 'Invalid access ID')
            require(identity not in access_by_id, 'Duplicate access ID: ' + identity)
            aliases = raw[name].get('aliases', [])
            require(isinstance(aliases, list) and all(isinstance(a, str) and a.strip() for a in aliases), 'Invalid access aliases')
            point.update(id=identity, name=name, state=code, aliases=aliases)
            access_by_id[identity] = point
    for code, points in map_points.items():
        names = {}
        for name, point in points.items():
            for alias in [name] + point.get('aliases', []):
                require(alias not in names or names[alias] == name, 'Ambiguous access alias: ' + alias)
                names[alias] = name
    def lookup_reference(code, name):
        points = map_points.get(code, {})
        if name in points:
            return points[name]
        return next((p for p in points.values() if name in p.get('aliases', [])), None)
    rivers, ids = [], set()
    for path in sorted((root / 'catalog/rivers').glob('*.json')):
        r = json.loads(path.read_text())
        prefix = path.name + ': '
        require(SLUG.fullmatch(r['id']) and r['id'] == path.stem and r['id'] not in ids, prefix + 'ID must be unique and match filename')
        ids.add(r['id'])
        require(r['state'] in codes, prefix + 'Unknown state')
        for field in ('name', 'blurb'):
            require(isinstance(r[field], str) and r[field].strip(), prefix + field + ' required')
        try:
            validate_gauge(r)
            validate_source(r)
        except (ValueError, TypeError) as exc:
            raise ValueError(prefix + str(exc)) from exc
        if 'gaugeContext' in r:
            context = r['gaugeContext']
            require(isinstance(context, dict) and context.get('status') in ('context-only', 'seasonal-gap', 'unresolved'), prefix + 'Invalid gauge context status')
            for key in ('note', 'sourceName', 'sourceUrl', 'checkedOn'):
                require(isinstance(context.get(key), str) and context[key].strip(), prefix + 'Gauge context ' + key + ' required')
            require(context['sourceUrl'].startswith('https://'), prefix + 'Gauge context source must use HTTPS')
            try:
                date.fromisoformat(context['checkedOn'])
            except ValueError:
                raise ValueError(prefix + 'Gauge context checkedOn must use YYYY-MM-DD')
        try: ZoneInfo(r['timezone'])
        except (ZoneInfoNotFoundError, ValueError): raise ValueError(prefix + 'Invalid IANA timezone')
        timing = r.get('timing', {'mode': 'model'})
        require(isinstance(timing, dict) and timing.get('mode') in ('model', 'unavailable'), prefix + 'Invalid timing mode')
        if 'timing' in r and timing['mode'] == 'model':
            for key in ('note', 'sourceName', 'sourceUrl', 'checkedOn'):
                require(isinstance(timing.get(key), str) and timing[key].strip(), prefix + 'Model timing ' + key + ' required')
            require(timing['sourceUrl'].startswith('https://'), prefix + 'Model timing source must use HTTPS')
            try:
                date.fromisoformat(timing['checkedOn'])
            except ValueError:
                raise ValueError(prefix + 'Model timing checkedOn must use YYYY-MM-DD')
        if timing['mode'] == 'unavailable':
            require(isinstance(timing.get('note'), str) and timing['note'].strip(), prefix + 'Unavailable timing requires a note')
            require(r.get('refFlowCfs') is None and r.get('refSpeedMph') is None, prefix + 'Unavailable timing must not contain calibration numbers')
        numeric_fields = [('lat', -90, 90), ('lon', -180, 180)]
        if timing['mode'] == 'model':
            numeric_fields += [('refFlowCfs', 0, 10000000), ('refSpeedMph', 0, 30)]
        for key, low, high in numeric_fields:
            v = r[key]
            require(type(v) in (int, float) and math.isfinite(v) and low < v <= high, prefix + 'Invalid ' + key)
        require(isinstance(r['sections'], list) and len(r['sections']) > 0, prefix + 'Sections required')
        section_ids = set()
        for sec in r['sections']:
            derived_map_fields = ('mapPilot', 'mapReleased', 'mapReleaseNote', 'mapPrecision', 'mapPendingReason', 'putInCoords', 'takeOutCoords', 'putInAccess', 'takeOutAccess')
            require(not any(key in sec for key in derived_map_fields), prefix + 'Map fields are generated from catalog/map_points; remove them from section ' + sec.get('id', '?'))
            require(SLUG.fullmatch(sec['id']) and sec['id'] not in section_ids, prefix + 'Invalid/duplicate section ID')
            section_ids.add(sec['id'])
            for key in ('putIn', 'takeOut', 'difficulty', 'notes'):
                require(isinstance(sec[key], str) and sec[key].strip(), prefix + 'Section ' + key + ' required')
            require(type(sec['miles']) in (int, float) and math.isfinite(sec['miles']) and 0 < sec['miles'] <= 2000, prefix + 'Invalid mileage')
            require(isinstance(sec.get('multiDay', False), bool), prefix + 'Section multiDay must be true or false')
            for guide in sec.get('guideTimes', []):
                require(isinstance(guide, dict) and guide.get('unit') in ('hours', 'days'), prefix + 'Invalid guide time unit')
                lo, hi = guide.get('min'), guide.get('max')
                require(type(lo) in (int, float) and type(hi) in (int, float) and math.isfinite(lo) and math.isfinite(hi) and 0 < lo <= hi, prefix + 'Invalid guide time range')
                for key in ('conditions', 'sourceName', 'sourceUrl', 'checkedOn'):
                    require(isinstance(guide.get(key), str) and guide[key].strip(), prefix + 'Guide ' + key + ' required')
                require(guide['sourceUrl'].startswith('https://'), prefix + 'Guide URL must use HTTPS')
                try:
                    date.fromisoformat(guide['checkedOn'])
                except ValueError:
                    raise ValueError(prefix + 'Guide checkedOn must use YYYY-MM-DD')
            point_registry = map_points.get(r['state'], {})
            audit = map_audits.get(r['state'], {}).get(r['id'])
            def endpoint_access(end):
                identity = sec.get(end + 'AccessId')
                ref = sec.get(end + 'Point')
                if identity is not None:
                    require(isinstance(identity, str) and identity in access_by_id, prefix + 'Unknown access ID')
                    # Validate retained legacy references, but resolve identity by ID.
                    if ref is not None:
                        require(isinstance(ref, dict) and set(ref) == {'state', 'name'}, prefix + 'Invalid endpoint reference')
                        require(lookup_reference(ref['state'], ref['name']) is not None, prefix + 'Unknown endpoint reference')
                        require(lookup_reference(ref['state'], ref['name']).get('id') == identity, prefix + 'Endpoint reference disagrees with access ID')
                    return access_by_id[identity]
                if ref is None:
                    return point_registry.get(sec[end])
                require(isinstance(ref, dict) and set(ref) == {'state', 'name'}, prefix + 'Invalid endpoint reference')
                require(isinstance(ref['state'], str) and isinstance(ref['name'], str), prefix + 'Invalid endpoint reference values')
                require(lookup_reference(ref['state'], ref['name']) is not None, prefix + 'Unknown endpoint reference')
                return lookup_reference(ref['state'], ref['name'])
            put_access = endpoint_access('putIn')
            take_access = endpoint_access('takeOut')
            if 'distanceReview' in sec:
                require(isinstance(sec['distanceReview'], str) and sec['distanceReview'].strip(), prefix + 'Distance review requires a note')
            if 'accessReview' in sec:
                require(isinstance(sec['accessReview'], str) and sec['accessReview'].strip(), prefix + 'Access review requires a note')
            notices = sec.get('notices', [])
            require(isinstance(notices, list), prefix + 'Notices must be a list')
            for notice in notices:
                require(isinstance(notice, dict), prefix + 'Invalid notice')
                for field in ('title', 'text', 'sourceName', 'sourceUrl', 'checkedOn'):
                    require(isinstance(notice.get(field), str) and notice[field].strip(), prefix + 'Notice ' + field + ' required')
                require(notice['sourceUrl'].startswith('https://'), prefix + 'Notice source must use HTTPS')
                try: date.fromisoformat(notice['checkedOn'])
                except ValueError: raise ValueError(prefix + 'Invalid notice date')
            mapped = bool(
                not sec.get('accessReview') and audit
                and put_access and put_access['status'] in ('verified', 'access-verified')
                and take_access and take_access['status'] in ('verified', 'access-verified')
            )
            if audit and not mapped:
                pending_reasons = []
                for label, access in ((sec['putIn'], put_access), (sec['takeOut'], take_access)):
                    if not access or access['status'] == 'pending':
                        note = access['note'] if access else 'No sourced access record has been added yet.'
                        pending_reasons.append(label + ': ' + note)
                sec['mapPendingReason'] = sec.get('accessReview') or (' '.join(pending_reasons) if pending_reasons else audit['note'])
            if mapped:
                sec['mapPilot'] = True
                sec['mapPrecision'] = 'exact' if all(p['status'] == 'verified' for p in (put_access, take_access)) else 'approximate'
                sec['putInCoords'] = {k: (put_access if put_access['status'] == 'verified' else put_access['areaCenter'])[k] for k in ('lat', 'lon')}
                sec['takeOutCoords'] = {k: (take_access if take_access['status'] == 'verified' else take_access['areaCenter'])[k] for k in ('lat', 'lon')}
                access_fields = ('id', 'status', 'accessType', 'operator', 'sourceName', 'sourceUrl', 'verifiedOn', 'note', 'directions', 'coordinateSourceUrl')
                bank_fields = ('riverBank', 'bankVerifiedOn', 'bankSourceName', 'bankSourceUrl', 'bankNote')
                sec['putInAccess'] = {k: put_access[k] for k in access_fields + bank_fields if k in put_access}
                sec['takeOutAccess'] = {k: take_access[k] for k in access_fields + bank_fields if k in take_access}
            approval = map_reviews.get(r['state'], {}).get(r['id'] + '/' + sec['id'], {})
            reviewed = r['state'] not in review_required or (approval.get('status') == 'reviewed' and approval.get('fingerprint') == fingerprint(r, sec, put_access, take_access))
            sec['mapReleased'] = bool(mapped and r['state'] in release['states'] and reviewed)
            if mapped and not reviewed:
                sec['mapReleaseNote'] = 'This section awaits map review or its evidence has changed.'
            require(isinstance(sec.get('mapPilot', False), bool), prefix + 'Section mapPilot must be true or false')
            coord_keys = ('putInCoords', 'takeOutCoords')
            require(all(key in sec for key in coord_keys) or not any(key in sec for key in coord_keys), prefix + 'Section map coordinates must include both endpoints')
            for key in coord_keys:
                if key not in sec:
                    continue
                point = sec[key]
                require(isinstance(point, dict), prefix + 'Section ' + key + ' must be an object')
                require(set(point) == {'lat', 'lon'}, prefix + 'Section ' + key + ' must contain only lat and lon')
                for axis, low, high in [('lat', -90, 90), ('lon', -180, 180)]:
                    value = point[axis]
                    require(type(value) in (int, float) and math.isfinite(value) and low <= value <= high, prefix + 'Invalid section ' + key + ' ' + axis)
            validate_distance_evidence(sec, prefix + sec['id'] + ': ')
            require(not distance_conflict(sec) or sec.get('distanceReview'), prefix + sec['id'] + ': Impossible mapped mileage; correct it or add distanceReview to block estimates')
        require(isinstance(r.get("multiDay", False), bool), prefix + "multiDay must be true or false")
        r["multiDay"] = r.get("multiDay", False)
        audit = map_audits.get(r['state'], {}).get(r['id'])
        r['mapAudit'] = audit['status'] if audit else 'not-audited'
        if audit:
            r['mapAuditNote'] = audit['note']
        rivers.append(r)
    require(bool(rivers), 'No rivers found')
    river_by_id = {river['id']: river for river in rivers}
    for state, audits in map_audits.items():
        for river_id, audit in audits.items():
            require(river_id in river_by_id and river_by_id[river_id]['state'] == state, state + ': unknown audited river ' + river_id)
            if audit['status'] == 'verified':
                for sec in river_by_id[river_id]['sections']:
                    require(sec.get('mapPrecision') == 'exact', state + ': verified river ' + river_id + ' has an unverified endpoint in ' + sec['id'])
    rivers.sort(key=lambda r: (r['state'], r['name'].casefold()))
    result = {'version': 1, 'states': states, 'craft': settings['craft'], 'mapRelease': release, 'rivers': rivers, 'accessPoints': list(access_by_id.values())}
    build_outputs(root, result)  # Route review is independent of calculator mileage.
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate and verify generated output is current')
    args = parser.parse_args()
    payload = json.dumps(build(), ensure_ascii=False, indent=2) + '\n'
    target = ROOT / 'public/catalog.json'
    if args.check:
        require(target.exists() and target.read_text() == payload, 'Run python3 tools/build_catalog.py to update public/catalog.json')
    else:
        temp = target.with_suffix('.tmp'); temp.write_text(payload); temp.replace(target)
    write_or_check(ROOT, json.loads(payload), args.check)
    write_catalog_assets(ROOT, json.loads(payload), args.check)
    print(f'Catalog valid: {len(json.loads(payload)["rivers"])} rivers')

if __name__ == '__main__': main()
