import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.flow_sources import flow_key, flow_label, dayfile_url, parse_dayfile, validate_source, parse_cdwr, cdwr_urls
from tools.build_catalog import build
import seo
import server


class FlowSourceTests(unittest.TestCase):
    def setUp(self):
        self.river = json.loads((Path(__file__).resolve().parents[1] / 'catalog/rivers/north-platte-glendo.json').read_text())
        self.source = self.river['flowSource']
        self.now = datetime(2026, 10, 30, 15, 15, tzinfo=timezone.utc)

    def table(self, rows, station='GLWY', parameter='Q', clock='Fri Oct 30 09:15:00 2026'):
        return f'<PRE>retrieved: {clock}</PRE>\nBEGIN DATA\nDATE       TIME , {station} {parameter}\n' + rows + '\nEND DATA'

    def test_discharge_parser_preserves_zero_and_rejects_flags_missing_and_future(self):
        text = self.table('10/30/2026 08:00, 24.0\n10/30/2026 08:15, 25.2\n10/30/2026 08:30, 0\n'
                          '10/30/2026 08:45, 998877\n10/30/2026 09:00, 99.0*\n10/30/2026 09:01, -1\n'
                          '10/30/2026 09:02, NaN\n10/30/2026 09:03, \n10/30/2026 10:00, 999')
        result = parse_dayfile(text, self.source, self.now)
        self.assertEqual(result['flow'], 0)
        self.assertEqual(len(result['series']), 3)
        self.assertEqual(result['at'], datetime(2026, 10, 30, 14, 30, tzinfo=timezone.utc).timestamp()*1000)
        self.assertIsNone(result['temp'])
        self.assertTrue(result['provisional'])

    def test_wrong_station_parameter_clock_or_error_page_is_not_a_reading(self):
        for text in [self.table('', station='WRBD'), self.table('', parameter='GH'), '<html>Service error</html>',
                     self.table('', clock='Fri Oct 30 08:15:00 2026')]:
            with self.assertRaises(ValueError):
                parse_dayfile(text, self.source, self.now)

    def test_dst_ambiguous_and_nonexistent_times_are_skipped(self):
        for now, clock, rows in [
            (datetime(2026,11,1,10,tzinfo=timezone.utc), 'Sun Nov 01 03:00:00 2026', '11/01/2026 01:30, 500\n11/01/2026 02:30, 450'),
            (datetime(2026,3,8,10,tzinfo=timezone.utc), 'Sun Mar 08 04:00:00 2026', '03/08/2026 02:30, 500\n03/08/2026 03:30, 450'),
        ]:
            result = parse_dayfile(self.table(rows, clock=clock), self.source, now)
            self.assertEqual([p['q'] for p in result['series']], [450])

    def test_catalog_override_requires_context_and_cannot_enable_timing(self):
        validate_source(self.river)
        for key, value in [('parameter','GH'), ('station','https://evil.example/'), ('provider','unknown'), ('timeZone','UTC')]:
            river = copy.deepcopy(self.river);river['flowSource'][key] = value
            with self.assertRaises(ValueError): validate_source(river)
        river = copy.deepcopy(self.river);river['timing']['mode'] = 'model'
        with self.assertRaises(ValueError): validate_source(river)
        self.assertEqual(flow_key(self.river), 'USBR:GLWY:Q')
        self.assertEqual(flow_key({'gauge':'06041000'}), '06041000')
        self.assertIn('format=2', dayfile_url(self.source,self.now))
        self.assertNotIn('format=10', dayfile_url(self.source,self.now))

    def test_built_pages_name_actual_provider_without_reenabling_eta(self):
        for river in build()['rivers']:
            if not river.get('flowSource'): continue
            page = seo.river_html(river)
            self.assertIn(flow_label(river),page)
            self.assertIn(river['flowSource']['sourceUrl'],page)
            self.assertNotIn('What USGS gauge',page)
            self.assertEqual(river['timing']['mode'],'unavailable')
            self.assertIsNone(river['refFlowCfs'])

    def test_provider_cache_and_failure_keep_original_measurement_age(self):
        key = 'USBR:GLWY:Q'
        reading = {'flow':25.2,'at':12345,'series':[]}
        with patch.object(server,'_gauge_cache',{}), patch.object(server,'_download_gauge',return_value=reading) as fetch:
            with patch.object(server.time,'time',return_value=1000): server._cached_gauge_reading(key)
            with patch.object(server.time,'time',return_value=1800): self.assertEqual(server._cached_gauge_reading(key),reading)
            self.assertEqual(fetch.call_count,1)
            fetch.side_effect=ValueError('Invalid upstream schema')
            with patch.object(server.time,'time',return_value=2000):
                result=server._cached_gauge_reading(key)
                self.assertTrue(result['stale']);self.assertEqual(result['at'],12345)
            with patch.object(server.time,'time',return_value=5000), self.assertRaises(ValueError):
                server._cached_gauge_reading(key)

    def cdwr_fixture(self):
        source = {'provider':'colorado-dwr','station':'ARKSALCO','parameter':'DISCHRG',
                  'timeZone':'America/Denver','sourceUrl':'https://dwr.state.co.us/Tools/Stations/ARKSALCO'}
        row = {'abbrev':'ARKSALCO','parameter':'DISCHRG','units':'CFS','dataSourceAbbrev':'DWR',
               'stationStatus':'Active','thirdParty':False,'flagA':'O','flagB':None,
               'measValue':258.0,'measDateTime':'2026-10-30T09:00:00-06:00'}
        history = [{**row,'measUnit':'cfs','measDateTime':'2026-10-30T08:45:00','measValue':257},
                   {**row,'measUnit':'cfs','measDateTime':'2026-10-30T09:00:00'}]
        wrap = lambda rows: {'PageCount':1,'PageNumber':1,'ResultCount':len(rows),'ResultList':rows}
        return source, wrap([row]), wrap(history)

    def test_failed_source_requests_back_off_without_extending_reading_age(self):
        key='CDWR:ARKSALCO:DISCHRG'
        with patch.object(server,'_gauge_cache',{}), patch.object(server,'_download_gauge',side_effect=OSError('upstream unavailable')) as fetch:
            for now in [1000,1010,1899]:
                with patch.object(server.time,'time',return_value=now), self.assertRaises(OSError):
                    server._cached_gauge_reading(key)
            self.assertEqual(fetch.call_count,1)
            with patch.object(server.time,'time',return_value=1901), self.assertRaises(OSError):
                server._cached_gauge_reading(key)
            self.assertEqual(fetch.call_count,2)
        entry={'fetchedAt':1000,'failedAt':2000,'data':{'flow':258,'at':12345,'series':[]}}
        with patch.object(server,'_gauge_cache',{key:entry}), patch.object(server,'_download_gauge') as fetch:
            with patch.object(server.time,'time',return_value=2010):
                result=server._cached_gauge_reading(key)
                self.assertTrue(result['stale']);self.assertEqual(result['at'],12345)
            fetch.assert_not_called()

    def test_cdwr_uses_offset_time_and_preserves_true_zero(self):
        source, station, history = self.cdwr_fixture()
        result = parse_cdwr(station, history, source, self.now)
        self.assertEqual((result['flow'],result['at']),(258,datetime(2026,10,30,15,tzinfo=timezone.utc).timestamp()*1000))
        self.assertEqual([p['q'] for p in result['series']],[257,258])
        station['ResultList'][0]['measValue']=0
        self.assertEqual(parse_cdwr(station,history,source,self.now)['flow'],0)
        self.assertEqual(flow_key({'flowSource':source}),'CDWR:ARKSALCO:DISCHRG')
        self.assertIn('Colorado DWR',flow_label({'flowSource':source}))
        self.assertTrue(all(url.startswith('https://dwr.state.co.us/Rest/GET/') for url in cdwr_urls(source,self.now)))

    def test_cdwr_rejects_ice_estimates_bad_units_and_incomplete_responses(self):
        for flag in ('Ice','Bkw','e','Ssn','Eqp'):
            source,station,history=self.cdwr_fixture()
            station['ResultList'][0]['flagB']=flag
            for row in history['ResultList']:row['flagB']=flag
            result=parse_cdwr(station,history,source,self.now)
            self.assertIsNone(result['flow']);self.assertIsNone(result['at']);self.assertEqual(result['series'],[])
        for field,value in [('units','ft'),('parameter','GAGE_HT'),('abbrev','OTHER'),
                            ('measDateTime','2026-10-30T09:00:00'),
                            ('measDateTime','2026-10-30T09:00:00+00:00'),('thirdParty',True)]:
            source,station,history=self.cdwr_fixture();station['ResultList'][0][field]=value
            with self.assertRaises(ValueError):parse_cdwr(station,history,source,self.now)
        source,station,history=self.cdwr_fixture();history['PageCount']=2
        with self.assertRaises(ValueError):parse_cdwr(station,history,source,self.now)

    def test_cdwr_dst_history_does_not_guess_repeated_hour(self):
        source,station,history=self.cdwr_fixture()
        station['ResultList'][0]['measDateTime']='2026-11-01T02:30:00-07:00'
        history['ResultList'][0]['measDateTime']='2026-11-01T01:30:00'
        history['ResultList'][1]['measDateTime']='2026-11-01T02:30:00'
        now=datetime(2026,11,1,10,tzinfo=timezone.utc)
        self.assertEqual(len(parse_cdwr(station,history,source,now)['series']),1)

