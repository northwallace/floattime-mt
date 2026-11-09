"""Review signatures must use the same normalized evidence as the map gate."""
import copy
import json
from pathlib import Path
import unittest
from tools.build_catalog import build
from tools.map_review import current_fingerprints

ROOT=Path(__file__).resolve().parents[1]

class MapReviewFingerprintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.catalog=build()

    def test_report_matches_mixed_precision_approval_without_changing_catalog(self):
        before=copy.deepcopy(self.catalog)
        rows=current_fingerprints(self.catalog,river_id='american-river-lower',section_id='lower-sunrise-river-bend')
        approval=json.loads((ROOT/'catalog/map_reviews/CA.json').read_text())['sections']['american-river-lower/lower-sunrise-river-bend']
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['fingerprint'],approval['fingerprint'])
        self.assertEqual(rows[0]['accessStatuses'],['access-verified','verified'])
        self.assertEqual(before,self.catalog)

    def test_changed_evidence_changes_signature_without_approving_map(self):
        catalog=copy.deepcopy(self.catalog)
        river=next(r for r in catalog['rivers'] if r['id']=='american-river-lower')
        section=river['sections'][0]
        original=current_fingerprints(catalog,river_id=river['id'])[0]['fingerprint']
        section['mapReleased']=False
        point=next(p for p in catalog['accessPoints'] if p['id']==section['putInAccessId'])
        point['directions']='A changed source needs review.'
        row=current_fingerprints(catalog,river_id=river['id'])[0]
        self.assertNotEqual(row['fingerprint'],original)
        self.assertFalse(row['mapReleased'])
        self.assertEqual(current_fingerprints(catalog,state='MT',river_id=river['id']),[])

    def test_missing_access_id_cannot_produce_an_approval_fingerprint(self):
        catalog=copy.deepcopy(self.catalog)
        river=next(r for r in catalog['rivers'] if r['id']=='american-river-lower')
        del river['sections'][0]['putInAccessId']
        with self.assertRaisesRegex(ValueError, 'normalized access IDs are required'):
            current_fingerprints(catalog,river_id=river['id'])
