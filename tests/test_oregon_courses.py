"""Oregon course rollout preserves access precision, timing and source geometry."""
import copy
import json
from pathlib import Path
import unittest
from tools.build_catalog import build
from tools.route_catalog import validate

ROOT=Path(__file__).resolve().parents[1]

class OregonCourseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=build()
        cls.river=next(r for r in cls.catalog['rivers'] if r['id']=='deschutes-maupin')

    def test_deschutes_is_display_only_with_original_endpoints_and_mileage(self):
        before=json.loads((ROOT/'research/oregon-courses-20261109/before/public/catalog.json').read_text())
        old=next(r for r in before['rivers'] if r['id']=='deschutes-maupin')
        for section in self.river['sections']:
            prior=next(s for s in old['sections'] if s['id']==section['id'])
            for key in ('miles','putInCoords','takeOutCoords','putInAccessId','takeOutAccessId'):
                self.assertEqual(section[key],prior[key])
            record=json.loads((ROOT/('catalog/routes/OR/deschutes-maupin--'+section['id']+'.json')).read_text())
            validate(record,self.catalog,ROOT)
            self.assertEqual(record['scope'],'river-course-overview')
            self.assertEqual(record['features'],dict(display=True,landOverlay=False,distanceEstimate=False,remainingTime=False))
            self.assertTrue(all(c['status']=='not-mapped' for c in record['overviewReview']['connections'].values()))
            bad=copy.deepcopy(record);bad['geometry']['coordinates'][2][0]+=.001
            with self.assertRaises(ValueError):validate(bad,self.catalog,ROOT)

    def test_sherars_exit_notice_and_closed_sandy_access_remain(self):
        sandy_beach=next(s for s in self.river['sections'] if s['id']=='maupin-sandy-beach')
        self.assertTrue(any('Sherars' in n['title'] for n in sandy_beach['notices']))
        sandy=next(r for r in self.catalog['rivers'] if r['id']=='sandy')
        self.assertTrue(all(not s.get('mapReleased') for s in sandy['sections']))
        index=json.loads((ROOT/'catalog/routes/OR.json').read_text())
        self.assertFalse(any('/sandy--' in p for p in index['routes']))

    def test_deschutes_reconstructs_from_original_downstream_source(self):
        try:
            from pyproj import Transformer
            from tools.import_nhd_routes import network,directed_route
        except ImportError:self.skipTest('Development GIS dependencies required')
        project=Transformer.from_crs(4326,5070,always_xy=True).transform
        unproject=Transformer.from_crs(5070,4326,always_xy=True).transform
        for section in self.river['sections']:
            route=json.loads((ROOT/('catalog/routes/OR/deschutes-maupin--'+section['id']+'.json')).read_text())
            source=json.loads((ROOT/route['source']['evidenceFile']).read_text())
            edges,adj=network(source,project)
            geometry,direction=directed_route(edges,adj,section,project,unproject,overview=True)
            self.assertEqual(json.loads(json.dumps(geometry)),route['geometry'])
            self.assertEqual(direction,route['direction'])
