import json
import shutil
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from html import unescape
import re

import seo
from tools.build_catalog import build, validate_distance_evidence
import copy

ROOT = Path(__file__).resolve().parents[1]


class DistanceEvidenceTests(unittest.TestCase):
    def test_published_guide_miles_support_both_directions(self):
        rivers = {r['id']: r for r in build()['rivers']}
        self.assertEqual(rivers['madison-lower']['sections'][2]['miles'], 4)
        self.assertEqual(rivers['missouri-breaks']['sections'][0]['miles'], 88.5)
        self.assertEqual(rivers['smith']['sections'][0]['miles'], 58.8)
        self.assertEqual([s['miles'] for s in rivers['flathead-north']['sections']], [9.3, 9.2, 11.5])
        for rid, index in [('madison-lower', 2), ('missouri-breaks', 0)]:
            section = copy.deepcopy(rivers[rid]['sections'][index])
            validate_distance_evidence(section, rid)
            section['miles'] += 1
            with self.assertRaisesRegex(ValueError, 'Mileage disagrees'):
                validate_distance_evidence(section, rid)

    def test_guide_direction_and_named_launch_cannot_silently_change(self):
        source = next(r for r in build()['rivers'] if r['id']=='missouri-breaks')['sections'][0]
        section = copy.deepcopy(source)
        section['distanceEvidence']['measureDirection'] = 'decreases-downstream'
        with self.assertRaisesRegex(ValueError, 'Mileage disagrees'):
            validate_distance_evidence(section, '')
        section = copy.deepcopy(source)
        section['putIn'] = 'Fort Benton Motorboat Launch'
        with self.assertRaisesRegex(ValueError, 'endpoint name changed'):
            validate_distance_evidence(section, '')
        section = copy.deepcopy(source)
        del section['distanceEvidence']['putIn']['sourceLocation']
        with self.assertRaisesRegex(ValueError, 'source location required'):
            validate_distance_evidence(section, '')

    def test_unresolved_shedds_takeout_does_not_offer_an_estimate(self):
        river = next(r for r in build()['rivers'] if r['id']=='gallatin-lower')
        self.assertEqual(river['timing']['mode'], 'unavailable')
        self.assertIsNone(river['refSpeedMph'])
        self.assertFalse(river['sections'][0].get('mapPilot'))

    def edit_copy(self, change):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(ROOT / 'catalog', root / 'catalog');shutil.copytree(Path(__file__).resolve().parents[1]/'research/routes',root/'research/routes')
            path = root / 'catalog/rivers/blackfoot.json'
            record = json.loads(path.read_text())
            change(record)
            path.write_text(json.dumps(record))
            return build(root)

    def test_seven_corrections_are_sourced_and_estimate_review_is_resolved(self):
        expected = {'blackfoot': [11.1, 16.5, 10.7], 'missouri-craig': [7.7, 13.4], 'stillwater': [9.6, 7.9]}
        for r in build()['rivers']:
            if r['id'] not in expected:
                continue
            self.assertEqual([s['miles'] for s in r['sections']], expected[r['id']])
            for s in r['sections']:
                self.assertNotIn('distanceReview', s)
                self.assertEqual(s['distanceEvidence']['checkedOn'], '2026-10-27')
            self.assertIn('How this distance was checked', seo.river_html(r))

    def test_mileage_cannot_diverge_from_saved_agency_measures(self):
        with self.assertRaisesRegex(ValueError, 'Mileage disagrees'):
            self.edit_copy(lambda r: r['sections'][0].update(miles=9))

    def test_reversed_markers_are_rejected(self):
        def change(r):
            e = r['sections'][0]['distanceEvidence']
            e['putIn']['riverMile'], e['takeOut']['riverMile'] = e['takeOut']['riverMile'], e['putIn']['riverMile']
        with self.assertRaisesRegex(ValueError, 'Mileage disagrees'):
            self.edit_copy(change)

    def test_endpoint_change_requires_rechecking_distance(self):
        def change(r):
            r['sections'][0]['distanceEvidence']['putIn']['lat'] += .001
        with self.assertRaisesRegex(ValueError, 'Access coordinates changed'):
            self.edit_copy(change)

    def test_impossible_unsourced_distance_blocks_catalog_build(self):
        def change(r):
            s = r['sections'][0]
            s.pop('distanceEvidence')
            s['miles'] = 1
        with self.assertRaisesRegex(ValueError, 'Impossible mapped mileage'):
            self.edit_copy(change)

    def test_reviewed_conflict_can_publish_information_without_timing(self):
        def change(r):
            s = r['sections'][0]
            s.pop('distanceEvidence')
            s.update(miles=1, distanceReview='Research in progress')
        r = next(r for r in self.edit_copy(change)['rivers'] if r['id']=='blackfoot')
        self.assertIn('Research in progress', seo.river_html(r))

    def test_all_map_links_identify_the_correct_eligible_section(self):
        for r in build()['rivers']:
            page = seo.river_html(r)
            links = re.findall(r'class="section-map-link" href="([^"]+)"', page)
            expected = [s['id'] for s in r['sections'] if s.get('mapReleased')]
            self.assertEqual(len(links), len(expected))
            for link, section in zip(links, expected):
                q = parse_qs(urlsplit(unescape(link)).query)
                self.assertEqual(q['river'], [r['id']])
                self.assertEqual(q['section'], [section])
                self.assertEqual(q['map'], ['1'])
            self.assertNotIn('<iframe', page)

    def test_thibodeau_is_upstream_of_johnsrud_and_holter_is_approximate(self):
        rivers = {r['id']: r for r in build()['rivers']}
        self.assertEqual(rivers['blackfoot']['sections'][1]['difficulty'], 'Class II–III')
        holter = rivers['missouri-craig']['sections'][0]
        self.assertEqual(holter['mapPrecision'], 'approximate')
        self.assertEqual(holter['putInAccess']['status'], 'access-verified')
        self.assertEqual(rivers['stillwater']['sections'][0]['takeOut'], 'Absaroka FAS')
