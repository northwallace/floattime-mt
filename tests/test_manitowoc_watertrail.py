"""Agency segment distances must retain explicit downstream order and source fidelity."""
import copy,json,unittest
from pathlib import Path
from tools.build_catalog import build
from tools.agency_courses import validate_agency_course,signature
from tools.route_catalog import validate
ROOT=Path(__file__).resolve().parents[1]
class ManitowocWaterTrailTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=build()
  cls.river=next(r for r in cls.catalog['rivers'] if r['id']=='manitowoc-river')
  cls.section=next(s for s in cls.river['sections'] if s['id']=='clarks-mills-below-dam-to-lower-cato-falls')
  cls.record=json.loads((ROOT/'catalog/routes/WI/manitowoc-river--clarks-mills-below-dam-to-lower-cato-falls.json').read_text())
  cls.payload=json.loads((ROOT/cls.record['source']['evidenceFile']).read_text())
 def test_published_length_uses_distinct_below_dam_access_and_preserves_original_hold(self):
  validate(self.record,self.catalog,ROOT)
  old=next(s for s in self.river['sections'] if s['id']=='clarks-mills-pond-ramp-to-manitou-city-park-boat-ramp')
  self.assertFalse(old['mapReleased']);self.assertTrue(self.section['mapReleased'])
  self.assertNotEqual(old['putInAccessId'],self.section['putInAccessId'])
  self.assertEqual(self.section['miles'],1.2)
  self.assertEqual(self.section['distanceEvidence']['method'],'published-trip-length')
  self.assertTrue(all('riverMile' not in self.section['distanceEvidence'][side] for side in ['putIn','takeOut']))
  self.assertFalse(self.record['features']['remainingTime']);self.assertFalse(self.record['features']['distanceEstimate'])
 def test_trip_distance_alone_cannot_establish_downstream_order(self):
  for mutation in ['missing','reversed','unlocated','generic']:
   s=copy.deepcopy(self.section);r=copy.deepcopy(self.record);e=s['distanceEvidence'];order=e['downstreamOrder']
   if mutation=='missing':del e['downstreamOrder']
   if mutation=='reversed':order['putIn'],order['takeOut']=order['takeOut'],order['putIn']
   if mutation=='unlocated':order['sourceLocation']=''
   if mutation=='generic':order['kind']='nearby-water'
   r['direction']['tripEvidenceSha256']=signature(e)
   with self.subTest(mutation=mutation),self.assertRaisesRegex(ValueError,'downstream'):
    validate_agency_course(r,s,self.payload,ROOT)
 def test_changed_trip_length_or_geometry_cannot_be_resigned_into_release(self):
  s=copy.deepcopy(self.section);r=copy.deepcopy(self.record);s['distanceEvidence']['miles']=2
  r['direction']['tripEvidenceSha256']=signature(s['distanceEvidence'])
  with self.assertRaisesRegex(ValueError,'length changed'):validate_agency_course(r,s,self.payload,ROOT)
  r=copy.deepcopy(self.record);r['geometry']['coordinates'][4][0]+=.0001
  with self.assertRaisesRegex(ValueError,'differs from its source'):validate_agency_course(r,self.section,self.payload,ROOT)
 def test_steep_carry_and_seasonal_access_survive_the_catalog(self):
  self.assertIn('Class II',self.section['difficulty'])
  self.assertTrue(any('April 1' in n['text'] and 'October 31' in n['text'] for n in self.section['notices']))
  self.assertIn('steep',self.section['notes'])
