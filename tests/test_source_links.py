import json
from pathlib import Path
import tempfile
import unittest

from tools.build_catalog import build
from tools.source_links import validate_public_source_urls

ROOT = Path(__file__).resolve().parents[1]


class SourceLinkTests(unittest.TestCase):
    def test_temporary_download_links_fail_without_exposing_credentials(self):
        queries = [
            'sig.expires=1999999999&sig=private-value',
            'X-Amz-Signature=private-value&X-Amz-Expires=900',
            'X-Goog-Signature=private-value',
            'Key-Pair-Id=demo&Signature=private-value',
            'sv=2025-01-01&se=2030-01-01&sig=private-value',
        ]
        for query in queries:
            with self.subTest(query=query.split('=')[0]):
                with self.assertRaises(ValueError) as failure:
                    validate_public_source_urls({'sections': [{'sourceUrl': 'https://agency.example/map?' + query}]})
                self.assertIn('sections[0].sourceUrl', str(failure.exception))
                self.assertNotIn('private-value', str(failure.exception))

    def test_permanent_document_and_gis_queries_remain_usable(self):
        validate_public_source_urls({'sources': [
            'https://agency.example/view/map.pdf#page=15',
            'https://agency.example/query?where=ID%3D1&outFields=name&outSR=4326&f=json',
            'https://agency.example/document?id=123',
        ]})

    def test_catalog_import_rejects_temporary_notice_link(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'catalog/rivers').mkdir(parents=True)
            settings = json.loads((ROOT / 'catalog/settings.json').read_text())
            settings.pop('mapReviewRequiredStates', None)
            (root / 'catalog/settings.json').write_text(json.dumps(settings))
            river = json.loads((ROOT / 'catalog/rivers/blackfoot.json').read_text())
            for section in river['sections']:
                section.pop('putInAccessId', None)
                section.pop('takeOutAccessId', None)
            river['sections'][0]['notices'] = [{'title': 'Source test', 'text': 'Test',
                'sourceName': 'Agency', 'sourceUrl': 'https://agency.example/map?sig.expires=9999999999&sig=private-value', 'checkedOn': '2026-11-05'}]
            (root / 'catalog/rivers/blackfoot.json').write_text(json.dumps(river))
            with self.assertRaisesRegex(ValueError, 'temporary signed source URL'):
                build(root)
