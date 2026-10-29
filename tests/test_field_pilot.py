import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import server

ROOT=Path(__file__).resolve().parents[1]

class FieldPilotTests(unittest.TestCase):
    def test_explicit_request_only_and_only_one_pilot(self):
        with patch.dict(server.os.environ, {'ARCGIS_BASEMAP_API_KEY':'test-browser-key'}):
            base=server._map_config()
            self.assertNotIn('fieldTest',base)
            self.assertNotIn('fieldTest',server._map_config('unknown'))
            pilot=server._map_config('greycliff')
            entry=pilot.pop('fieldTest')
            self.assertEqual(pilot,base)
            self.assertEqual(entry['riverId'],'madison-lower')
            self.assertEqual(entry['sectionId'],'blacks-ford-greycliff')
            self.assertEqual(len(json.loads((ROOT/'catalog/field_pilots.json').read_text())['pilots']),1)

    def test_checks_preserve_source_and_continuous_downstream_graph(self):
        review=json.loads((ROOT/'research/MT/greycliff-pilot-20261029/route-checks.json').read_text())
        source=ROOT/review['sourceFile']
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),review['sourceSha256'])
        features=json.loads(source.read_text())['response']['features']
        by_id={f['attributes']['hydroseq']:f for f in features}
        ids=review['hydrosequences']
        for a,b in zip(ids,ids[1:]):
            self.assertEqual(by_id[a]['attributes']['dnhydroseq'],b)
            self.assertEqual(by_id[a]['geometry']['paths'][0][-1],by_id[b]['geometry']['paths'][0][0])
        self.assertTrue(all(by_id[i]['attributes']['divergence']!=2 for i in ids))
        self.assertLess(review['endOffsetMeters'],50)
        self.assertTrue(review['isSimple'])
        self.assertLess(review['maxSegmentMeters'],250)
        self.assertLess(abs(review['utmRouteMiles']/review['fwpComparison']['miles']-1),.02)
        data=json.loads((ROOT/'public/field-pilots/greycliff.json').read_text())
        self.assertEqual(data['geometry'],review['geometry'])

    def test_tampered_pilot_is_not_enabled(self):
        with patch.dict(server.os.environ, {'ARCGIS_BASEMAP_API_KEY':'test-browser-key'}), patch.object(server.hashlib,'sha256') as digest:
            digest.return_value.hexdigest.return_value='wrong'
            self.assertNotIn('fieldTest',server._map_config('greycliff'))
