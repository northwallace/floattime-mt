import copy, json, shutil, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from tools.build_catalog import build
from tools.access_registry import migrate
from tools.map_review import fingerprint
from feedback_location import validate_location
ROOT=Path(__file__).resolve().parents[1]

class NationalScalingTests(unittest.TestCase):
 def test_midwest_maps_require_review_and_do_not_enable_uncalibrated_eta(self):
  catalog=build()
  for state,count in [('MO',23),('AR',22)]:
   rivers=[r for r in catalog['rivers'] if r['state']==state]
   self.assertEqual(len(rivers),count)
   settings=json.loads((ROOT/'catalog/settings.json').read_text())
   self.assertIn(state,settings['mapReviewRequiredStates'])
   for river in rivers:
    self.assertEqual(river['timing']['mode'],'unavailable')
    self.assertIsNone(river['refSpeedMph'])
    for section in river['sections']:
     if section['mapReleased']:
      self.assertFalse(section.get('accessReview'))
      self.assertFalse(section.get('distanceReview'))
      self.assertIn(section['putInAccess']['status'],('verified','access-verified'))
      self.assertIn(section['takeOutAccess']['status'],('verified','access-verified'))
  buffalo=next(r for r in catalog['rivers'] if r['id']=='buffalo-river')
  held=[s for s in buffalo['sections'] if 'tyler-bend' in s['id']]
  self.assertEqual(len(held),2)
  self.assertTrue(all(s.get('distanceReview') and not s['mapReleased'] for s in held))
  for river in catalog['rivers']:
   if river['id']=='saline-river':
    self.assertTrue(all(not s['mapReleased'] for s in river['sections'][:3]))
    self.assertTrue(all(s['mapPendingReason']==s['accessReview'] for s in river['sections'][:3]))
   if river['id']=='buffalo-river':
    self.assertTrue(all(not s['mapReleased'] for s in river['sections'] if 'buffalo-point' in s['id']))

 def test_midwest_missing_or_changed_approval_withdraws_map(self):
  root=self.temp_root()
  path=root/'catalog/map_reviews/MO.json';reviews=json.loads(path.read_text())
  key='current-river-upper/cedar-grove-to-akers';self.assertIn(key,reviews['sections'])
  del reviews['sections'][key];path.write_text(json.dumps(reviews))
  river=next(r for r in build(root)['rivers'] if r['id']=='current-river-upper')
  section=next(s for s in river['sections'] if s['id']=='cedar-grove-to-akers')
  self.assertTrue(section['mapPilot']);self.assertFalse(section['mapReleased'])

 def test_review_inventory_discovers_new_state_local_evidence(self):
  from tools.build_review_queue import inventory
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder)
   (root/'public/routes').mkdir(parents=True)
   (root/'public/routes/index.json').write_text('{"routes":[]}')
   (root/'research/XX/access-grades').mkdir(parents=True)
   (root/'research/XX/access-grades/XX.json').write_text('{"points":{"Example landing":{"grade":"pending"}}}')
   (root/'research/XX/readiness-status.json').write_text('{"rivers":{"example-river":{"note":"Research only"}}}')
   with patch('tools.build_review_queue.build',return_value={'states':[{'id':'XX'}],'rivers':[],'accessPoints':[]}):
    result=inventory(root)
   self.assertEqual({r['subject'] for r in result['research']},{'Example landing','example-river'})
   self.assertEqual({r['state'] for r in result['research']},{'XX'})
   self.assertEqual(result['sections'],[])

 def test_corrected_dubois_area_does_not_publish_the_old_pin_or_mileage(self):
  import seo
  catalog=build();r=next(r for r in catalog['rivers'] if r['id']=='wind-river-dubois');s=r['sections'][0]
  self.assertEqual(s['putInAccessId'],'acc-c48e7f18d82b5d83b74d')
  self.assertTrue(s['mapReleased']);self.assertEqual(s['mapPrecision'],'approximate')
  self.assertTrue(s['distanceReview']);self.assertAlmostEqual(s['putInCoords']['lat'],43.5358385258117)
  self.assertNotIn('<td>15.9 mi',seo.river_html(r))
  source=json.loads((ROOT/'catalog/map_points/WY.json').read_text())['points']['Dubois City Park (Wind)']
  self.assertNotIn('lat',source);self.assertNotIn('riverBank',source)
 def temp_root(self):
  temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)
  shutil.copytree(ROOT/'catalog',root/'catalog');shutil.copytree(ROOT/'research/routes',root/'research/routes');return root
 def test_every_endpoint_has_stable_known_identity(self):
  catalog=build();points={p['id']:p for p in catalog['accessPoints']}
  self.assertEqual(len(points),len(catalog['accessPoints']))
  for river in catalog['rivers']:
   for section in river['sections']:
    for end in ('putIn','takeOut'):self.assertIn(section[end+'AccessId'],points)
 def test_identity_survives_rename_and_migration_is_idempotent(self):
  root=self.temp_root();path=root/'catalog/map_points/MT.json';d=json.loads(path.read_text());point=d['points'].pop('Johnsrud Park');identity=point['id'];point['aliases'].append('Johnsrud Park');d['points']['Johnsrud renamed facility']=point;path.write_text(json.dumps(d))
  catalog=build(root);s=next(r for r in catalog['rivers'] if r['id']=='blackfoot')['sections'];self.assertTrue(any(sec.get('takeOutAccessId')==identity or sec.get('putInAccessId')==identity for sec in s))
  # Rename does not change access identity. Re-running migration must not rebind it.
  migrate(root);self.assertEqual(json.loads(path.read_text())['points']['Johnsrud renamed facility']['id'],identity)
 def test_duplicate_and_unknown_id_fail_instead_of_name_fallback(self):
  root=self.temp_root();p=root/'catalog/map_points/MT.json';d=json.loads(p.read_text());points=list(d['points'].values());points[1]['id']=points[0]['id'];p.write_text(json.dumps(d))
  with self.assertRaisesRegex(ValueError,'Duplicate access ID'):build(root)
 def test_changed_evidence_withdraws_section_release(self):
  root=self.temp_root();before=build(root);river=next(r for r in before['rivers'] if r['id']=='yakima-canyon');section=river['sections'][0];self.assertTrue(section['mapReleased'])
  path=root/'catalog/map_points/WA.json';d=json.loads(path.read_text());d['points'][section['putIn']]['note']+=' New conflicting evidence.';path.write_text(json.dumps(d));after=next(r for r in build(root)['rivers'] if r['id']==river['id'])['sections'][0]
  self.assertTrue(after['mapPilot']);self.assertFalse(after['mapReleased']);self.assertIn('evidence',after['mapReleaseNote'])
 def test_location_evidence_is_typed_and_remains_community_reported(self):
  point={'lat':46.1,'lon':-114.2,'endpoint':'putIn','pinType':'parking','method':'manual','observedOn':'2026-01-01','firsthand':True,'status':'verified'}
  self.assertEqual(validate_location(point)['status'],'community-reported')
  for update in [{'lat':True},{'lat':float('nan')},{'lon':181},{'pinType':'ramp-ish'},{'observedOn':'2099-01-01'},{'firsthand':'yes'}]:
   with self.assertRaises(ValueError):validate_location({**point,**update})

 def test_per_river_assets_are_small_and_hash_changes_with_evidence(self):
  from tools.catalog_assets import outputs
  catalog=build();before=outputs(catalog);index=json.loads(before['public/catalog-index.json'])
  self.assertNotIn('accessPoints',index)
  # The national index grows with listings, but never carries full evidence,
  # gauge history or route geometry. Budget its average cost per river.
  self.assertLess(len(before['public/catalog-index.json']),1000*len(index['rivers']))
  for row in index['rivers']:
   self.assertEqual(set(row),{'id','name','state','lat','lon','sections','file'})
   self.assertTrue(all(set(s)=={'id','putIn','takeOut'} for s in row['sections']))
  river=catalog['rivers'][0];old_file=index['rivers'][0]['file'];river['blurb']+=' Updated.'
  after=outputs(catalog);new_file=json.loads(after['public/catalog-index.json'])['rivers'][0]['file']
  self.assertNotEqual(old_file,new_file);self.assertNotIn('public/'+old_file,after)
 def test_cross_state_legacy_alias_keeps_one_canonical_record(self):
  root=self.temp_root();path=root/'catalog/map_points/UT.json';d=json.loads(path.read_text());point=d['points'].pop('Westwater Ranger Station Boat Ramp');identity=point['id'];point['aliases'].append('Westwater Ranger Station Boat Ramp');d['points']['Renamed Westwater ramp']=point;path.write_text(json.dumps(d))
  section=next(r for r in build(root)['rivers'] if r['id']=='colorado-river-ruby-horsethief')['sections'][0]
  self.assertEqual(section['takeOutAccessId'],identity);self.assertEqual(section['takeOutAccess']['id'],identity)

 def test_changed_trip_guidance_withdraws_map_approval(self):
  root=self.temp_root();path=root/'catalog/rivers/yakima-canyon.json';r=json.loads(path.read_text());r['sections'][0]['notes']+=' New diversion hazard under review.';path.write_text(json.dumps(r))
  changed=next(r for r in build(root)['rivers'] if r['id']=='yakima-canyon')['sections'][0]
  self.assertFalse(changed['mapReleased'])
 def test_wyoming_maps_do_not_enable_uncalibrated_timing_or_hazard_routes(self):
  catalog=build();rivers=[r for r in catalog['rivers'] if r['state']=='WY']
  self.assertTrue(any(s.get('mapReleased') for r in rivers for s in r['sections']))
  self.assertTrue(all(r['timing']['mode']=='unavailable' for r in rivers))
  green=next(r for r in rivers if r['id']=='green-river-fontenelle')
  for sid in ['james-town-to-expedition-island','expedition-island-to-stratton-meyer']:
   section=next(s for s in green['sections'] if s['id']==sid)
   self.assertTrue(section['accessReview']);self.assertFalse(section['mapReleased'])
  for r in rivers:
   for s in r['sections']:
    if s.get('mapReleased'):
     self.assertIn(s['putInAccess']['status'],('verified','access-verified'))
     self.assertIn(s['takeOutAccess']['status'],('verified','access-verified'))

 def test_cinnabar_is_distinct_from_closed_corwin_and_withholds_old_distance(self):
  import seo
  river=next(r for r in build()['rivers'] if r['id']=='yellowstone-upper')
  old,new=river['sections'];self.assertNotEqual(old['takeOutAccessId'],new['putInAccessId'])
  self.assertEqual(new['putIn'],'Cinnabar (USFS)');self.assertTrue(new['mapReleased']);self.assertTrue(new['distanceReview'])
  page=seo.river_html(river);self.assertIn('<td>Distance under review</td>',page);self.assertNotIn('<td>7 mi',page)
