"""Sparse NHD lake courses require source fidelity and display-only review."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from tools.build_catalog import build
from tools.route_catalog import validate,review_signature,geometry_checks,reviewed_source_segments
ROOT=Path(__file__).resolve().parents[1]
class NhdSourceSegmentTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=build()
  cls.record=json.loads((ROOT/'catalog/routes/WI/yahara-river--yahara-river-to-lottes-park-boat-launch.json').read_text())
 def test_reviewed_lake_chord_exports_only_its_display_metadata(self):
  _,metrics=validate(self.record,self.catalog,ROOT)
  self.assertEqual(reviewed_source_segments(self.record,ROOT),[16])
  self.assertAlmostEqual(metrics['maxSegmentMeters'],1029.5,places=1)
  public=json.loads((ROOT/'public/routes/yahara-river--yahara-river-to-lottes-park-boat-launch.json').read_text())
  self.assertEqual(public['overview']['longSourceSegments'],[16])
  self.assertNotIn('sourceSegmentReview',public)
  self.assertEqual(public['features'],dict(display=True,landOverlay=False,distanceEstimate=False,remainingTime=False))
 def test_resigning_an_edited_lake_line_does_not_waive_source_reconstruction(self):
  r=copy.deepcopy(self.record);r['geometry']['coordinates'][16][0]+=.0001
  metrics,issues=geometry_checks(r);r['checks']=dict(metrics=metrics,issues=issues);r['overviewReview']['signature']=review_signature(r)
  with self.assertRaisesRegex(ValueError,'original downstream source vertices'):validate(r,self.catalog,ROOT)
 def test_incomplete_or_changed_source_snapshot_cannot_qualify(self):
  for mutation in ['coverage','hash']:
   r=copy.deepcopy(self.record);payload=json.loads((ROOT/r['source']['evidenceFile']).read_text())
   if mutation=='coverage':payload.pop('queryPolicy')
   raw=json.dumps(payload).encode()
   with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);p=root/r['source']['evidenceFile'];p.parent.mkdir(parents=True);p.write_bytes(raw)
    r['source']['sha256']=hashlib.sha256(raw).hexdigest() if mutation=='coverage' else '0'*64
    with self.assertRaisesRegex(ValueError,'source coverage|source evidence changed'):reviewed_source_segments(r,root)
 def test_review_cannot_enable_land_or_timing_capabilities(self):
  for feature in ['landOverlay','distanceEstimate','remainingTime']:
   r=copy.deepcopy(self.record);r['features'][feature]=True
   with self.subTest(feature=feature),self.assertRaisesRegex(ValueError,'display only'):reviewed_source_segments(r,ROOT)
