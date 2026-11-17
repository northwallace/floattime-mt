"""Facility coordinates must not regain exact landing or bank claims."""
import hashlib
import json
import unittest
from pathlib import Path

from tools.build_catalog import build
from tests.later_catalog_reviews import before_nov17_local_release
from tools.route_catalog import reconstruct_directed_source, validate

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'research/montana-access-courses-20261117'


class MadisonAccessPrecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (B / 'decisions.json').exists():
            raise unittest.SkipTest('Local Montana review evidence is not packaged')
        cls.catalog = build()
        cls.rivers = {r['id']: r for r in cls.catalog['rivers']}
        cls.points = json.loads((ROOT / 'catalog/map_points/MT.json').read_text())['points']
        cls.old_points = json.loads((B / 'before/catalog/map_points/MT.json').read_text())['points']
        cls.old_catalog = json.loads((B / 'before/public/catalog.json').read_text())

    def test_facility_coordinates_keep_identity_without_claiming_bank_or_landing(self):
        for name in ['Warm Springs', 'Palisades', 'McAtee Bridge', 'Lyons Bridge', 'Varney Bridge']:
            old, current = self.old_points[name], self.points[name]
            with self.subTest(name=name):
                self.assertEqual(current['id'], old['id'])
                self.assertEqual(current['status'], 'access-verified')
                for field in ['lat', 'lon']:
                    self.assertEqual(current['areaCenter'][field], old[field])
                    self.assertNotIn(field, current)
                self.assertFalse(any(k == 'riverBank' or k.startswith('bank') for k in current))

    def test_documented_harrys_facility_does_not_clear_other_endpoints_or_closure(self):
        point = self.points["Harry's Flat"]
        self.assertEqual(point['id'], self.old_points["Harry's Flat"]['id'])
        self.assertEqual(point['status'], 'access-verified')
        self.assertIn('hardened river access ramp', (B / 'sources/harrys-flat.html').read_text().lower())
        for s in self.rivers['rock-creek']['sections']:
            self.assertFalse(s['mapReleased'])
            self.assertTrue(s['accessReview'])
            if "Harry's Flat" in [s['putIn'], s['takeOut']]:
                self.assertTrue(any(n['title'] == "Harry's Flat seasonal closure" and 'September 28' in n['text'] for n in s['notices']))

    def test_course_reviews_never_enable_timing_or_claim_shore_connections(self):
        d = json.loads((B / 'decisions.json').read_text())
        self.assertEqual(len(d['pathsAdded']), 2)
        for row in d['allReviewedCourses']:
            record = json.loads((ROOT / row['route']['file']).read_text())
            validate(record, self.catalog, ROOT)
            self.assertEqual(record['features'], dict(display=True, landOverlay=False, distanceEstimate=False, remainingTime=False))
            self.assertEqual(record['scope'], 'river-course-overview')
            if record['direction']['method'] == 'usgs-flow-directed-network':
                reconstruct_directed_source(record, ROOT)
            review = json.loads((ROOT / row['fullReview']['file']).read_text())
            self.assertEqual(len(review['imagery']), review['coursePanels'] + 2)
            for image in review['imagery']:
                self.assertEqual(hashlib.sha256((ROOT / image['file']).read_bytes()).hexdigest(), image['sha256'])

    def test_existing_models_planning_distances_and_access_ids_are_unchanged(self):
        for old in self.old_catalog['rivers']:
            current = self.rivers[old['id']]
            for key in ['timing', 'refFlowCfs', 'refSpeedMph', 'flowSource', 'usgsSite']:
                self.assertEqual(current.get(key), old.get(key), (old['id'], key))
            sections = {s['id']: s for s in before_nov17_local_release(current)['sections']}
            for old_s in old['sections']:
                s = sections[old_s['id']]
                for key in ['miles', 'putInAccessId', 'takeOutAccessId', 'mapReleased']:
                    self.assertEqual(s.get(key), old_s.get(key), (old['id'], s['id'], key))

    def test_pending_access_is_not_cleared_by_a_future_public_site_proposal(self):
        point = self.points['Buckhouse Bridge (Missoula)']
        self.assertEqual(point['status'], 'pending')
        self.assertNotIn('areaCenter', point)
        section = next(s for s in self.rivers['bitterroot']['sections'] if s['id'] == 'florence-buckhouse')
        self.assertFalse(section['mapReleased'])
        self.assertTrue(section['accessReview'])