class OptionalGaugeTests(unittest.TestCase):
    def river(self, relation='none'):
        river=json.loads((Path(__file__).resolve().parents[1]/'catalog/rivers/buffalo-river.json').read_text())
        river['gaugeRelationship']=relation
        river.setdefault('multiDay',False)
        if relation=='none': river['gauge']=None;river['gaugeName']=None
        river['gaugeContext']={'status':'unresolved' if relation=='none' else 'context-only','note':'Reviewed station suitability.','sourceName':'USGS','sourceUrl':'https://waterdata.usgs.gov/','checkedOn':'2026-10-30'}
        return river

    def test_null_gauge_builds_without_erasing_access_or_guide_times(self):
        import shutil,tempfile
        from tools.flow_sources import validate_gauge,flow_url
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            temp=Path(d);shutil.copytree(root/'catalog',temp/'catalog');shutil.copytree(root/'research/routes',temp/'research/routes')
            river=self.river();(temp/'catalog/rivers/buffalo-river.json').write_text(json.dumps(river))
            result=next(r for r in build(temp)['rivers'] if r['id']=='buffalo-river')
            self.assertTrue(any(s.get('mapReleased') for s in result['sections']))
            self.assertTrue(any(s.get('guideTimes') for s in result['sections']))
            validate_gauge(result);self.assertIsNone(flow_key(result));self.assertIsNone(flow_url(result))
            page=seo.river_html(result)
            self.assertIn('No suitable flow gauge',page);self.assertIn('Published guide',page)
            self.assertNotIn('USGS-None',page);self.assertNotIn('href="None"',page)

    def test_gauge_roles_fail_closed_and_require_source_notes(self):
        from tools.flow_sources import validate_gauge,supports_live_timing
        for relation in ('none','same-river-reference','other-river-reference'):
            river=self.river(relation);validate_gauge(river);self.assertFalse(supports_live_timing(river))
            river['timing']={'mode':'model'}
            with self.assertRaises(ValueError):validate_gauge(river)
        river=self.river();river.pop('gaugeContext')
        with self.assertRaises(ValueError):validate_gauge(river)
        for update in ({'gauge':''},{'gauge':12345678},{'gaugeRelationship':'invented'},{'gaugeRelationship':'representative'}):
            with self.assertRaises(ValueError):validate_gauge({**self.river(),**update})

    def test_other_river_reference_is_not_an_allowed_flow_request(self):
        from tools.flow_sources import flow_description
        river=self.river('other-river-reference')
        with patch.object(seo,'load_rivers',return_value=[river,self.river()]):
            self.assertEqual(server._allowed_gauges(),set())
        self.assertIsNone(flow_key(river))
        self.assertIn('another river',flow_description(river))
        page=seo.river_html(river)
        self.assertIn('another river',page);self.assertNotIn('for discharge when a recent reading',page)

    def test_empty_usgs_response_retries_after_cache_expiry(self):
        empty={'flow':None,'at':None,'series':[]};current={'flow':200,'at':1301000,'series':[]}
        with patch.object(server,'_gauge_cache',{}),patch.object(server,'_download_gauge',side_effect=[empty,current]) as fetch:
            with patch.object(server.time,'time',return_value=1000):self.assertEqual(server._cached_gauge_reading('12345678'),empty)
            with patch.object(server.time,'time',return_value=1299):self.assertEqual(server._cached_gauge_reading('12345678'),empty)
            with patch.object(server.time,'time',return_value=1301):self.assertEqual(server._cached_gauge_reading('12345678'),current)
            self.assertEqual(fetch.call_count,2)

    def test_unresolved_routes_never_advertise_a_published_trip_time(self):
        section={'guideTimes':[{'min':2,'max':3,'unit':'hours','conditions':'Guide','sourceName':'Agency','sourceUrl':'https://example.gov'}]}
        self.assertIn('Published guide',seo._guide_html(section))
        for hold in ('accessReview','distanceReview'):
            self.assertEqual(seo._guide_html({**section,hold:'Unresolved endpoints'}),'')
