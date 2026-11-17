"""OSM source fidelity and attribution must survive staging and export."""
import copy,json,unittest
from tools.osm_courses import METHOD,LICENSE,source_chain,validate_osm_course,osm_source
from tools.agency_courses import nearest_position,trim_chain

class OsmCourseTests(unittest.TestCase):
 def fixture(self):
  raw=b'''<osm version="0.6"><bounds minlon="-121.01" minlat="44.99" maxlon="-120.99" maxlat="45.01"/>
  <node id="1" lon="-121" lat="45"/><node id="2" lon="-120.999" lat="45"/><node id="3" lon="-120.998" lat="45"/><node id="4" lon="-120.997" lat="45"/>
  <way id="10" version="2"><nd ref="1"/><nd ref="2"/><nd ref="3"/><tag k="waterway" v="river"/></way>
  <way id="11" version="3"><nd ref="3"/><nd ref="4"/><tag k="waterway" v="river"/></way></osm>'''
  parts=[dict(wayId='10',wayVersion=2,fromNodeIndex=0,toNodeIndex=2),dict(wayId='11',wayVersion=3,fromNodeIndex=0,toNodeIndex=1)]
  chain=source_chain(raw,parts);ends={'putIn':dict(lon=-121,lat=45),'takeOut':dict(lon=-120.997,lat=45)};clip={name:nearest_position(chain,ends[side]) for name,side in [('start','putIn'),('end','takeOut')]}
  r=dict(scope='river-course-overview',license=dict(LICENSE),source=dict(url='https://api.openstreetmap.org/api/0.6/map?bbox=-121.01,44.99,-120.99,45.01'),direction=dict(method=METHOD,parts=parts,clip=clip),geometry=trim_chain(chain,clip),features=dict(display=False,landOverlay=False,distanceEstimate=False,remainingTime=False),**ends)
  return raw,r
 def test_original_nodes_and_shared_node_join_reconstruct_without_connectors(self):
  raw,r=self.fixture();before=copy.deepcopy(r);validate_osm_course(r,raw);self.assertEqual(r,before);self.assertEqual(r['geometry']['coordinates'],[[-121,45],[-120.999,45],[-120.998,45],[-120.997,45]])
 def test_changed_or_reversed_part_cannot_reuse_a_source_selection(self):
  raw,r=self.fixture()
  for change in ['version','index','reverse','disconnected','extra']:
   v=copy.deepcopy(r)
   if change=='version':v['direction']['parts'][0]['wayVersion']=3
   if change=='index':v['direction']['parts'][0]['toNodeIndex']=3
   if change=='reverse':v['direction']['parts'][0].update(fromNodeIndex=2,toNodeIndex=0)
   if change=='disconnected':v['direction']['parts'][0]['toNodeIndex']=1
   if change=='extra':v['direction']['parts'][0]['reverse']=True
   with self.subTest(change=change),self.assertRaises(ValueError):validate_osm_course(v,raw)
 def test_source_snapshot_cannot_omit_nodes_or_use_xml_entities(self):
  raw,r=self.fixture()
  for changed in [raw.replace(b'<node id="2" lon="-120.999" lat="45"/>',b''),b'<!DOCTYPE osm [<!ENTITY x "bad">]>'+raw,raw.replace(b'lon="-120.999"',b'lon="NaN"')]:
   with self.assertRaises(ValueError):osm_source(changed)
 def test_edited_geometry_or_arbitrary_source_trim_is_rejected(self):
  raw,r=self.fixture();r['geometry']['coordinates'][1][1]+=.0001
  with self.assertRaisesRegex(ValueError,'original source nodes'):validate_osm_course(r,raw)
  raw,r=self.fixture();r['direction']['clip']['start']['fraction']=.5
  with self.assertRaisesRegex(ValueError,'trim no longer matches'):validate_osm_course(r,raw)
 def test_license_and_display_only_limits_cannot_be_dropped(self):
  raw,r=self.fixture()
  for change in ['license','credit','scope','landOverlay','distanceEstimate','remainingTime']:
   v=copy.deepcopy(r)
   if change=='license':v.pop('license')
   elif change=='credit':v['license']['attribution']='USGS'
   elif change=='scope':v['scope']='landing-to-landing'
   else:v['features'][change]=True
   with self.subTest(change=change),self.assertRaises(ValueError):validate_osm_course(v,raw)
 def test_source_query_cannot_claim_a_different_or_incomplete_corridor(self):
  raw,r=self.fixture()
  for u in ['https://example.com/map?bbox=-121.01,44.99,-120.99,45.01','https://api.openstreetmap.org/api/0.6/map?bbox=-121.00,44.99,-120.99,45.01','https://api.openstreetmap.org/api/0.6/map?bbox=0,0,20,20']:
   v=copy.deepcopy(r);v['source']['url']=u
   with self.subTest(url=u),self.assertRaises(ValueError):validate_osm_course(v,raw)
