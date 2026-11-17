"""Separate the documented lower Plover outing from the unresolved through-trip."""
import hashlib,json,unittest
from pathlib import Path
from tools.build_catalog import build
ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'research/plover-access-courses-20261116'
class PloverAccessReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if not (B/'decisions.json').exists():raise unittest.SkipTest('Local Plover review evidence is not packaged')
  cls.catalog=build();cls.river=next(r for r in cls.catalog['rivers'] if r['id']=='plover-river');cls.sections={s['id']:s for s in cls.river['sections']};cls.new=cls.sections['jordan-below-dam-to-iverson-park']
 def test_lower_outing_does_not_clear_original_dam_crossing(self):
  old=self.sections['plover-river-wayside-canoe-launch-to-lehner-landing']
  self.assertFalse(old['mapReleased']);self.assertIn('Jordan',old['accessReview']);self.assertIn('McDill',old['accessReview'])
  self.assertTrue(self.new['mapReleased']);self.assertEqual(self.new['mapPrecision'],'approximate')
  self.assertEqual(self.river['timing']['mode'],'unavailable')
 def test_published_duration_is_not_a_new_live_model_or_mapped_distance(self):
  self.assertEqual(self.new['miles'],7.75);g=self.new['guideTimes'][0];self.assertEqual((g['min'],g['max'],g['unit']),(3,3,'hours'))
  self.assertIn('not a live estimate',g['conditions']);self.assertEqual(self.new['distanceEvidence']['method'],'published-trip-length')
  self.assertIsNone(self.river['refSpeedMph']);self.assertIsNone(self.river['refFlowCfs'])
 def test_area_markers_preserve_the_county_putin_and_explain_manual_beach_placement(self):
  p=json.loads((ROOT/'catalog/map_points/WI.json').read_text())['points'];m=json.loads((B/'point-methods.json').read_text())
  for name in ['Jordan Park Below-Dam Canoe Launch','Iverson Park Beach Access']:
   row=p[name];self.assertEqual(row['status'],'access-verified');self.assertNotIn('lat',row);self.assertNotIn('riverBank',row)
   for k,v in m['points'][name].items():self.assertEqual(row['areaCenter'][k],v)
  self.assertIn('not an agency landing coordinate',p['Iverson Park Beach Access']['note'])
  self.assertNotEqual(self.new['putInAccessId'],self.sections['plover-river-wayside-canoe-launch-to-lehner-landing']['putInAccessId'])
 def test_visibly_misaligned_candidate_does_not_leak_into_public_routes(self):
  candidate=json.loads((B/'candidate.json').read_text());self.assertEqual(candidate['status'],'candidate');self.assertFalse(any(candidate['features'].values()))
  index=json.loads((ROOT/'public/routes/index.json').read_text())['routes'];self.assertFalse(any(x['riverId']=='plover-river' and x['sectionId']==self.new['id'] for x in index))
  self.assertFalse((ROOT/'public/routes/plover-river--jordan-below-dam-to-iverson-park.json').exists())
  review=json.loads((B/'full-course-review.json').read_text());self.assertEqual(review['decision'],'hold-course-only');self.assertEqual(review['county2025CoursePanels'],15)
  for row in review['imagery']:self.assertEqual(hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest(),row['sha256'])
