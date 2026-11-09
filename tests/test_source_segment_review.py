"""Long agency segments need bounded evidence, never a general gap override."""
import copy,json
from pathlib import Path
import unittest
from tools.build_catalog import build
from tools.route_catalog import validate,review_signature,reviewed_source_segments
ROOT=Path(__file__).resolve().parents[1]
class SourceSegmentReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=build()
  cls.record=json.loads((ROOT/'catalog/routes/MN/root-river-mn--hokah-highway26.json').read_text())
 def test_reviewed_original_straight_segment_is_display_only(self):
  _,metrics=validate(self.record,self.catalog,ROOT)
  self.assertAlmostEqual(metrics['maxSegmentMeters'],1583.5,places=1)
  self.assertEqual(reviewed_source_segments(self.record,ROOT),[35])
  public=json.loads((ROOT/'public/routes/root-river-mn--hokah-highway26.json').read_text())
  self.assertEqual(public['overview']['longSourceSegments'],[35])
  self.assertNotIn('sourceSegmentReview',public)
  self.assertEqual(public['features'],dict(display=True,remainingTime=False,distanceEstimate=False,landOverlay=False))
 def test_missing_extra_duplicate_or_changed_evidence_fails(self):
  for change in ['missing','empty','duplicate','wrong-index','boolean','hash','non-image']:
   r=copy.deepcopy(self.record)
   if change=='missing':r.pop('sourceSegmentReview')
   if change=='empty':r['sourceSegmentReview']=[]
   if change=='duplicate':r['sourceSegmentReview']*=2
   if change=='wrong-index':r['sourceSegmentReview'][0]['segment']=34
   if change=='boolean':r['sourceSegmentReview'][0]['segment']=True
   if change=='hash':r['sourceSegmentReview'][0]['imageryEvidence'][0]['sha256']='0'*64
   if change=='non-image':r['sourceSegmentReview'][0]['imageryEvidence'][0]['file']=r['source']['evidenceFile']
   r['overviewReview']['signature']=review_signature(r)
   with self.subTest(change=change),self.assertRaises(ValueError):validate(r,self.catalog,ROOT)
 def test_source_geometry_and_review_remain_bound(self):
  r=copy.deepcopy(self.record);r['sourceSegmentReview'][0]['note']+=' altered'
  with self.assertRaisesRegex(ValueError,'changed'):validate(r,self.catalog,ROOT)
  r=copy.deepcopy(self.record);r['geometry']['coordinates'][35][1]+=.0001
  r['overviewReview']['signature']=review_signature(r)
  with self.assertRaisesRegex(ValueError,'differs from its source'):validate(r,self.catalog,ROOT)
 def test_exception_never_accepts_duplicates_unbounded_segments_or_other_methods(self):
  for change in ['duplicate','too-long','other-source','landing-route']:
   r=copy.deepcopy(self.record)
   if change=='duplicate':r['geometry']['coordinates'][1]=r['geometry']['coordinates'][0]
   if change=='too-long':r['geometry']['coordinates'][36][0]+=.03
   if change=='other-source':r['direction']['method']='usgs-flow-directed-network'
   if change=='landing-route':r['scope']='landing-to-landing'
   with self.subTest(change=change),self.assertRaises(ValueError):reviewed_source_segments(r,ROOT)
