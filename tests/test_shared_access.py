import json, shutil, tempfile, unittest
from pathlib import Path
from tools.build_catalog import build
import seo
ROOT=Path(__file__).resolve().parents[1]
class SharedAccessTests(unittest.TestCase):
 def test_cross_state_uses_original_registry_and_pending_still_blocks(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);shutil.copytree(ROOT/'catalog',root/'catalog');shutil.copytree(Path(__file__).resolve().parents[1]/'research/routes',root/'research/routes')
   def section():return next(r for r in build(root)['rivers'] if r['id']=='colorado-river-ruby-horsethief')['sections'][0]
   self.assertEqual(section()['mapPrecision'],'exact')
   p=root/'catalog/map_points/UT.json';d=json.loads(p.read_text());d['points']['Westwater Ranger Station Boat Ramp']={'status':'pending','note':'Closed for review'}
   # Its original Utah river must also lose its fully-verified audit.
   for a in d['auditedRivers'].values():a['status']='pending'
   p.write_text(json.dumps(d));self.assertNotIn('mapPilot',section());self.assertIn('Closed for review',section()['mapPendingReason'])
 def test_invalid_reference_is_not_silently_guessed(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);shutil.copytree(ROOT/'catalog',root/'catalog');shutil.copytree(Path(__file__).resolve().parents[1]/'research/routes',root/'research/routes');p=root/'catalog/rivers/colorado-river-ruby-horsethief.json';d=json.loads(p.read_text());d['sections'][0]['takeOutPoint']['name']='Missing';p.write_text(json.dumps(d))
   with self.assertRaisesRegex(ValueError,'Unknown endpoint reference'):build(root)
 def test_notices_appear_in_guide_and_unsafe_source_is_rejected(self):
  rivers={r['id']:r for r in build()['rivers']};page=seo.river_html(rivers['yampa-river-dinosaur']);self.assertIn('Deerlodge takeout permit',page)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);shutil.copytree(ROOT/'catalog',root/'catalog');shutil.copytree(Path(__file__).resolve().parents[1]/'research/routes',root/'research/routes');p=root/'catalog/rivers/yampa-river-dinosaur.json';d=json.loads(p.read_text());d['sections'][0]['notices'][0]['sourceUrl']='javascript:alert(1)';p.write_text(json.dumps(d))
   with self.assertRaisesRegex(ValueError,'Notice source must use HTTPS'):build(root)
