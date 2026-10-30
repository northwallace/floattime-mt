import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from fetch_agency_layer import download, archive
from check_agency_bindings import check, digest

CONFIG = {'id':'OR-test','url':'https://example.org/FeatureServer/0','discoveryUrl':'https://example.org','fields':['name'],'where':"public_display='Yes'"}

class AgencySourceTests(unittest.TestCase):
    def service(self, mode=None):
        inventory_calls = [0]
        def request(url, params):
            if not url.endswith('/query'):
                return {'geometryType':'esriGeometryPoint','objectIdField':'id','fields':[{'name':'id','type':'esriFieldTypeOID'},{'name':'name','type':'esriFieldTypeString'}]}
            if params.get('returnIdsOnly'):
                inventory_calls[0] += 1
                return {'objectIds':list(range(202 if mode=='moving' and inventory_calls[0]>1 else 201))}
            self.assertNotEqual(params['outFields'],'*')
            ids = list(map(int,params['objectIds'].split(',')))
            features = [{'attributes':{'id':i,'name':str(i),'internal':'omit me'},'geometry':{'x':-120,'y':45}} for i in ids]
            if mode=='missing':features.pop()
            if mode=='duplicate':features.append(features[0])
            return {'features':features,'exceededTransferLimit':mode=='truncated'}
        return request

    def test_complete_pagination_and_attribute_allowlist(self):
        data=download(CONFIG,self.service())
        self.assertEqual(len(data['features']),201)
        self.assertNotIn('internal', data['features'][0]['attributes'])

    def test_fail_closed_on_partial_duplicate_or_changing_inventory(self):
        for mode in ('missing','duplicate','moving','truncated'):
            with self.subTest(mode=mode), self.assertRaises(ValueError):download(CONFIG,self.service(mode))

    def test_unknown_field_refuses_changed_schema(self):
        with self.assertRaises(ValueError):download({**CONFIG,'fields':['unknown']},self.service())

    def test_binding_detects_changes_without_promoting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); data=download(CONFIG,self.service()); receipt=archive(root,CONFIG,data);f=data['features'][0]
            b={'accessId':'acc-example','name':'test','sourceId':CONFIG['id'],'sourceSnapshot':receipt['file'],'sourceSha256':receipt['sha256'],'featureField':'id','featureId':0,'featureSha256':digest(f),'decision':'access-verified'}
            self.assertEqual(check([b],root)[0]['status'],'unchanged')
            newer=copy.deepcopy(data);newer['features'][0]['geometry']['x']=-121;archive(root,CONFIG,newer)
            self.assertEqual(check([b],root)[0]['status'],'needs-review')
            self.assertFalse((root/'catalog').exists())
            (root/receipt['file']).write_text('{}')
            with self.assertRaises(ValueError):check([b],root)

    def test_immutable_archive_detects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);data=download(CONFIG,self.service());receipt=archive(root,CONFIG,data)
            (root/receipt['file']).write_text('{}')
            with self.assertRaises(ValueError):archive(root,CONFIG,data)

class ExpansionEvidenceTests(unittest.TestCase):
    def test_whole_trip_length_needs_matching_named_endpoints(self):
        from tools.build_catalog import validate_distance_evidence
        sec={'putIn':'Start','takeOut':'Finish','miles':2,'distanceEvidence':{'method':'published-trip-length','miles':2,'sourceName':'County','sourceUrl':'https://example.org/guide','checkedOn':'2026-10-29','streamId':'Test river','note':'Published approximate trip length.','putIn':{'name':'Start','sourceLocation':'Trip guide'},'takeOut':{'name':'Finish','sourceLocation':'Trip guide'}}}
        validate_distance_evidence(sec,'test: ')
        for key,value in [('miles',3),('putIn','Different landing')]:
            bad=copy.deepcopy(sec);bad[key]=value
            with self.assertRaises(ValueError):validate_distance_evidence(bad,'test: ')

    def test_closed_or_conflated_routes_cannot_be_released(self):
        from tools.build_catalog import build
        rivers={r['id']:r for r in build()['rivers']}
        for rid,sid in [('boise','ann-morrison-eagle'),('sandy','dodge-oxbow'),('sandy','oxbow-dabney'),('payette-nf','cabarton-banks'),('payette-sf','lowman-deadwood')]:
            s=next(s for s in rivers[rid]['sections'] if s['id']==sid)
            self.assertTrue(s['accessReview'])
            self.assertFalse(s['mapReleased'])

    def test_california_has_guide_time_without_fabricated_model(self):
        from tools.build_catalog import build
        river=next(r for r in build()['rivers'] if r['id']=='russian-river-forestville')
        self.assertEqual(river['timing']['mode'],'unavailable')
        self.assertIsNone(river['refSpeedMph'])
        sec=river['sections'][0]
        self.assertEqual(sec['guideTimes'][0]['min'],4.5)
        self.assertEqual(sec['mapPrecision'],'approximate')
        self.assertTrue(sec['mapReleased'])

    def test_new_agency_maps_have_explicit_section_approval(self):
        from tools.build_catalog import build
        cat=build()
        for state in ('OR','ID','CA'):
            self.assertIn(state,json.loads((Path(__file__).resolve().parents[1]/'catalog/settings.json').read_text())['mapReviewRequiredStates'])
            self.assertTrue(any(s.get('mapReleased') for r in cat['rivers'] if r['state']==state for s in r['sections']))
