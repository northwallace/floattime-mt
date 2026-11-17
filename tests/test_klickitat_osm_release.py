"""The reviewed OSM pilot preserves source nodes, imagery and display-only limits."""
import copy,hashlib,json,unittest
from pathlib import Path
from tools.osm_courses import validate_osm_course,LICENSE
ROOT=Path(__file__).resolve().parents[1]
class KlickitatOsmReleaseTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.record=json.loads((ROOT/'catalog/routes/WA/klickitat--leidl-icehouse.json').read_text())
  cls.raw=(ROOT/cls.record['source']['evidenceFile']).read_bytes()
 def test_real_review_reconstructs_and_keeps_full_frame_evidence(self):
  r=self.record;validate_osm_course(r,self.raw,ROOT)
  self.assertEqual(hashlib.sha256(self.raw).hexdigest(),r['source']['sha256'])
  full=json.loads((ROOT/r['osmReview']['fullCourse']['file']).read_text())
  self.assertEqual(len(full['imagery']),34)
  self.assertEqual(r['features'],dict(display=True,landOverlay=False,distanceEstimate=False,remainingTime=False))
 def test_changed_geometry_or_review_cannot_reuse_pilot_approval(self):
  for kind in ['geometry','frame','license','version']:
   r=copy.deepcopy(self.record)
   if kind=='geometry':r['geometry']['coordinates'][10][1]+=.0001
   elif kind=='frame':r['osmReview']['fullCourse']['sha256']='0'*64
   elif kind=='license':r['license']['attribution']='Someone else'
   else:r['direction']['parts'][0]['wayVersion']+=1
   with self.subTest(kind=kind),self.assertRaises(ValueError):validate_osm_course(r,self.raw,ROOT)
 def test_public_export_has_credit_and_never_claims_navigation(self):
  r=json.loads((ROOT/'public/routes/klickitat--leidl-icehouse.json').read_text())
  self.assertEqual(r['license'],LICENSE)
  self.assertEqual(r['scope'],'river-course-overview')
  self.assertFalse(any(r['features'][k] for k in ['landOverlay','distanceEstimate','remainingTime']))
  self.assertIn('bank',r['note'])
