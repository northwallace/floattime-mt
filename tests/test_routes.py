from catalog_contracts import assert_registry_identity, assert_river_identity, assert_catalog_identity
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
        expected = set()
        for manifest in (ROOT/'catalog/routes').glob('??.json'):
            for path in json.loads(manifest.read_text())['routes']:
                record = json.loads((ROOT/'catalog/routes'/path).read_text())
                if record['status'] == 'reviewed' and record['features']['display']:
                    expected.add((record['riverId'], record['sectionId']))
        self.assertEqual({(e['riverId'], e['sectionId']) for e in entries}, expected)
        self.assertTrue(all(not e['features']['remainingTime'] and not e['features']['distanceEstimate'] for e in entries))
        self.assertNotIn('public/routes/madison-lower--blacks-ford-greycliff.json',outputs)
        self.assertEqual(before,self.catalog)
    def test_wyoming_source_order_and_resolution_evidence_are_enforced(self):
        base=ROOT/'catalog/routes/WY'
        directed=json.loads((base/'north-platte-gray-reef-casper--government-bridge-to-whitetail.json').read_text())
        generalized=json.loads((base/'north-platte-gray-reef-casper--gray-reef-to-lusby.json').read_text())
        for original in (directed,generalized):
            validate(original,self.catalog,ROOT)
            record=copy.deepcopy(original);record['direction']['featureIds']=['missing-feature']
            with self.assertRaisesRegex(ValueError,'missing'):validate(record,self.catalog,ROOT)
            record=copy.deepcopy(original);record['direction']['featureIds'].reverse()
            with self.assertRaisesRegex(ValueError,'disconnected|reversed'):validate(record,self.catalog,ROOT)
        record=copy.deepcopy(generalized);record['resolutionReview']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'changed'):validate(record,self.catalog,ROOT)
    def test_single_source_feature_uses_stations_not_perpendicular_offsets(self):
        record=json.loads((ROOT/'catalog/routes/WI/namekagon-river--north-springbrook-landing-to-springbrook-landing.json').read_text())
        direction=record['direction']
        direction['putInSourceStationMeters']=direction['putInOffsetMeters']
        direction['takeOutSourceStationMeters']=direction['takeOutOffsetMeters']
        direction['putInOffsetMeters']=direction['takeOutOffsetMeters']=0
        validate(record,self.catalog,ROOT)
        direction['putInSourceStationMeters'],direction['takeOutSourceStationMeters']=direction['takeOutSourceStationMeters'],direction['putInSourceStationMeters']
        with self.assertRaisesRegex(ValueError,'reversed'):validate(record,self.catalog,ROOT)
        del direction['takeOutSourceStationMeters']
        with self.assertRaisesRegex(ValueError,'source-line station'):validate(record,self.catalog,ROOT)

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
        from tools.build_review_queue import inventory
        # Generate from the current catalog, not the historical October queue.
        # Minimal source context keeps this contract independent of archived research.
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'public/routes').mkdir(parents=True)
            (root/'public/routes/index.json').write_bytes((ROOT/'public/routes/index.json').read_bytes())
            with patch('tools.build_review_queue.build',return_value=self.catalog):
                queue=[r for r in inventory(root)['sections'] if r['state']=='MT']
        sections={(r['id'],s['id']):s for r in self.catalog['rivers'] if r['state']=='MT' for s in r['sections']}
        self.assertEqual({(r['riverId'],r['sectionId']) for r in queue},set(sections))
        for row in queue:
            section=sections[row['riverId'],row['sectionId']]
            self.assertEqual(row['released'],section['mapReleased'])
            if section.get('accessReview'):
                self.assertEqual(row['blocker'],section['accessReview'])
                self.assertEqual(row['distance'],'held');self.assertEqual(row['timing'],'unavailable')
            if not row['riverPath']:
                self.assertTrue(row['riverPathIssues']);self.assertTrue(row['riverPathNextAction'])

if __name__=='__main__':unittest.main()
