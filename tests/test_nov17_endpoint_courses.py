"""Facility orientation does not establish through-dam or falls navigation."""
import copy,hashlib,json,unittest
from pathlib import Path
from tools.build_catalog import build
from tools.route_catalog import validate,reconstruct_directed_source
from tests.later_catalog_reviews import before_nov17_endpoint_course_review
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'research/white-salmon-course-20261117';W=ROOT/'research/wisconsin-endpoint-recheck-20261117'
def read(p):return json.loads(p.read_text())
class NovemberEndpointCourseTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if not (B/'decisions.json').exists():raise unittest.SkipTest('Local November 17 evidence not packaged')
  cls.catalog=build();cls.rivers={r['id']:r for r in cls.catalog['rivers']};cls.route=read(ROOT/'catalog/routes/WA/white-salmon--bz-husum.json')
 def test_white_salmon_uses_main_river_without_changing_source_vertices(self):
  r=self.route;validate(r,self.catalog,ROOT);reconstruct_directed_source(r,ROOT)
  self.assertNotIn('150802399',r['direction']['featureIds'])
  self.assertEqual(r['direction']['featureIds'][0],'{7D1BFB42-7D72-4B66-BCF5-8A478FC61A96}')
  for side,p in r['overviewReview']['connections'].items():self.assertEqual(p['status'],'not-mapped')
  self.assertEqual(r['features'],dict(display=True,landOverlay=False,distanceEstimate=False,remainingTime=False))
  s=self.rivers['white-salmon']['sections'][0];self.assertIn('ABOVE Class V Husum Falls',s['routeReview']);self.assertEqual(s['miles'],4.4)
 def test_anchor_cannot_reuse_missing_or_changed_imagery(self):
  r=copy.deepcopy(self.route);r['courseAnchors']['putIn']['imageryEvidence'][0]['sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'imagery changed'):validate(r,self.catalog,ROOT)
 def test_mullet_map_is_not_a_through_dam_or_timing_approval(self):
  r=self.rivers['mullet-river'];s=r['sections'][0];self.assertTrue(s['mapReleased']);self.assertEqual(s['mapPrecision'],'approximate');self.assertTrue(s['distanceReview']);self.assertEqual(r['timing']['mode'],'unavailable');self.assertIn('water-control outlet',s['notes']);self.assertIn('drawdowns',s['notes']);self.assertFalse((ROOT/'public/routes'/('mullet-river--'+s['id']+'.json')).exists())
  before=read(W/'before/catalog/map_points/WI.json')['points'];after=read(ROOT/'catalog/map_points/WI.json')['points']
  for name in ['Deerview Drive Bridge Access','Hwy G Flowage']:
   for k in ['id','areaCenter','status']:self.assertEqual(after[name][k],before[name][k])
  bridge=self.rivers['bridge-creek']['sections'][0];self.assertFalse(bridge['mapReleased']);self.assertIn('above Dells Mill Dam',bridge['accessReview'])
 def test_review_frames_are_hash_bound_and_later_exemption_is_exact(self):
  full=read(B/'course/full-course-review.json');self.assertEqual(len(full['imagery']),11)
  for row in full['imagery']:self.assertEqual(hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest(),row['imageSha256'])
  rows=read(B/'normalized-later-changes.json');self.assertEqual({x['id'] for x in rows},{'mullet-river','bridge-creek','white-salmon'})
  for row in rows:
   self.assertEqual(before_nov17_endpoint_course_review(row['after']),row['before'])
   changed=copy.deepcopy(row['after']);changed['gauge']='12345678';self.assertEqual(before_nov17_endpoint_course_review(changed),changed)
