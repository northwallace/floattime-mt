"""Explicit later corrections allowed by historical batch-preservation checks.

These are reviewed changes, not a blanket exemption for a river or state.
Source decisions and new feature boundaries have separate regression checks.
"""
REVIEWED_MILES = {
    'jefferson-upper': {'silver-star-parsons': 10.5, 'parsons-parrott': 7.7},
    'snake-sf-swan': {'palisades-spring': 12.2, 'spring-conant': 2.0},
    'snake-sf-canyon': {'conant-byington': 24.8, 'byington-lorenzo': 14.7},
    'teton': {'bates-rainey': 4.3, 'rainey-cache': 3.7},
}


def before_barretts_course_review(record, raw=False):
    """Undo only the recorded two-course copy change for historical audits."""
    if record.get('id') != 'beaverhead':return record
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / 'research/barretts-courses-20261106' / ('raw-river-change.json' if raw else 'normalized-river-change.json')
    change = json.loads(path.read_text())
    return change['before'] if record == change['after'] else record


def before_access_completion_record(record, kind='rivers'):
    """Reverse only exact recorded Barretts/Crow Wing changes for older audits."""
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / 'research/access-completion-20261106/normalized-changes.json'
    if kind == 'rivers':record = before_barretts_course_review(record)
    rows = json.loads(path.read_text())[kind]
    row = next((r for r in rows if r['id'] == record.get('id')), None)
    return row['before'] if row and record == row['after'] else record


def before_barretts_registry_review(registry):
    """A narrow ledger for one source record and its river-level audit note."""
    import copy
    import json
    from pathlib import Path
    batch = Path(__file__).resolve().parents[1] / 'research/access-completion-20261106'
    before = json.loads((batch / 'before/catalog/map_points/MT.json').read_text())
    after = json.loads((batch / 'after-MT-registry.json').read_text())
    result = copy.deepcopy(registry)
    name = 'Barretts Station Park (above dam)'
    if result['points'].get(name) == after['points'][name]:
        result['points'][name] = before['points'][name]
    if result['auditedRivers'].get('beaverhead') == after['auditedRivers']['beaverhead']:
        result['auditedRivers']['beaverhead'] = before['auditedRivers']['beaverhead']
    return result


def before_jefferson_course_review(river):
    """Reverse only the exact recorded course-copy update, never pin changes."""
    if river.get('id') != 'jefferson-upper':
        return river
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / 'research/jefferson-course-refinement-20261106/normalized-river-change.json'
    change = json.loads(path.read_text())
    return change['before'] if river == change['after'] else river


def before_jefferson_route_addition(routes):
    """Remove only the exact local route-index addition for old snapshot tests."""
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / 'research/jefferson-course-refinement-20261106/public-route-index-additions.json'
    additions = json.loads(path.read_text())
    return [row for row in routes if row not in additions]
SNAKE_RIVERS = {'snake-sf-swan', 'snake-sf-canyon'}
SNAKE_POINTS = {'Palisades Dam', 'Spring Creek', 'Conant', 'Fullmer', 'Byington', 'Lorenzo'}
TETON_POINTS = {'Bates Bridge', 'Rainey Bridge', 'Cache Bridge'}
HENRYS_RIVERS = {'henrys-fork-ashton', 'henrys-fork-box'}
HENRYS_POINTS = {'Island Park Dam (Box Canyon)', 'Last Chance', 'Warm River Campground',
                 'Ashton (Vernon area)', 'Vernon Bridge', 'St. Anthony'}
REVIEWED_ID_ROUTES = [
    'ID/teton--south-bates-buxton.json',
    'ID/henrys-fork-ashton--stone-bridge-jump-off.json',
    'ID/henrys-fork-ashton--jump-off-ashton-reservoir.json',
    'ID/henrys-fork-ashton--stone-bridge-ashton-reservoir.json',
    'ID/henrys-fork-box--box-canyon.json',
    'ID/henrys-fork-ashton--ora-vernon.json',
    'ID/henrys-fork-ashton--vernon-chester-upstream.json',
    'ID/henrys-fork-ashton--ora-chester-upstream.json',
    'ID/henrys-fork-ashton--chester-downstream-fun-farm.json',
]
REVIEWED_WI_ROUTES = [
    'WI/black-river-wi--pettibone-pass-canoe-launch-to-mark-holmgren-memorial-landing.json',
    'WI/black-river-wi--pettibone-halls-creek.json',
    'WI/black-river-wi--halls-creek-holmgren.json',
    'WI/little-wolf-river--wolf-road-county-j.json',
    'WI/little-wolf-river--county-j-big-falls.json',
    'WI/waupaca-river--cobbtown-brainards.json',
    'WI/wisconsin-river-lower--boscobel-west-woodman.json',
    'WI/wisconsin-river-lower--woodman-millville.json',
    'WI/kinnickinnic-river-river-falls--glen-park-county-f.json',
]
REVIEWED_WI_STREAMS = [
    {'riverName': 'Waupaca River', 'riverIds': ['waupaca-river']},
    {'riverName': 'Crystal River', 'riverIds': ['crystal-river']},
    {'riverName': 'Kinnickinnic River', 'riverIds': ['kinnickinnic-river-river-falls']},
]


