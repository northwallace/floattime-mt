"""Evidence-backed White River paths must preserve the existing trip contract."""
import hashlib,json
from pathlib import Path
import unittest
from tools.build_catalog import build
from tools.route_catalog import validate

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'research/white-river-courses-20261109'

class WhiteRiverCourseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=build()
        cls.before=json.loads((B/'before/catalog.json').read_text())
        cls.decisions=json.loads((B/'decisions.json').read_text())['routes']

    def test_approved_paths_keep_access_pins_distances_and_gauge_models(self):
        rows=[r for r in self.decisions if r['decision']=='reviewed-display-only']
        self.assertEqual(len(rows),8)
        for row in rows:
            record=json.loads((ROOT/row['route']['file']).read_text());validate(record,self.catalog,ROOT)
            river=next(r for r in self.catalog['rivers'] if r['id']==row['riverId'])
            before=next(r for r in self.before['rivers'] if r['id']==row['riverId'])
            for key in ('gauge','timing','refFlowCfs','refSpeedMph'):
                self.assertEqual(river.get(key),before.get(key))
            section=next(s for s in river['sections'] if s['id']==row['sectionId'])
            original=next(s for s in before['sections'] if s['id']==row['sectionId'])
            for key in ('miles','putInCoords','takeOutCoords','putInAccessId','takeOutAccessId'):
                self.assertEqual(section[key],original[key])
            self.assertEqual(record['features'],dict(display=True,landOverlay=False,distanceEstimate=False,remainingTime=False))
            self.assertEqual(record['scope'],'river-course-overview')
            source=json.loads((ROOT/record['source']['evidenceFile']).read_text())
            self.assertEqual(source['queryPolicy'],'named-and-unnamed-flowlines-v1')
            self.assertTrue(source['archives'])
            self.assertTrue(any(f['attributes']['gnis_name'] in (None,'') for f in source['features']))

    def test_former_bank_mismatch_requires_the_later_recorded_course_review(self):
        held=[r for r in self.decisions if r['decision']=='needs-course-refinement']
        self.assertEqual([r['sectionId'] for r in held],['bertrand-boat-ramp-to-houseman-boat-ramp'])
        index=json.loads((ROOT/'public/routes/index.json').read_text())['routes']
        row=next(r for r in index if r['riverId']=='white-river-beaver-tailwater' and r['sectionId']==held[0]['sectionId'])
        path=ROOT/'catalog/routes/AR'/Path(row['file']).name
        later=json.loads((ROOT/'research/arkansas-tailwater-courses-20261109/decisions.json').read_text())
        review=next(x for x in later['courses'] if x['route']['file']==str(path.relative_to(ROOT)))
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),review['route']['sha256'])
        route=json.loads(path.read_text());validate(route,self.catalog,ROOT)
        self.assertEqual(route['scope'],'river-course-overview')
        self.assertEqual(route['features'],dict(display=True,landOverlay=False,distanceEstimate=False,remainingTime=False))
        self.assertEqual(route['review']['evidenceFile'],'research/arkansas-tailwater-courses-20261109/decisions.json')
        self.assertTrue(all(x['status']=='not-mapped' for x in route['overviewReview']['connections'].values()))

    def test_courses_match_original_unique_downstream_chains(self):
        try:
            from tools.import_nhd_routes import network,directed_route
            from pyproj import Transformer
        except ImportError:self.skipTest('Development GIS dependencies required')
        project=Transformer.from_crs(4326,5070,always_xy=True).transform
        unproject=Transformer.from_crs(5070,4326,always_xy=True).transform
        for row in self.decisions:
            if row['decision']!='reviewed-display-only':continue
            r=json.loads((ROOT/row['route']['file']).read_text())
            source=json.loads((ROOT/r['source']['evidenceFile']).read_text())
            river=next(v for v in self.catalog['rivers'] if v['id']==r['riverId'])
            section=next(s for s in river['sections'] if s['id']==r['sectionId'])
            edges,adj=network(source,project)
            geometry,direction=directed_route(edges,adj,section,project,unproject,overview=True)
            self.assertEqual(json.loads(json.dumps(geometry)),r['geometry'])
            self.assertEqual(direction,r['direction'])
