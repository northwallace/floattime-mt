"""Round-off at a shared source junction must not authorize a real connector."""
import copy,json,tempfile,unittest
from pathlib import Path
from tools.route_catalog import reconstruct_directed_source
class SourceJunctionRoundoffTests(unittest.TestCase):
 def fixture(self,root,delta=0):
  source={'features':[{'attributes':{'permanent_identifier':'up'},'geometry':{'paths':[[[-121,45],[-120.999,45]]]}},{'attributes':{'permanent_identifier':'down'},'geometry':{'paths':[[[-120.999+delta,45],[-120.998,45]]]}}]}
  path=root/'research/source.json';path.parent.mkdir();path.write_text(json.dumps(source))
  return {'source':{'evidenceFile':'research/source.json'},'direction':{'featureIds':['up','down']},'geometry':{'type':'LineString','coordinates':[[-121,45],[-120.999,45],[-120.998,45]]}}
 def test_shared_junction_float_roundoff_preserves_original_route(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);r=self.fixture(root,1e-13);before=copy.deepcopy(r);reconstruct_directed_source(r,root);self.assertEqual(r,before)
 def test_submillimetre_and_larger_gaps_still_fail(self):
  for delta in [1e-10,1e-8,1e-5]:
   with self.subTest(delta=delta),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);r=self.fixture(root,delta)
    with self.assertRaisesRegex(ValueError,'cannot invent connectors'):reconstruct_directed_source(r,root)
 def test_roundoff_permission_cannot_hide_an_edited_route_vertex(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);r=self.fixture(root,1e-13);r['geometry']['coordinates'][1][1]+=.0001
   with self.assertRaisesRegex(ValueError,'original downstream source vertices'):reconstruct_directed_source(r,root)
