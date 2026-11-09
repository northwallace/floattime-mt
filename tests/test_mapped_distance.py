"""Mapped mileage is reproducible evidence, not an automatic map/timing approval."""
import copy
import hashlib
import math
from pathlib import Path
import tempfile
import unittest
from tools.build_catalog import validate_distance_evidence
from tools.mapped_distance import ALGORITHM
import seo


class MappedDistanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'research').mkdir()
        # One degree of longitude along the equator has an independent analytic length.
        miles = 6371008.8 * math.pi / 180 / 1609.344
        self.section = dict(putIn='Start', takeOut='End', miles=round(miles, 1),
            putInCoords=dict(lon=0, lat=0), takeOutCoords=dict(lon=1, lat=0),
            distanceEvidence=dict(method='mapped-course-length', sourceName='Published test map',
                sourceUrl='https://example.org/map', checkedOn='2026-11-06', streamId='Test river',
                note='Measured approximate planning miles, not a published numeric trip length.',
                putIn=dict(name='Start', lon=0, lat=0, sourceLocation='Start marker'),
                takeOut=dict(name='End', lon=1, lat=0, sourceLocation='End marker'),
                measurement=dict(format='kml', algorithm=ALGORITHM, evidenceFile='research/map.kml',
                    featureName='Trip', measuredMiles=miles, reviewNote='Reviewed endpoints and complete course.')))
        self.write_kml()

    def write_kml(self, coordinates='0,0 0.5,0 1,0', extra='', declarations=''):
        raw = (declarations + '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
            '<Placemark><name>Trip</name><LineString><coordinates>' + coordinates +
            '</coordinates></LineString></Placemark>' + extra + '</Document></kml>').encode()
        (self.root/'research/map.kml').write_bytes(raw)
        self.section['distanceEvidence']['measurement']['sha256'] = hashlib.sha256(raw).hexdigest()

    def validate(self):
        validate_distance_evidence(self.section, 'test: ', self.root)

    def test_known_length_validates_without_changing_access_or_timing(self):
        before = copy.deepcopy(self.section)
        self.validate()
        self.assertEqual(self.section, before)
        self.assertNotIn('mapReleased', self.section)
        self.assertNotIn('timing', self.section)
        html = seo._distance_html(self.section)
        self.assertIn('Measured from published map: approximately', html)
        self.assertNotIn('River mile', html)
        self.assertNotIn('Published trip length', html)

    def test_source_edit_requires_review_even_when_geometry_still_looks_valid(self):
        p = self.root/'research/map.kml'
        p.write_bytes(p.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'changed; re-review'): self.validate()

    def test_ambiguous_or_absent_named_feature_is_rejected(self):
        self.write_kml(extra='<Placemark><name>Trip</name></Placemark>')
        with self.assertRaisesRegex(ValueError, 'unique'): self.validate()
        self.write_kml()
        self.section['distanceEvidence']['measurement']['featureName'] = 'Another trip'
        with self.assertRaisesRegex(ValueError, 'unique'): self.validate()

    def test_nonfinite_out_of_bounds_and_zero_length_geometry_is_rejected(self):
        for coords in ['0,0 NaN,0', '0,0 181,0', '0,0 0,91', '0,0 0,0']:
            with self.subTest(coords=coords):
                self.write_kml(coords)
                with self.assertRaises(ValueError): self.validate()

    def test_escaped_path_and_symlink_are_rejected(self):
        m = self.section['distanceEvidence']['measurement']
        outside = self.root/'outside.kml'
        outside.write_bytes((self.root/'research/map.kml').read_bytes())
        for name in ['research/../outside.kml', str(outside)]:
            m['evidenceFile'] = name
            with self.assertRaisesRegex(ValueError, 'research/'): self.validate()
        (self.root/'research/link.kml').symlink_to(outside)
        m['evidenceFile'] = 'research/link.kml'
        with self.assertRaisesRegex(ValueError, 'research/'): self.validate()

    def test_changed_access_or_reversed_line_requires_review(self):
        self.section['putInCoords']['lon'] = .001
        with self.assertRaisesRegex(ValueError, 'coordinates changed'): self.validate()
        self.section['putInCoords']['lon'] = 0
        self.write_kml('1,0 0.5,0 0,0')
        with self.assertRaisesRegex(ValueError, 'endpoint or downstream order'): self.validate()

    def test_miles_and_review_note_cannot_drift(self):
        good = copy.deepcopy(self.section)
        for field, value in [('measuredMiles', 80), ('reviewNote', ''), ('algorithm', 'unknown')]:
            with self.subTest(field=field):
                self.section = copy.deepcopy(good)
                self.section['distanceEvidence']['measurement'][field] = value
                with self.assertRaises(ValueError): self.validate()
        self.section = copy.deepcopy(good)
        self.section['miles'] = 80
        with self.assertRaisesRegex(ValueError, 'Mileage disagrees'): self.validate()

    def test_xml_entities_are_not_accepted(self):
        self.write_kml(declarations='<!DOCTYPE kml [<!ENTITY x "unsafe">]>')
        with self.assertRaisesRegex(ValueError, 'declarations'): self.validate()


if __name__ == '__main__': unittest.main()
