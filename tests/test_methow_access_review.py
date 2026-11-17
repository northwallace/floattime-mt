"""Documented facility areas must not acquire precise landing or timing claims."""
import hashlib
import json
import unittest
from pathlib import Path
from tools.build_catalog import build
from tests.later_catalog_reviews import before_nov17_endpoint_course_review
ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'research/washington-access-recheck-20261117'
class MethowAccessReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if not (B/'decisions.json').exists():raise unittest.SkipTest('Local Methow evidence is not packaged')
  cls.catalog=build();cls.old=json.loads((B/'before/public/catalog.json').read_text());cls.rivers={r['id']:r for r in cls.catalog['rivers']};cls.points=json.loads((ROOT/'catalog/map_points/WA.json').read_text())['points'];cls.old_points=json.loads((B/'before/catalog/map_points/WA.json').read_text())['points']
 def test_three_documented_facilities_keep_ids_and_approximate_precision(self):
  for name in ['Red Barn Access (Winthrop)','Big Eddy (Methow)','Twisp Access']:
   p=self.points[name]
   with self.subTest(name=name):
    self.assertEqual(p['id'],self.old_points[name]['id']);self.assertEqual(p['status'],'access-verified');self.assertNotIn('lat',p);self.assertNotIn('lon',p);self.assertTrue(p['areaCenter']['feature']);self.assertFalse(any(k=='riverBank' or k.startswith('bank') for k in p));self.assertTrue(p['coordinateSourceUrl'].startswith('https://'))
 def test_access_maps_do_not_create_boat_ramps_or_live_calibration(self):
  r=self.rivers['methow-upper'];self.assertEqual(r['timing']['mode'],'unavailable')
  for s in r['sections']:
   self.assertTrue(s['mapReleased']);self.assertEqual(s['mapPrecision'],'approximate');self.assertIn('steep',s['notes'].lower());self.assertIn('carry',s['notes'].lower())
  self.assertIn('not a boat ramp',self.points['Big Eddy (Methow)']['directions']);self.assertIn('no larger-watercraft put-in',self.points['Twisp Access']['directions'])
 def test_historical_proposal_is_not_the_completion_evidence(self):
  d=json.loads((B/'decisions.json').read_text());self.assertTrue(d['asBuiltLabelNotTreatedAsProof']);self.assertTrue(d['oldConstructionHoldReplacedByAcceptedCompletionEvidence'])
  self.assertIn('Water access ramp and bank', (B/'mack-lloyd-progress-20241218-1.txt').read_text())
  self.assertIn('complete', (B/'mack-lloyd-progress-20241218-1.txt').read_text())
  for proof in d['imageryAndSourceProof']:self.assertEqual(hashlib.sha256((ROOT/proof['file']).read_bytes()).hexdigest(),proof['sha256'])
 def test_all_other_rivers_and_existing_models_distances_and_access_ids_preserved(self):
  changed=[]
  for old in self.old['rivers']:
   r=before_nov17_endpoint_course_review(self.rivers[old['id']])
   if r!=old:changed.append(r['id'])
   for k in ['gauge','usgsSite','flowSource','refFlowCfs','refSpeedMph','timing']:self.assertEqual(r.get(k),old.get(k),(r['id'],k))
   self.assertEqual([s['id'] for s in r['sections']],[s['id'] for s in old['sections']])
   for s,o in zip(r['sections'],old['sections']):
    for k in ['miles','putInAccessId','takeOutAccessId']:self.assertEqual(s.get(k),o.get(k),(r['id'],s['id'],k))
    if r['id']!='methow-upper':self.assertEqual(s['mapReleased'],o['mapReleased'])
  self.assertEqual(set(changed),{'big-hole','methow-upper'})
 def test_bad_big_hole_source_course_is_not_exported(self):
  b=ROOT/'research/big-hole-courses-20261117';r=json.loads((b/'courses/divide-melrose-main-river/candidate.json').read_text());self.assertFalse(any(r['features'].values()));self.assertEqual(r['status'],'candidate');self.assertEqual(json.loads((b/'courses/divide-melrose-main-river/full-course-review.json').read_text())['status'],'held');self.assertFalse((ROOT/'public/routes/big-hole--divide-melrose.json').exists())

 def test_new_course_preserves_original_source_and_display_only_boundaries(self):
  from tools.route_catalog import validate,reconstruct_directed_source
  record=json.loads((ROOT/'catalog/routes/WA/methow-upper--red-barn-big-eddy.json').read_text());validate(record,self.catalog,ROOT);reconstruct_directed_source(record,ROOT)
  self.assertEqual(record['scope'],'river-course-overview');self.assertEqual(record['features'],dict(display=True,landOverlay=False,distanceEstimate=False,remainingTime=False));self.assertTrue(all(x['status']=='not-mapped' for x in record['overviewReview']['connections'].values()))
  full=json.loads((B/'courses/red-barn-big-eddy/full-course-review.json').read_text());self.assertEqual(len(full['imagery']),full['coursePanels']+full['endpointPanels'])
  for image in full['imagery']:self.assertEqual(hashlib.sha256((ROOT/image['file']).read_bytes()).hexdigest(),image['imageSha256'])
  held=json.loads((B/'courses/big-eddy-twisp/full-course-review.json').read_text());self.assertEqual(held['status'],'held');self.assertEqual(held['findings'][0]['panels'],[10,11]);self.assertFalse((ROOT/'public/routes/methow-upper--big-eddy-twisp.json').exists())
