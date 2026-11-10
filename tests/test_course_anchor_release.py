"""Production guardrails for reviewed source anchors; no GIS runtime needed."""
import copy,json,unittest
from pathlib import Path
from tools.build_catalog import build
from tools.route_catalog import validate,review_signature,geometry_checks
ROOT=Path(__file__).resolve().parents[1]
class CourseAnchorReleaseTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=build();cls.record=json.loads((ROOT/'catalog/routes/WY/north-fork-shoshone--libby-creek-aka-white-rocks-to-newton-creek.json').read_text())
 def test_anchor_evidence_and_display_only_boundary_are_enforced(self):
  validate(self.record,self.catalog,ROOT)
  for kind in ('feature','imagery','scope','remainingTime','distanceEstimate','landOverlay'):
   route=copy.deepcopy(self.record)
   if kind=='feature':route['courseAnchors']['putIn']['featureId']='not-the-reviewed-source'
   elif kind=='imagery':route['courseAnchors']['putIn']['imageryEvidence'][0]['sha256']='0'*64
   elif kind=='scope':route['scope']='landing-to-landing'
   else:route['features'][kind]=True
   route['overviewReview']['signature']=review_signature(route)
   with self.subTest(kind=kind),self.assertRaises(ValueError):validate(route,self.catalog,ROOT)
 def test_resigning_geometry_does_not_allow_a_synthetic_path(self):
  route=copy.deepcopy(self.record);route['geometry']['coordinates'][4][0]+=.0002
  metrics,issues=geometry_checks(route);route['checks']=dict(metrics=metrics,issues=issues)
  route['overviewReview']['signature']=review_signature(route)
  with self.assertRaisesRegex(ValueError,'original downstream source'):validate(route,self.catalog,ROOT)
