import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.build_catalog import build
import seo

class CatalogTests(unittest.TestCase):
    def test_every_river_has_a_page_and_sitemap_entry(self):
        catalog = build()
        self.assertEqual(catalog, seo.catalog())
        sitemap = seo.sitemap_xml()
        if isinstance(sitemap, bytes): sitemap = sitemap.decode()
        for r in catalog['rivers']:
            page = seo.river_html(r)
            if isinstance(page, bytes): page = page.decode()
            self.assertIn(seo.esc(r['name']), page)
            self.assertIn('/rivers/' + r['id'], sitemap)
        for state in catalog['states']:
            self.assertIn(state['name'], seo.state_html(state['id']))

    def test_new_river_requires_no_page_edit(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'catalog/rivers').mkdir(parents=True)
            (root/'catalog/settings.json').write_text(json.dumps({k:v for k,v in build().items() if k in ('states','craft')}))
            r=json.loads((Path(__file__).resolve().parents[1]/'catalog/rivers/blackfoot.json').read_text());r['id']='test-river';r['name']='A river with {braces} and "quotes"'
            path=root/'catalog/rivers/test-river.json';path.write_text(json.dumps(r))
            self.assertEqual(build(root)['rivers'][0]['name'], r['name'])
            r['refFlowCfs']=0;path.write_text(json.dumps(r))
            with self.assertRaises(ValueError): build(root)
            r['refFlowCfs']=100;r['timezone']='Not/AZone';path.write_text(json.dumps(r))
            with self.assertRaises(ValueError): build(root)

    def test_duplicate_section_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'catalog/rivers').mkdir(parents=True)
            c=build();(root/'catalog/settings.json').write_text(json.dumps({k:c[k] for k in ('states','craft')}))
            r=copy.deepcopy(c['rivers'][0]);r['sections'].append(r['sections'][0]);(root/f'catalog/rivers/{r["id"]}.json').write_text(json.dumps(r))
            with self.assertRaises(ValueError):build(root)

    def test_montana_maps_follow_endpoint_precision(self):
        catalog = build()
        verified = {
            'madison-upper', 'yellowstone-paradise', 'flathead-north',
            'jefferson-canyon', 'clark-fork-gorge', 'bitterroot-upper', 'stillwater',
            'blackfoot',
        }
        pending = {
            'rock-creek', 'beaverhead', 'jefferson-upper', 'gallatin-lower',
            'gallatin-canyon', 'bitterroot', 'clark-fork', 'clarks-fork-yst',
            'dearborn', 'missouri-breaks', 'smith', 'swan',
            'yellowstone-upper', 'big-hole', 'madison-lower',
        }
        for river in (r for r in catalog['rivers'] if r['state'] == 'MT'):
            self.assertIn(river['id'], verified | pending | {'missouri-craig'})
            self.assertEqual(river['mapAudit'], 'verified' if river['id'] in verified else 'pending')
            for section in river['sections']:
                approximate_rivers = {'missouri-craig', 'smith', 'big-hole', 'madison-lower', 'dearborn', 'missouri-breaks'}
                if river['id']=='bitterroot':
                    eligible = section['id'] in ('bell-crossing-stevi', 'stevi-florence')
                    self.assertEqual(bool(section.get('mapPilot')), eligible)
                    if eligible: self.assertEqual(section['mapPrecision'], 'approximate')
                    else: self.assertNotIn('takeOutCoords', section)
                    continue
                self.assertEqual(bool(section.get('mapPilot')), river['id'] in verified or river['id'] in approximate_rivers, river['id'] + '/' + section['id'])
                if river['id']=='missouri-craig':
                    self.assertEqual(section['mapPrecision'], 'approximate' if section['id']=='holter-craig' else 'exact')
                    continue
                if river['id'] in approximate_rivers:
                    exact = section['id'] in ('divide-melrose', 'bear-trap')
                    self.assertEqual(section['mapPrecision'], 'exact' if exact else 'approximate')
                    continue
                if river['id'] not in verified:
                    self.assertNotIn('putInCoords', section)
                    self.assertNotIn('takeOutCoords', section)
                    continue
                self.assertEqual(set(section['putInCoords']), {'lat', 'lon'})
                self.assertEqual(set(section['takeOutCoords']), {'lat', 'lon'})
                for key in ('putInAccess', 'takeOutAccess'):
                    self.assertTrue(section[key]['sourceUrl'].startswith('https://'))
                    self.assertRegex(section[key]['verifiedOn'], r'^\d{4}-\d{2}-\d{2}$')
                    self.assertRegex(section[key]['accessType'].lower(), r'ramp|launch')
                take_out = section['takeOutAccess']
                if river['id']=='flathead-north':
                    self.assertNotIn('riverBank', take_out)  # Landing survey is not a bank audit.
                    continue
                self.assertIn(take_out['riverBank'], ('river-left', 'river-right'))
                self.assertRegex(take_out['bankVerifiedOn'], r'^\d{4}-\d{2}-\d{2}$')
                self.assertTrue(take_out['bankSourceUrl'].startswith('https://'))

    def test_incomplete_verified_point_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root/'catalog/rivers').mkdir(parents=True)
            (root/'catalog/map_points').mkdir(parents=True)
            catalog = build()
            (root/'catalog/settings.json').write_text(json.dumps({k: catalog[k] for k in ('states', 'craft')}))
            river = copy.deepcopy(next(r for r in catalog['rivers'] if r['id'] == 'madison-lower'))
            for section in river['sections']:
                for key in ('mapPilot', 'putInCoords', 'takeOutCoords', 'putInAccess', 'takeOutAccess'):
                    section.pop(key, None)
            river.pop('mapAudit', None)
            (root/'catalog/rivers/madison-lower.json').write_text(json.dumps(river))
            source = json.loads((Path(__file__).resolve().parents[1]/'catalog/map_points/MT.json').read_text())
            source['points']['Warm Springs'].pop('sourceUrl')
            (root/'catalog/map_points/MT.json').write_text(json.dumps(source))
            with self.assertRaisesRegex(ValueError, 'sourceUrl required'):
                build(root)

    def test_verified_takeout_requires_complete_bank_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root/'catalog/rivers').mkdir(parents=True)
            (root/'catalog/map_points').mkdir(parents=True)
            catalog = build()
            (root/'catalog/settings.json').write_text(json.dumps({k: catalog[k] for k in ('states', 'craft')}))
            river = copy.deepcopy(next(r for r in catalog['rivers'] if r['id'] == 'madison-lower'))
            for section in river['sections']:
                for key in ('mapPilot', 'putInCoords', 'takeOutCoords', 'putInAccess', 'takeOutAccess'):
                    section.pop(key, None)
            river.pop('mapAudit', None)
            (root/'catalog/rivers/madison-lower.json').write_text(json.dumps(river))
            source = json.loads((Path(__file__).resolve().parents[1]/'catalog/map_points/MT.json').read_text())
            source['points']['Warm Springs'].pop('bankSourceUrl')
            (root/'catalog/map_points/MT.json').write_text(json.dumps(source))
            with self.assertRaisesRegex(ValueError, 'bank metadata must be complete'):
                build(root)

    def test_directory_and_state_pages_are_search_visible(self):
        directory=seo.directory_html()
        self.assertIn('/rivers/madison-upper',directory)
        self.assertIn('Madison',seo.state_html('MT'))
        self.assertIn('Salmon',seo.state_html('ID'))
        self.assertIn('Deschutes',seo.state_html('OR'))
        self.assertIn('Yakima',seo.state_html('WA'))

    def test_unavailable_timing_never_leaks_into_seo(self):
        rivers = {r['id']: r for r in build()['rivers']}
        for river in rivers.values():
            if river.get('timing', {}).get('mode') != 'unavailable':
                continue
            self.assertIsNone(river['refFlowCfs'])
            self.assertIsNone(river['refSpeedMph'])
            page = seo.river_html(river)
            self.assertIn('Live estimate not available', page)
            self.assertNotIn('Speed is scaled from a reference', page)
            self.assertNotIn('calibrated to this gauge', page)
            self.assertNotIn('isAccessibleForFree', page)
        self.assertIn('Published guide: 3–4 days', seo.river_html(rivers['green-river-labyrinth']))

    def test_maps_are_eligible_per_section_and_approximate_sources_are_labelled(self):
        rivers = {r['id']: r for r in build()['rivers']}
        methow = rivers['methow-lower']
        self.assertEqual(methow['mapAudit'], 'pending')
        self.assertEqual(methow['sections'][0]['mapPrecision'], 'exact')
        self.assertFalse(methow['sections'][1].get('mapPilot', False))
        sanjuan = rivers['san-juan']
        self.assertEqual(sanjuan['sections'][0]['mapPrecision'], 'approximate')
        page = seo.river_html(rivers['smith'])
        self.assertIn('Approximate facility locations', page)
        self.assertNotIn('Put-in directions', page)
        for key in ('putInAccess', 'takeOutAccess'):
            self.assertNotIn('riverBank', sanjuan['sections'][0][key])

    def test_unavailable_timing_rejects_placeholder_calibration(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root/'catalog/rivers').mkdir(parents=True)
            c = build()
            (root/'catalog/settings.json').write_text(json.dumps({k:c[k] for k in ('states','craft')}))
            source = Path(__file__).resolve().parents[1]/'catalog/rivers/green-river-flaming-gorge.json'
            r = json.loads(source.read_text()); r['refSpeedMph'] = 3
            (root/'catalog/rivers/green-river-flaming-gorge.json').write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError, 'calibration numbers'):
                build(root)

    def test_approximate_access_never_accepts_an_exact_pin(self):
        with tempfile.TemporaryDirectory() as d:
            import shutil
            root = Path(d)
            shutil.copytree(Path(__file__).resolve().parents[1]/'catalog', root/'catalog');shutil.copytree(Path(__file__).resolve().parents[1]/'research/routes',root/'research/routes')
            path = root/'catalog/map_points/UT.json'
            data = json.loads(path.read_text())
            data['points']['Mexican Hat Boat Launch']['lat'] = 37.1471
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'exact pin coordinates'):
                build(root)

    def test_exact_access_can_have_unknown_bank_without_inventing_guidance(self):
        with tempfile.TemporaryDirectory() as d:
            import shutil
            root = Path(d)
            shutil.copytree(Path(__file__).resolve().parents[1]/'catalog', root/'catalog');shutil.copytree(Path(__file__).resolve().parents[1]/'research/routes',root/'research/routes')
            path = root/'catalog/map_points/MT.json'
            data = json.loads(path.read_text())
            point = data['points']['Warm Springs']
            for key in ('riverBank','bankVerifiedOn','bankSourceName','bankSourceUrl','bankNote'):
                point.pop(key, None)
            path.write_text(json.dumps(data))
            river = next(r for r in build(root)['rivers'] if r['id']=='madison-lower')
            section = next(s for s in river['sections'] if s['takeOut']=='Warm Springs')
            self.assertTrue(section['mapPilot'])
            self.assertNotIn('riverBank', section['takeOutAccess'])

    def test_river_pages_only_link_verified_access(self):
        catalog = build()
        by_id = {river['id']: river for river in catalog['rivers']}
        pending = seo.river_html(by_id['rock-creek'])
        verified = seo.river_html(by_id['madison-upper'])
        self.assertNotIn('class="section-map-link"', pending)
        self.assertNotIn('Put-in directions', pending)
        self.assertEqual(pending.count('<strong>Map unavailable:</strong>'), 3)
        self.assertIn('Valley of the Moon: The old pin was across the road from river access', pending)
        self.assertEqual(verified.count('class="section-map-link"'), 4)
        self.assertEqual(verified.count('Sources checked 2026-10-23'), 4)
        self.assertEqual(verified.count('Take-out: river right'), 4)

        canyon = seo.river_html(by_id['jefferson-canyon'])
        self.assertEqual(canyon.count('class="section-map-link"'), 3)
        self.assertIn('Take-out: river left', canyon)
        self.assertEqual(canyon.count('Take-out: river right'), 2)


    def test_only_montana_maps_are_released_and_other_guides_remain(self):
        catalog=build()
        self.assertEqual(catalog['mapRelease'], {'states':['MT'], 'reviewedRoutes':True})
        released=[]
        for river in catalog['rivers']:
            for section in river['sections']:
                self.assertEqual(section['mapReleased'], bool(river['state']=='MT' and section.get('mapPilot') and not section.get('accessReview')))
                if section['mapReleased']: released.append(section)
            if river['state']!='MT':
                self.assertNotIn('section-map-link',seo.river_html(river))
        self.assertEqual(len(released),38)
        self.assertTrue(any(r['state']=='WA' for r in catalog['rivers']))

    def test_access_hold_cannot_publish_timing_or_map_links(self):
        river=next(r for r in build()['rivers'] if r['id']=='clark-fork')
        page=seo.river_html(river)
        self.assertIn('Grass Valley',page)
        self.assertIn('Access and route under review',page)
        self.assertNotIn('section-map-link',page)
        self.assertNotIn('in a raft at a reference',page)
        self.assertNotIn('tubes can work',page)
        self.assertIn('Route under review',page)

if __name__=='__main__': unittest.main()
