import unittest
from tools.audit_gauges import classify


class GaugeAuditTests(unittest.TestCase):
    def test_seasonal_and_unresolved_sources_are_explained_on_river_pages(self):
        import seo
        from tools.build_catalog import build
        rivers = {r['id']: r for r in build()['rivers']}
        for rid in ('arkansas-river-salida', 'tongue-river-wy'):
            river = rivers[rid]
            page = seo.river_html(river)
            self.assertIn(river['gaugeContext']['note'], page)
            self.assertNotIn('for live discharge.', page)
        self.assertEqual(rivers['encampment-river']['gauge'], '06625000')
        self.assertEqual(rivers['encampment-river']['timing']['mode'], 'unavailable')

    def test_freshness_rejects_future_and_stale_measurements(self):
        now = 1800000000000
        for minutes in (-6, 121):
            result = classify({'flow': 250, 'at': now - minutes * 60000}, now)
            self.assertEqual(result['status'], 'stale-or-invalid-time')
            self.assertFalse(result['meetsFlowFreshnessCheck'])
        self.assertEqual(classify({'flow': 250, 'at': now - 120 * 60000}, now)['status'], 'current')

    def test_zero_flow_is_real_data_but_not_a_float_estimate(self):
        result = classify({'flow': 0, 'at': 1000}, 1000)
        self.assertEqual(result['status'], 'current')
        self.assertFalse(result['meetsFlowFreshnessCheck'])

    def test_null_nonfinite_and_negative_are_not_readings(self):
        for value in (None, float('nan'), float('inf'), -1, True, '250'):
            self.assertEqual(classify({'flow': value, 'at': 1000}, 1000)['status'], 'no-discharge')

    def test_unassigned_and_other_river_sources_are_skipped_without_requests(self):
        import io,json,tempfile
        from pathlib import Path
        from unittest.mock import patch
        from tools.audit_gauges import main
        rivers=[{'id':'none','state':'XX','gauge':None},{'id':'proxy','state':'XX','gauge':'12345678','gaugeRelationship':'other-river-reference'}]
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'audit.json'
            with patch('sys.argv',['audit','--base-url','http://localhost:9999','--output',str(out)]),patch('tools.audit_gauges.urlopen',return_value=io.BytesIO(json.dumps({'rivers':rivers}).encode())) as fetch:
                self.assertEqual(main(),0);self.assertEqual(fetch.call_count,1)
            self.assertEqual({r['status'] for r in json.loads(out.read_text())['gauges']},{'unassigned','reference-only'})
