"""A dated closure can be replaced by positive opening evidence, without exact pins."""
import hashlib,html,json,re,unittest
from pathlib import Path
from tools.build_catalog import build
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'research/hoh-access-recheck-20261116'
def read(p):return json.loads(p.read_text())
class HohAccessReopeningTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=build();cls.river=next(r for r in cls.catalog['rivers'] if r['id']=='hoh');cls.section=cls.river['sections'][0]
 def test_positive_agency_road_campground_and_boating_evidence_is_bound(self):
  for source in read(B/'sources/receipts.json'):
   raw=(B/'sources'/(source['name']+'.html')).read_bytes()
   self.assertEqual(source['sha256'],hashlib.sha256(raw).hexdigest())
  road=(B/'sources/nps-roads.html').read_text();row=next(r for r in re.findall(r'<tr\b.*?</tr>',road,re.S|re.I) if 'Upper Hoh Road' in r);text=re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]*>',' ',row)))
  self.assertIn('Open',text);self.assertIn('11/13/26',text)
  conditions=html.unescape(re.sub('<[^>]*>',' ',(B/'sources/nps-conditions.html').read_text()));self.assertIn('Hoh Campground is open.',re.sub(r'\s+',' ',conditions))
  dnr=(B/'sources/dnr-campsites.html').read_text();row=next(r for r in re.findall(r'<tr\b.*?</tr>',dnr,re.S|re.I) if 'Hoh Oxbow' in r);self.assertRegex(re.sub(r'\s+',' ',re.sub('<[^>]*>',' ',row)),r'Hoh Oxbow\s+OLY\s+Open')
 def test_reopening_releases_only_approximate_areas_without_live_timing_or_course(self):
  s=self.section;self.assertTrue(s['mapReleased']);self.assertEqual('approximate',s['mapPrecision']);self.assertNotIn('accessReview',s)
  for side in ['putInAccess','takeOutAccess']:self.assertEqual('access-verified',s[side]['status']);self.assertNotIn('riverBank',s[side])
  self.assertEqual('unavailable',self.river['timing']['mode'])
  self.assertNotIn('WA/hoh--hoh-campground-oxbow.json',read(ROOT/'catalog/routes/WA.json')['routes'])
  self.assertTrue(any('Log jams' in n['title'] for n in s['notices']))
  self.assertFalse(any('Upper Hoh Road closed'==n['title'] for n in s['notices']))
 def test_permanent_ids_existing_oxbow_location_and_planning_miles_are_preserved(self):
  old=read(B/'before/catalog/map_points/WA.json')['points'];now=read(ROOT/'catalog/map_points/WA.json')['points']
  for name in ['Hoh Rainforest Campground','Hoh Oxbow Campground']:self.assertEqual(old[name]['id'],now[name]['id'])
  self.assertEqual(old['Hoh Oxbow Campground']['areaCenter'],now['Hoh Oxbow Campground']['areaCenter'])
  self.assertEqual(read(B/'before/catalog/rivers/hoh.json')['sections'][0]['miles'],self.section['miles'])
  raw=(B/'sources/recreation-gov.html').read_text();m=re.search(r'"geo":\{"@type":"GeoCoordinates","latitude":([\d.-]+),"longitude":([\d.-]+)\}',raw);self.assertIsNotNone(m)
  p=now['Hoh Rainforest Campground'];self.assertEqual(float(m[1]),p['areaCenter']['lat']);self.assertEqual(float(m[2]),p['areaCenter']['lon']);self.assertNotIn('lat',p)
