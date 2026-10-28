"""Build-time GIS checks; skipped in the package-free production environment."""
import json
import unittest
from pathlib import Path

try:
    from shapely.geometry import Polygon, shape
    from shapely.ops import transform
    from pyproj import Transformer
    from tools.build_route_land import normalize_land_polygon
    HAS_GIS = True
except ImportError:
    HAS_GIS = False


@unittest.skipUnless(HAS_GIS, 'Run with the development GIS environment')
class LandGeometryTests(unittest.TestCase):
    def test_valid_boundary_is_unchanged(self):
        original = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
        result, evidence = normalize_land_polygon(original)
        self.assertIs(result, original)
        self.assertIsNone(evidence)

    def test_area_changing_bow_tie_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'boundary review'):
            normalize_land_polygon(Polygon([(0, 0), (5, 5), (0, 5), (5, 0)]))

    def test_saved_madison_self_touch_preserves_land_and_boundary(self):
        root = Path(__file__).resolve().parents[1]
        files = list((root / 'research/routes/MT/land/madison-upper--mcatee-varney').glob('*/layer-1.json'))
        self.assertEqual(len(files), 1)
        feature = next(f for f in json.loads(files[0].read_text())['response']['features']
                       if str(f['properties']['TractID']) == '11955')
        original = transform(Transformer.from_crs(4326, 32612, always_xy=True).transform,
                             shape(feature['geometry']))
        self.assertFalse(original.is_valid)
        result, evidence = normalize_land_polygon(original)
        self.assertTrue(result.is_valid)
        self.assertLess(abs(result.area - original.area), .001)
        self.assertEqual(result.boundary.difference(original.boundary).length, 0)
        self.assertEqual(evidence['method'], 'remove-zero-area-self-touch')
