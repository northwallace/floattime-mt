import copy
import hashlib
import json
from pathlib import Path
import unittest

from tools.agency_courses import registered_source, source_chain, trim_chain
from tools.build_catalog import build
from tools.route_catalog import validate, geometry_checks, review_signature
from tools.stage_agency_course import stage_record

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'research/kettle-course-20261106'

def read(path):
    return json.loads(path.read_text())

class AgencyCourseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build()
        cls.record = read(ROOT / 'catalog/routes/MN/kettle-river-mn--musclewood-highway-23.json')
        cls.payload = read(ROOT / cls.record['source']['evidenceFile'])
        cls.config = registered_source(cls.record, ROOT)

    def test_reusable_staging_suggests_source_trims_without_approving_or_changing_pins(self):
        before_index = (ROOT / 'catalog/routes/MN.json').read_bytes()
        before_access = (ROOT / 'catalog/map_points/MN.json').read_bytes()
        source = self.record['source']
        candidate = stage_record(ROOT, self.record['riverId'], self.record['sectionId'],
            source['adapterId'], source['evidenceFile'], self.record['direction']['parts'])
        self.assertEqual(candidate['geometry'], self.record['geometry'])
        self.assertEqual(candidate['status'], 'candidate')
        self.assertFalse(any(candidate['features'].values()))
        self.assertNotIn('review', candidate)
        self.assertNotIn('overviewReview', candidate)
        self.assertEqual((ROOT / 'catalog/routes/MN.json').read_bytes(), before_index)
        self.assertEqual((ROOT / 'catalog/map_points/MN.json').read_bytes(), before_access)

    def test_display_is_reconstructed_from_actual_source_with_explicit_trims(self):
        section, metrics = validate(self.record, self.catalog, ROOT)
        chain = source_chain(self.payload, self.config, 'CBR00618', self.record['direction']['parts'])
        self.assertEqual(trim_chain(chain, self.record['direction']['clip']), self.record['geometry'])
        self.assertEqual([p['featureId'] for p in self.record['direction']['parts']], ['37', '35'])
        self.assertEqual(section['miles'], 16.5)
        self.assertAlmostEqual(metrics['routeMiles'], 16.3729, places=3)
        self.assertEqual(self.record['checks']['issues'], [])
        self.assertEqual(self.record['features'], dict(display=True, landOverlay=False, distanceEstimate=False, remainingTime=False))
        self.assertEqual(section['mapPrecision'], 'approximate')

    def test_resigning_an_invented_corner_does_not_bypass_source_fidelity(self):
        record = copy.deepcopy(self.record)
        record['geometry']['coordinates'][20][0] += .0001
        record['checks']['metrics'], record['checks']['issues'] = geometry_checks(record)
        record['overviewReview']['signature'] = review_signature(record)
        with self.assertRaisesRegex(ValueError, 'differs from its source'):
            validate(record, self.catalog, ROOT)
        record = copy.deepcopy(self.record)
        del record['geometry']['coordinates'][20]
        record['checks']['metrics'], record['checks']['issues'] = geometry_checks(record)
        record['overviewReview']['signature'] = review_signature(record)
        with self.assertRaisesRegex(ValueError, 'differs from its source'):
            validate(record, self.catalog, ROOT)

    def test_reversed_disconnected_unknown_or_repeated_parts_fail(self):
        for mutation, message in [('order', 'disconnected'), ('orientation', 'disconnected'), ('unknown', 'missing'), ('duplicate', 'Repeated')]:
            with self.subTest(mutation=mutation):
                record = copy.deepcopy(self.record)
                parts = record['direction']['parts']
                if mutation == 'order': parts.reverse()
                if mutation == 'orientation': parts[0]['reverse'] = True
                if mutation == 'unknown': parts[0]['featureId'] = '999999'
                if mutation == 'duplicate': parts.insert(1, copy.deepcopy(parts[0]))
                with self.assertRaisesRegex(ValueError, message):
                    validate(record, self.catalog, ROOT)

    def test_invalid_or_reversed_trim_fails(self):
        for mutation in ('reverse', 'outside', 'negative', 'boolean'):
            record = copy.deepcopy(self.record)
            clip = record['direction']['clip']
            if mutation == 'reverse': clip['start'], clip['end'] = clip['end'], clip['start']
            if mutation == 'outside': clip['end']['segment'] = 100000
            if mutation == 'negative': clip['start']['fraction'] = -0.1
            if mutation == 'boolean': clip['start']['segment'] = True
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'trim'):
                validate(record, self.catalog, ROOT)

    def test_source_registration_water_trail_and_trip_evidence_are_bound(self):
        for key, value, message in [('adapterSha256', '0' * 64, 'registration changed'), ('adapterId', '../other', 'source ID'), ('streamId', 'another-river', 'different water trail'), ('url', 'https://example.org/river', 'URL')]:
            record = copy.deepcopy(self.record)
            record['source'][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, message):
                validate(record, self.catalog, ROOT)
        catalog = copy.deepcopy(self.catalog)
        section = next(r for r in catalog['rivers'] if r['id'] == 'kettle-river-mn')['sections'][0]
        section['distanceEvidence']['note'] += ' Changed trip evidence.'
        with self.assertRaisesRegex(ValueError, 'trip evidence changed'):
            validate(self.record, catalog, ROOT)

    def test_partial_ambiguous_wrong_crs_or_other_river_source_fails(self):
        for mutation, message in [('truncated', 'incomplete'), ('duplicate', 'Ambiguous'), ('crs', 'WGS84'), ('stream', 'different water trail'), ('gap', 'disconnected')]:
            payload = copy.deepcopy(self.payload)
            if mutation == 'truncated': payload['exceededTransferLimit'] = True
            if mutation == 'duplicate': payload['features'].append(copy.deepcopy(payload['features'][0]))
            if mutation == 'crs': payload['spatialReference'] = {'wkid': 26915}
            if mutation == 'stream':
                for f in payload['features']: f['attributes']['prgm_prj'] = 'wrong-trail'
            if mutation == 'gap':
                f = next(f for f in payload['features'] if f['attributes']['objectid'] == 35)
                f['geometry']['paths'][0][0][0] += .00001
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, message):
                source_chain(payload, self.config, 'CBR00618', self.record['direction']['parts'])

    def test_adapter_cannot_enable_navigation_timing_or_land_corridors(self):
        for key in ('landOverlay', 'distanceEstimate', 'remainingTime'):
            record = copy.deepcopy(self.record)
            record['features'][key] = True
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'timing'):
                validate(record, self.catalog, ROOT)
        record = copy.deepcopy(self.record)
        record['scope'] = 'landing-to-landing'
        with self.assertRaisesRegex(ValueError, 'display-only'):
            validate(record, self.catalog, ROOT)

    def test_existing_routes_accesses_and_timing_remain_unchanged(self):
        old = read(B / 'before/public/routes/index.json')['routes']
        now = read(ROOT / 'public/routes/index.json')['routes']
        # Preserve every previously published index record, while allowing new
        # independently reviewed courses. A frozen total/eight-item allowance
        # made this adapter test fail whenever another river was added.
        identities = [(r['riverId'], r['sectionId']) for r in now]
        self.assertEqual(len(identities), len(set(identities)))
        by_id = {identity: row for identity, row in zip(identities, now)}
        for row in old:
            identity = (row['riverId'], row['sectionId'])
            refinements = {
                ('salt-river-lower', 'lsr-water-users-phon-d'): ('research/western-access-review-20261109/course-decisions.json', 'routes'),
                ('big-piney-river', 'boiling-spring-access-to-mason-bridge-access'): ('research/big-piney-courses-20261109/decisions.json', 'courses'),
                ('crawfish-river', 'hubbleton-canoe-launch-to-olson-road-canoe-launch'): ('research/wisconsin-carry-access-20261109/decisions.json', 'course'),
            }
            if identity in refinements:
                # These later reviews explicitly reduced precision to course
                # overviews. Require the exact recorded approval and no new
                # navigation/timing capability, rather than ignoring changes.
                self.assertEqual(by_id.get(identity), dict(row, scope='river-course-overview'))
                manifest, collection = refinements[identity]
                decisions = read(ROOT / manifest)[collection]
                if isinstance(decisions, dict): decisions = [decisions]
                relative = 'catalog/routes/' + row['state'] + '/' + row['file'].split('/')[-1]
                decision = next(r for r in decisions if r.get('route', {}).get('file') == relative)
                source = ROOT / relative
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), decision['route']['sha256'])
                route = read(source)
                self.assertEqual(route['features'], dict(display=True, landOverlay=False, distanceEstimate=False, remainingTime=False))
                validate(route, self.catalog, ROOT)
            else:
                self.assertEqual(by_id.get(identity), row, identity)
        before = read(B / 'before/catalog/rivers/kettle-river-mn.json')
        current = read(ROOT / 'catalog/rivers/kettle-river-mn.json')
        del current['sections'][0]['routeReview']
        self.assertEqual(current['sections'][0], before['sections'][0])
        for key in ('id', 'state', 'gauge', 'gaugeRelationship', 'refFlowCfs', 'refSpeedMph', 'timing'):
            self.assertEqual(current[key], before[key])
        for image in read(B / 'decisions.json')['imageryEvidence']:
            self.assertEqual(hashlib.sha256((ROOT / image['file']).read_bytes()).hexdigest(), image['sha256'])

if __name__ == '__main__':
    unittest.main()
