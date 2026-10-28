import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.route_catalog import validate,geometry_checks,build_outputs,write_or_check
from tools.build_catalog import build

class RouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=build();cls.record=json.loads((ROOT/'catalog/routes/MT/blackfoot--johnsrud-weigh-station.json').read_text())
    def test_reviewed_only_exports_and_never_changes_timing(self):
        before=copy.deepcopy(self.catalog);outputs=build_outputs(ROOT,self.catalog)
        entries=json.loads(outputs['public/routes/index.json'])['routes']
        self.assertEqual(len(entries),13)
        self.assertTrue(all(not e['features']['remainingTime'] and not e['features']['distanceEstimate'] for e in entries))
        self.assertNotIn('public/routes/madison-lower--blacks-ford-greycliff.json',outputs)
        self.assertEqual(before,self.catalog)
    def test_endpoint_and_mileage_edits_force_review(self):
        for field in ['putInCoords','miles']:
            catalog=copy.deepcopy(self.catalog);section=next(s for r in catalog['rivers'] if r['id']=='blackfoot' for s in r['sections'] if s['id']==self.record['sectionId'])
            if field=='miles':section['miles']+=1
            else:section[field]['lon']+=.001
            with self.assertRaisesRegex(ValueError,'changed'):validate(self.record,catalog,ROOT)
    def test_candidates_and_future_features_cannot_sneak_into_release(self):
        for status,flag in [('candidate','display'),('reviewed','remainingTime'),('reviewed','distanceEstimate')]:
            record=copy.deepcopy(self.record);record['status']=status;record['features'][flag]=True
            with self.assertRaises(ValueError):validate(record,self.catalog,ROOT)
    def test_geometry_reversal_gap_and_mileage_conflict_are_flagged(self):
        record=copy.deepcopy(self.record);record['geometry']['coordinates'].reverse()
        self.assertIn('endpoint-offset-over-100m',geometry_checks(record)[1])
        record=copy.deepcopy(self.record);record['geometry']['coordinates'][10][0]+=.1
        self.assertIn('route-gap-or-duplicate-vertex',geometry_checks(record)[1])
        record=copy.deepcopy(self.record);record['catalogMiles']=20
        self.assertIn('mileage-difference-over-5-percent',geometry_checks(record)[1])
        record=copy.deepcopy(self.record);record['direction']['takeOutMeasure']=999
        self.assertIn('downstream-order-unconfirmed',geometry_checks(record)[1])
    def test_evidence_and_corridor_cannot_silently_change(self):
        for target in ['source','landEvidence']:
            record=copy.deepcopy(self.record);record[target]['sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'changed'):validate(record,self.catalog,ROOT)
        record=copy.deepcopy(self.record);record['landEvidence']['routeSha256']='0'*64
        with self.assertRaisesRegex(ValueError,'old route'):validate(record,self.catalog,ROOT)
    def test_retired_generated_asset_is_removed_and_stale_checks_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);dest=root/'public/routes/retired.json';dest.parent.mkdir(parents=True);dest.write_text('{}')
            with patch('tools.route_catalog.build_outputs',return_value={}):
                with self.assertRaisesRegex(ValueError,'Stale public'):write_or_check(root,{},True)
                write_or_check(root,{});self.assertFalse(dest.exists())
    def test_all_montana_sections_have_actionable_queue_entries(self):
        queue=json.loads((ROOT/'research/routes/MT/review-queue.json').read_text())['sections']
        expected={(r['id'],s['id']) for r in self.catalog['rivers'] if r['state']=='MT' for s in r['sections']}
        self.assertEqual({(r['riverId'],r['sectionId']) for r in queue},expected)
        self.assertEqual(sum(r['issues']==['access-points-pending'] for r in queue),7)
        self.assertEqual(sum(r['issues']==['catalog-access-under-review'] for r in queue),13)

if __name__=='__main__':unittest.main()