def with_reviewed_wi_routes(expected):
    """Allow only this explicit ledger of later route additions.

    Historical batch tests still catch missing, reordered or unexpected routes,
    without requiring edits to every old test when another river is reviewed.
    Each added route has its own source/geometry and feature-boundary checks.
    """
    paths = expected['routes'] if isinstance(expected, dict) else expected
    paths = list(dict.fromkeys(paths + REVIEWED_WI_ROUTES))
    return dict(expected, routes=paths) if isinstance(expected, dict) else paths


WAUPACA_POINTS = {'Wolf River Road Access', 'County J Little Wolf Access',
                  'Cobbtown Road Access', 'Brainard’s Bridge Park Access'}

CRYSTAL_POINTS = {'Rural Crystal River Access', 'Nelson Park Crystal River Access',
                  'Shadow Lake Boat Launch'}


FLAMBEAU_POINTS = {'Cedar Rapids Bridge Access'}
LOWER_WISCONSIN_LANDING_POINTS = {'Port Andrews Boat Landing', 'Woodman Landing (Big Green River)'}
LOWER_WISCONSIN_POINTS = {'Arena Landing', 'Muscoda West', 'Boscobel West - Von Haden'}
BARRIER_REVIEW_POINTS = {'Wisconsin River - Hwy O Access', 'Newville Public Access'}
BARRIER_REVIEW_SECTIONS = {
    'wisconsin-river-headwaters/wisconsin-river-hwy-70-access-to-wisconsin-river-hwy-o-access',
    'wisconsin-river-headwaters/wisconsin-river-hwy-o-access-to-wisconsin-river-hwy-d-access',
    'rock-river/groeler-road-boat-launch-to-newville-public-access',
    'rock-river/newville-public-access-to-rock-river-ramp',
    'wisconsin-river-lower/woodman-millville',
}


def before_middle_kickapoo_review(key, review):
    """Reverse only an exact recorded local-name/approach review."""
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / 'research/middle-kickapoo-expansion-20261106/review-changes.json'
    rows = json.loads(path.read_text())
    change = next((r for r in rows if r['key'] == key), None)
    return change['before'] if change and review == change['after'] else review


def before_kickapoo_review(key, review):
    """Reverse only an exact, recorded November 6 access/notice review."""
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / 'research/kickapoo-review-20261106/review-changes.json'
    review = before_middle_kickapoo_review(key, review)
    rows = json.loads(path.read_text())
    change = next((r for r in rows if r['key'] == key and r['before']), None)
    if change and review == change['after']:
        return change['before']
    return review


def before_directions_rendering(key, review):
    """Undo only the documented normalization migration for historical comparisons."""
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / 'research/wisconsin-barrier-review-20261106/directions-rendering-migration.json'
    review = before_kickapoo_review(key, review)
    rows = json.loads(path.read_text())['sections']
    change = next((r for r in rows if r['section'] == key), None)
    if change and review.get('fingerprint') == change['afterFingerprint']:
        return dict(review, fingerprint=change['beforeFingerprint'])
    return review


def assert_later_review_update(case, key, before, after):
    original_after = after
    after = before_directions_rendering(key, after)
    if original_after != after and before == after:
        return True
    if key not in BARRIER_REVIEW_SECTIONS:
        return False
    # The later review improves precision/copy; it never releases a held map.
    case.assertEqual(after['status'], before['status'], key)
    case.assertEqual(after['sourceManifest'], 'research/wisconsin-barrier-review-20261106/manifest.json')
    case.assertEqual(after['checkedOn'], '2026-11-06')
    return True


