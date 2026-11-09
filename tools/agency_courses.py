"""Reconstruct display-only agency courses from immutable ArcGIS source lines.

This adapter establishes source fidelity, not navigability or travel speed.
An explicit source registration, published trip order and visual review are
still required. Production validation uses only the Python standard library.
"""
import hashlib
import json
import math
import re

METHOD = 'agency-published-water-trail'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def registered_source(record, root):
    source = record['source']
    identifier = source.get('adapterId', '')
    require(isinstance(identifier, str) and re.fullmatch(r'[A-Z]{2}-[a-z0-9-]+', identifier), 'Invalid agency course source ID')
    folder = (root / 'catalog/routes/agency_sources').resolve()
    path = (folder / (identifier + '.json')).resolve()
    require(path.is_relative_to(root.resolve()) and path.parent == folder and path.is_file(), 'Agency course source is not registered')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == source.get('adapterSha256'), 'Agency course source registration changed; re-review required')
    config = json.loads(raw)
    require(config.get('version') == 1 and config.get('id') == identifier and config.get('state') == record['state'], 'Agency course source registration mismatch')
    require(config.get('format') == 'arcgis-polyline-4326' and config.get('url') == source['url'], 'Agency course source URL or format mismatch')
    for field in ('featureIdField', 'streamField'):
        require(isinstance(config.get(field), str) and bool(config[field]), 'Agency course field mapping missing')
    return config


def source_chain(payload, config, stream_id, parts):
    require(not payload.get('error') and not payload.get('exceededTransferLimit'), 'Agency course response is incomplete')
    reference = payload.get('spatialReference', {})
    require(reference.get('latestWkid', reference.get('wkid')) == 4326, 'Agency course coordinates must be WGS84')
    require(isinstance(payload.get('features'), list) and payload['features'], 'Agency course has no source features')
    features = {}
    for feature in payload['features']:
        require(isinstance(feature, dict) and isinstance(feature.get('attributes'), dict), 'Invalid agency course feature')
        identifier = feature['attributes'].get(config['featureIdField'])
        require(type(identifier) in (str, int) and str(identifier).strip(), 'Agency source feature ID missing')
        identifier = str(identifier)
        require(identifier not in features, 'Ambiguous agency source feature ID')
        features[identifier] = feature
    require(isinstance(parts, list) and 1 <= len(parts) <= 1000, 'Agency source parts required')
    used, chain = set(), []
    for part in parts:
        require(isinstance(part, dict) and set(part) == {'featureId', 'pathIndex', 'reverse'}, 'Invalid agency source part')
        identifier, index, reverse = part['featureId'], part['pathIndex'], part['reverse']
        require(isinstance(identifier, str) and identifier in features, 'Agency source feature missing')
        require(type(index) is int and index >= 0 and type(reverse) is bool, 'Invalid agency source path or orientation')
        key = (identifier, index)
        require(key not in used, 'Repeated agency source part')
        used.add(key)
        feature = features[identifier]
        require(str(feature['attributes'].get(config['streamField'])) == stream_id, 'Agency source part belongs to a different water trail')
        paths = feature.get('geometry', {}).get('paths')
        require(isinstance(paths, list) and index < len(paths), 'Agency source path missing')
        coordinates = paths[index]
        require(isinstance(coordinates, list) and len(coordinates) >= 2, 'Invalid agency source line')
        require(all(isinstance(p, list) and len(p) == 2 and all(finite(v) for v in p) and abs(p[0]) <= 180 and abs(p[1]) <= 85 for p in coordinates), 'Invalid agency source coordinates')
        if reverse:
            coordinates = list(reversed(coordinates))
        # Exact source joins only: do not manufacture connectors across a gap.
        if chain:
            require(chain[-1] == coordinates[0], 'Agency source parts are disconnected or reversed')
        for point in coordinates:
            if not chain or point != chain[-1]:
                chain.append(point)
    require(2 <= len(chain) <= 100000, 'Agency source chain size invalid')
    return chain


