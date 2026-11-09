"""Published minima must not become invented maximums or live ETA models."""
import copy, json, tempfile, unittest
from pathlib import Path
import seo
from tools.build_catalog import build
ROOT=Path(__file__).resolve().parents[1]
class OpenEndedGuideTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name); (self.root/'catalog/rivers').mkdir(parents=True)
  settings=json.loads((ROOT/'catalog/settings.json').read_text())
  (self.root/'catalog/settings.json').write_text(json.dumps({k:settings[k] for k in ('states','craft')}))
  self.river=json.loads((ROOT/'catalog/rivers/pine-river-mn.json').read_text())
  for s in self.river['sections']:
   s.pop('putInAccessId');s.pop('takeOutAccessId')
  self.section=self.river['sections'][1]
  self.guide=copy.deepcopy(self.section['guideTimes'][0])
 def built(self):
  (self.root/'catalog/rivers/pine-river-mn.json').write_text(json.dumps(self.river))
  return build(self.root)['rivers'][0]
 def test_explicit_minimum_survives_build_and_server_render_without_live_timing(self):
  r=self.built(); self.assertIsNone(r['sections'][1]['guideTimes'][0]['max'])
  self.assertEqual(r['timing']['mode'],'unavailable');self.assertIsNone(r['gauge'])
  html=seo.river_html(r)
  self.assertIn('6 hours or more',html);self.assertIn('8 hours',html)
 def test_missing_max_and_invalid_bounds_are_rejected(self):
  cases=[{}, {'min':True,'max':None},{'min':0,'max':None},{'min':-2,'max':None},
   {'min':float('nan'),'max':None},{'min':float('inf'),'max':None},
   {'min':6,'max':False},{'min':6,'max':5},{'min':6,'max':float('inf')}]
  for change in cases:
   with self.subTest(change=change):
    g={**self.guide,**change}
    if not change: g.pop('max')
    self.section['guideTimes']=[g]
    with self.assertRaisesRegex(ValueError,'Invalid guide time range'): self.built()
 def test_minima_and_existing_ranges_are_formatted_consistently(self):
  for minimum,unit,expected in [(6,'hours','6 hours or more'),(1,'hours','1 hour or more'),(1.5,'hours','1 hr 30 min or more'),(.5,'hours','30 min or more'),(2,'days','2 days or more')]:
   self.assertEqual(seo._guide_time(dict(min=minimum,max=None,unit=unit)),expected)
  self.assertEqual(seo._guide_time(dict(min=3,max=4,unit='days')),'3–4 days')
  self.assertEqual(seo._guide_time(dict(min=.5,max=.75,unit='hours')),'30–45 min')
