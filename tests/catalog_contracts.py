"""Compatibility assertions for a growing, reviewed catalog.

Historical batches may add or correct evidence. Their tests must preserve public
identifiers and aliases without freezing unrelated coordinates, prose or counts.
Individual source/geometry tests and approval-mutation tests enforce precision.
"""


def assert_registry_identity(case, before, after):
    def rows(value):
        if isinstance(value, dict):
            return [dict(point, name=name) for name, point in value.items()]
        return value
    current = {p['id']: p for p in rows(after)}
    for old in rows(before):
        case.assertIn(old['id'], current, old.get('name'))
        point = current[old['id']]
        if old.get('name') != point.get('name'):
            case.assertIn(old['name'], point.get('aliases', []), old['id'])


def assert_river_identity(case, before, after):
    case.assertEqual(before['id'], after['id'])
    case.assertEqual(before['state'], after['state'])
    case.assertTrue({s['id'] for s in before['sections']} <= {s['id'] for s in after['sections']})


def assert_catalog_identity(case, before, after):
    current = {r['id']: r for r in after['rivers']}
    for old in before['rivers']:
        case.assertIn(old['id'], current)
        assert_river_identity(case, old, current[old['id']])
    if 'accessPoints' in before:
        assert_registry_identity(case, before['accessPoints'], after['accessPoints'])