def assert_later_point_update(case, name, before, after):
    """Only explicitly documented changes to existing points are permitted."""
    if before == after:
        return False
    if name == 'Barretts Station Park (above dam)' and 'name' not in before:
        import json
        from pathlib import Path
        batch = Path(__file__).resolve().parents[1] / 'research/access-completion-20261106'
        prior = json.loads((batch / 'before/catalog/map_points/MT.json').read_text())
        reviewed = json.loads((batch / 'after-MT-registry.json').read_text())
        case.assertEqual(before, prior['points'][name])
        case.assertEqual(after, reviewed['points'][name])
        return True
    if name in ('Clark Canyon Dam', 'High Bridge FAS'):
        import json
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / 'research/beaverhead-precision-20261106/point-changes.json'
        change = next(c for c in json.loads(path.read_text()) if c['beforeName'] == name)
        normalized = 'name' in before
        case.assertEqual(before, change['beforeNormalized' if normalized else 'before'])
        case.assertEqual(after, change['afterNormalized' if normalized else 'after'])
        return True
    if name == 'Village Park Access':
        import json
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / 'research/middle-kickapoo-expansion-20261106/point-changes.json'
        change = json.loads(path.read_text())[0]
        case.assertEqual(change['name'], name)
        for field in set(before) | set(after):
            if field not in change['changedFields']:
                case.assertEqual(before.get(field), after.get(field), field)
        for field in change['changedFields']:
            case.assertEqual(after[field], change['after'][field])
        return True
    if name == "Andrew's Canoe Landing":
        for field in set(before) | set(after):
            if field != 'aliases':
                case.assertEqual(before.get(field), after.get(field), field)
        case.assertEqual(after['aliases'], list(dict.fromkeys(before.get('aliases', []) +
                         ['Kickapoo River Landing 20', 'La Farge Landing 20'])))
        return True
    if name in BARRIER_REVIEW_POINTS:
        for field in ('id', 'sourceUrl', 'coordinateSourceUrl', 'operator', 'aliases'):
            case.assertEqual(after[field], before[field])
        case.assertEqual(after['status'], 'verified')
        for axis in ('lat', 'lon'):
            case.assertEqual(after[axis], before['areaCenter'][axis])
        case.assertNotIn('areaCenter', after)
        case.assertNotIn('riverBank', after)
        case.assertIn('desktop', after['note'])
        return True
    if name == 'Bridgeport Landing (North)':
        for field in set(before) | set(after):
            if field not in ('areaCenter', 'directions', 'note', 'verifiedOn', 'coordinateSourceUrl'):
                case.assertEqual(before.get(field), after.get(field))
        case.assertEqual(after['status'], 'access-verified')
        case.assertEqual(after['areaCenter']['lat'], 42.99967)
        case.assertEqual(after['areaCenter']['lon'], -91.0513594)
        case.assertNotIn('lat', after)
        case.assertNotIn('riverBank', after)
        case.assertIn('north channel', after['directions'])
        return True
    if name == 'South Fork Flambeau River Access — Town of Eisenstein #3014':
        for field in set(before) | set(after):
            if field != 'aliases':
                case.assertEqual(before.get(field), after.get(field))
        case.assertEqual(after['aliases'], list(dict.fromkeys(before.get('aliases', []) + ['Smith Rapids Canoe Access', 'Smith Rapids Covered Bridge'])))
        return True
    if name == 'Big Falls Pond Boat Ramp':
        case.assertEqual(after['id'], before['id'])
        case.assertEqual(after['status'], 'verified')
        for axis in ('lat', 'lon'):
            case.assertEqual(after[axis], before['areaCenter'][axis])
        case.assertNotIn('areaCenter', after)
        case.assertIn('above-dam takeout', after['note'])
        return True
    if name == 'Manawa Millpond Access':
        for field in set(before) | set(after):
            if field not in ('note', 'directions'):
                case.assertEqual(before.get(field), after.get(field))
        case.assertIn('July 2024 levee breach', after['note'])
        case.assertIn('July 2026', after['note'])
        return True
    return False