def trim_chain(chain, clip):
    require(isinstance(clip, dict) and set(clip) == {'start', 'end'}, 'Agency source trim required')
    positions = []
    for side in ('start', 'end'):
        position = clip[side]
        require(isinstance(position, dict) and set(position) == {'segment', 'fraction'}, 'Invalid agency source trim position')
        i, t = position['segment'], position['fraction']
        require(type(i) is int and 0 <= i < len(chain) - 1 and finite(t) and 0 <= t <= 1, 'Agency source trim outside the line')
        positions.append((i, t))
    (start, a), (end, b) = positions
    require(start + a < end + b, 'Agency source trim is reversed or empty')
    def interpolate(index, fraction):
        if fraction == 0:
            return list(chain[index])
        if fraction == 1:
            return list(chain[index + 1])
        return [chain[index][axis] + fraction * (chain[index + 1][axis] - chain[index][axis]) for axis in (0, 1)]
    points = [interpolate(start, a), *chain[start + 1:end + 1], interpolate(end, b)]
    result = []
    for point in points:
        if not result or point != result[-1]:
            result.append(point)
    require(len(result) >= 2, 'Agency source trim is empty')
    return {'type': 'LineString', 'coordinates': result}


def nearest_position(chain, point):
    """Suggest a source trim near an access area; never moves the access pin."""
    require(isinstance(point, dict) and finite(point.get('lat')) and finite(point.get('lon')), 'Access coordinate required')
    scale = math.cos(math.radians(point['lat']))
    nearest = None
    for i, (a, b) in enumerate(zip(chain, chain[1:])):
        ax, ay = (a[0] - point['lon']) * scale, a[1] - point['lat']
        dx, dy = (b[0] - a[0]) * scale, b[1] - a[1]
        length2 = dx * dx + dy * dy
        if not length2:
            continue
        t = max(0., min(1., -(ax * dx + ay * dy) / length2))
        distance2 = (ax + t * dx) ** 2 + (ay + t * dy) ** 2
        if nearest is None or distance2 < nearest[0]:
            nearest = distance2, {'segment': i, 'fraction': t}
    require(nearest is not None, 'Agency source line has no usable segments')
    return nearest[1]


def valid_direction(direction):
    return direction.get('method') == METHOD and isinstance(direction.get('parts'), list) and bool(direction['parts']) and isinstance(direction.get('clip'), dict)


def validate_agency_course(record, section, payload, root):
    require(record.get('scope') == 'river-course-overview', 'Agency water-trail courses are display-only overviews')
    require(not any(record.get('features', {}).get(k) for k in ('landOverlay', 'distanceEstimate', 'remainingTime')), 'Agency course cannot enable land access or timing features')
    direction = record['direction']
    config = registered_source(record, root)
    chain = source_chain(payload, config, record['source']['streamId'], direction.get('parts'))
    expected = trim_chain(chain, direction.get('clip'))
    require(record.get('geometry') == expected, 'Displayed agency course differs from its source segments or trim')
    evidence = section.get('distanceEvidence', {})
    require(evidence.get('method') == 'published-guide-miles', 'Agency course needs published downstream river-mile evidence')
    require(direction.get('tripEvidenceSha256') == signature(evidence), 'Agency course trip evidence changed; re-review required')
    endpoints = []
    for side in ('putIn', 'takeOut'):
        item = evidence.get(side, {})
        require(item.get('name') == section.get(side) and item.get('name') == record.get(side, {}).get('name') and finite(item.get('riverMile')), 'Agency course trip endpoints or river miles changed')
        endpoints.append(item['riverMile'])
    order = evidence.get('measureDirection')
    require((order == 'decreases-downstream' and endpoints[0] > endpoints[1]) or (order == 'increases-downstream' and endpoints[0] < endpoints[1]), 'Agency course downstream trip order is unconfirmed')
