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
            r=copy.deepcopy(build()['rivers'][0]);r['id']='test-river';r['name']='A river with {braces} and "quotes"'
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

if __name__=='__main__': unittest.main()