def assert_wi_access_preserved(case, before, after):
    # Preserve all prior identities and the reviewed additions. Future catalog
    # expansion is validated by the builder and its own source-evidence tests.
    case.assertTrue(set(before['points']) | {'Robb Park Upstream Takeout', 'Halls Creek Canoe Landing'} | WAUPACA_POINTS | CRYSTAL_POINTS | FLAMBEAU_POINTS | LOWER_WISCONSIN_POINTS | LOWER_WISCONSIN_LANDING_POINTS <= set(after['points']))
    for name, point in before['points'].items():
        current = after['points'][name]
        if name == 'Pettibone Pass Canoe Launch':
            case.assertEqual(point['id'], current['id'])
            case.assertEqual(current['status'], 'access-verified')
            case.assertIn('Mission Road Canoe Launch', current['aliases'])
        elif not assert_later_point_update(case, name, point, current):
            case.assertEqual(point, current)


def expected_miles(old):
    return {s['id']: REVIEWED_MILES.get(old['id'], {}).get(s['id'], s['miles'])
            for s in old['sections']}


def assert_timing_preserved_or_held(case, old, new):
    for field in ('gauge', 'gaugeContext', 'gaugeRelationship'):
        if old['id'] == 'wisconsin-river-headwaters' and field != 'gauge':
            case.assertEqual(new['gaugeRelationship'], 'same-river-reference')
            case.assertEqual(new['gaugeContext']['status'], 'context-only')
            case.assertIn('below Rainbow Dam', new['gaugeContext']['note'])
            continue
        if old['id'] == 'little-wolf-river' and field != 'gauge':
            case.assertEqual(new['gaugeRelationship'], 'same-river-reference')
            case.assertEqual(new['gaugeContext']['status'], 'context-only')
            case.assertIn('Royalton station is downstream', new['gaugeContext']['note'])
            continue
        if old['id'] == 'black-river-wi' and field != 'gauge':
            # The November 5 guide review distinguishes above-dam sections
            # from the Galesville reference station. Gauge ID stays unchanged.
            case.assertEqual(new['gaugeRelationship'], 'same-river-reference')
            case.assertEqual(new['gaugeContext']['status'], 'context-only')
            case.assertIn('downstream of Black River Falls Dam', new['gaugeContext']['note'])
            continue
        if old['id'] == 'henrys-fork-ashton' and field != 'gauge':
            # The November 4 review separates above-reservoir floats from this
            # below-dam reference station. Gauge identity itself is unchanged.
            case.assertEqual(new['gaugeRelationship'], 'same-river-reference')
            case.assertEqual(new['gaugeContext']['status'], 'context-only')
            case.assertIn('below Ashton Dam', new['gaugeContext']['note'])
            continue
        case.assertEqual(old.get(field), new.get(field), (old['id'], field))
    if old['id'] in SNAKE_RIVERS | HENRYS_RIVERS | {'teton'}:
        # The November 3 mileage review found no documented legacy calibration.
        case.assertIsNone(new['refFlowCfs'])
        case.assertIsNone(new['refSpeedMph'])
        case.assertEqual(new['timing']['mode'], 'unavailable')
        case.assertTrue(new['timing']['note'])
    else:
        for field in ('refFlowCfs', 'refSpeedMph', 'timing'):
            case.assertEqual(old.get(field), new.get(field), (old['id'], field))


def assert_id_access_preserved(case, before, after):
    for label, point in before['points'].items():
        if label in SNAKE_POINTS | TETON_POINTS | HENRYS_POINTS:
            case.assertEqual(point['id'], after['points'][label]['id'])
        else:
            case.assertEqual(point, after['points'][label])


def assert_kickapoo_path_withdrawn(case, path, old):
    from pathlib import Path
    import json
    filename = Path(path).name
    names = {'kickapoo-river--kickapoo-river-landing-4-to-kickapoo-river-landing-5.json',
             'kickapoo-river--kickapoo-river-landing-14-to-andrew-s-canoe-landing.json'}
    if filename not in names:
        return False
    root = Path(__file__).resolve().parents[1]
    now = json.loads((root / 'catalog/routes/WI' / filename).read_text())
    case.assertEqual(now['status'], 'candidate')
    case.assertFalse(any(now['features'].values()))
    case.assertIn('imagery-channel-mismatch', now['checks']['issues'])
    case.assertEqual(now['review']['evidenceFile'], 'research/kickapoo-review-20261106/manifest.json')
    for field in ('geometry', 'putIn', 'takeOut', 'catalogMiles'):
        case.assertEqual(old[field], now[field])
    case.assertFalse((root / 'public/routes' / filename).exists())
    return True
