import http.client
import hashlib
import re
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server

class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.patchers=[patch.object(server,'DATA_DIR',self.temp.name),patch.object(server,'REPORTS_FILE',self.temp.name+'/reports.json'),patch.object(server,'CONTACTS_FILE',self.temp.name+'/contacts.json'),patch.object(server,'FEEDBACK_FILE',self.temp.name+'/feedback.json'),patch.object(server,'_feedback_attempts',{})]
        for p in self.patchers:p.start()
        self.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        server._gauge_cache.clear()
        self.worker=threading.Thread(target=self.http.serve_forever,daemon=True);self.worker.start()
    def tearDown(self):
        self.http.shutdown();self.http.server_close();self.worker.join()
        for p in self.patchers:p.stop()
        self.temp.cleanup()
    def request(self,method,path,body=None):
        c=http.client.HTTPConnection('127.0.0.1',self.http.server_port,timeout=5)
        c.request(method,path,body=json.dumps(body) if body is not None else None,headers={'Content-Type':'application/json'})
        r=c.getresponse();status=r.status;data=r.read();c.close();return status,json.loads(data)
    def request_raw(self,method,path,headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.http.server_port,timeout=5)
        c.request(method,path,headers=headers or {})
        r=c.getresponse();result=(r.status,dict(r.getheaders()),r.read());c.close();return result
    def test_map_config_exposes_only_browser_key_and_is_not_cached(self):
        with patch.dict(server.os.environ, {"ARCGIS_BASEMAP_API_KEY": "test-public-map-key"}):
            status, headers, body = self.request_raw('GET', '/api/map-config')
            self.assertEqual(status, 200)
            config = json.loads(body)
            self.assertEqual(set(config), {'arcgisApiKey', 'routes'})
            self.assertEqual(config['arcgisApiKey'], 'test-public-map-key')
            self.assertEqual(len(config['routes']), 59)
            self.assertEqual({e['state'] for e in config['routes']}, {'MT','WY'})
            self.assertTrue(all(not e['features']['remainingTime'] and not e['features']['distanceEstimate'] for e in config['routes']))
            self.assertEqual(headers['Cache-Control'], 'no-store')
            self.assertIn('https://ibasemaps-api.arcgis.com', headers['Content-Security-Policy'])
        self.assertEqual(self.request_raw('GET', '/map-config.local.json')[0], 404)

    def test_map_config_local_file_is_allowlisted_and_missing_fails_closed(self):
        with patch.object(server, 'ROOT', self.temp.name), patch.dict(server.os.environ, {"ARCGIS_BASEMAP_API_KEY": ""}):
            self.assertEqual(self.request('GET', '/api/map-config')[0], 503)
            config = Path(self.temp.name, 'map-config.local.json')
            config.write_text(json.dumps({"arcgisApiKey": "local-test-key", "clientSecret": "never-expose"}))
            self.assertEqual(self.request('GET', '/api/map-config')[1], {"arcgisApiKey": "local-test-key"})
            config.write_text('{broken')
            self.assertEqual(self.request('GET', '/api/map-config')[0], 503)

    def test_optional_map_labels_require_explicit_configuration(self):
        with patch.dict(server.os.environ, {'ARCGIS_BASEMAP_API_KEY':'test-key','ARCGIS_LABELS_ENABLED':'true'}):
            self.assertTrue(server._map_config()['imageryLabelsEnabled'])
        with patch.dict(server.os.environ, {'ARCGIS_BASEMAP_API_KEY':'test-key','ARCGIS_LABELS_ENABLED':'false'}):
            self.assertNotIn('imageryLabelsEnabled',server._map_config())

    def test_homepage_state_links_and_counts_work_before_javascript(self):
        status, _, body = self.request_raw('GET','/')
        self.assertEqual(status,200)
        text = body.decode()
        for state in server.seo.catalog()['states']:
            self.assertGreaterEqual(text.count(f'href="/{state["slug"]}"'),2)
        rivers = server.seo.catalog()['rivers']
        self.assertIn(f'id="statRivers">{len(rivers)}<',text)
        self.assertIn(f'id="statSections">{sum(len(r["sections"]) for r in rivers)}<',text)
        self.assertNotIn('<!-- catalog:',text)

    def test_route_pilot_requires_local_opt_in_and_is_off_with_production_key(self):
        root = Path(self.temp.name)
        (root / 'map-config.local.json').write_text(json.dumps({"arcgisApiKey":"local-test", "routePilotEnabled":True}))
        index = root / 'catalog' / 'route_pilots' / 'index.json'
        index.parent.mkdir(parents=True)
        routes = [{"riverId":"blackfoot", "sectionId":"johnsrud-weigh-station", "file":"route-pilots/test.json"}]
        index.write_text(json.dumps({"routes":routes}))
        with patch.object(server, 'ROOT', self.temp.name), patch.dict(server.os.environ, {"ARCGIS_BASEMAP_API_KEY":""}):
            self.assertEqual(server._map_config()['routePilots'], routes)
            index.write_text('{broken')
            self.assertEqual(server._map_config(), {"arcgisApiKey":"local-test"})
        with patch.object(server, 'ROOT', self.temp.name), patch.dict(server.os.environ, {"ARCGIS_BASEMAP_API_KEY":"production-test"}):
            self.assertEqual(server._map_config(), {"arcgisApiKey":"production-test"})

    def test_route_maps_are_local_and_independent_of_gps_experiment(self):
        root=Path(self.temp.name)
        (root/'map-config.local.json').write_text(json.dumps({"arcgisApiKey":"test-key","routeMapsEnabled":True,"routePilotEnabled":False}))
        routes_dir=root/'public/routes';routes_dir.mkdir(parents=True)
        entries=[{"riverId":"blackfoot","sectionId":"a","file":"routes/test.json"}]
        (routes_dir/'index.json').write_text(json.dumps({"routes":entries}))
        with patch.object(server,'ROOT',str(root)), patch.object(server,'PUBLIC',str(root/'public')), patch.dict(server.os.environ,{"ARCGIS_BASEMAP_API_KEY":""}):
            self.assertEqual(server._map_config(),{"arcgisApiKey":"test-key","routes":entries})
        with patch.object(server,'ROOT',str(root)), patch.object(server,'PUBLIC',str(root/'public')), patch.dict(server.os.environ,{"ARCGIS_BASEMAP_API_KEY":"production-key"}):
            self.assertEqual(server._map_config(),{"arcgisApiKey":"production-key"})

    def test_reports_votes_and_private_metadata(self):
        status,r=self.request('POST','/api/reports',{'riverId':'madison-upper','description':'Test only','type':'strainer'})
        self.assertEqual(status,201)
        self.assertEqual(r['riverId'],'madison-upper')
        self.assertEqual(self.request('POST',f'/api/reports/{r["id"]}/cleared')[0],200)
        self.assertEqual(self.request('POST',f'/api/reports/{r["id"]}/cleared')[0],409)
        r.update(clearedVotes=8,_voters=['private']);server._save_reports([r])
        status,reports=self.request('GET','/api/reports');self.assertEqual(len(reports),1);self.assertNotIn('_voters',reports[0])
    def test_invalid_river_rejected(self):
        self.assertEqual(self.request('POST','/api/reports',{'river':'Invented','description':'Test'})[0],400)

    def test_contact_validation_and_storage(self):
        self.assertEqual(self.request('POST','/api/contact',{
            'name':'River User','email':'not-an-email','message':'Hello'
        })[0],400)
        status,response=self.request('POST','/api/contact',{
            'name':' River User ','email':'RIVER@EXAMPLE.COM','message':' Please add a river. '
        })
        self.assertEqual(status,201)
        self.assertEqual(response,{'ok':True})
        contacts=server._load_contacts()
        self.assertEqual(len(contacts),1)
        self.assertEqual(contacts[0]['email'],'river@example.com')
        self.assertEqual(contacts[0]['message'],'Please add a river.')
    def test_expired_reports_hidden(self):
        server._save_reports([{'id':'abc','createdAt':time.time()-46*86400}])
        self.assertEqual(self.request('GET','/api/reports')[1],[])

    def test_section_correction_is_canonical_private_and_does_not_change_catalog(self):
        before=Path(server.PUBLIC,'catalog.json').read_bytes()
        status,data=self.request('POST','/api/feedback',{
            'type':'correction','riverId':'madison-upper','sectionId':'lyons-palisades',
            'category':'map-location','message':'The landing should be checked.',
            'riverName':'Spoofed river','putIn':'Wrong put-in','email':'PERSON@EXAMPLE.COM'
        })
        self.assertEqual(status,201)
        self.assertEqual(set(data),{'ok','id'})
        entry=server._load_feedback()[0]
        self.assertEqual(entry['riverName'],'Madison River (Upper)')
        self.assertEqual(entry['putIn'],'Lyons Bridge')
        self.assertEqual(entry['sectionId'],'lyons-palisades')
        self.assertEqual(entry['email'],'person@example.com')
        self.assertEqual(entry['status'],'pending')
        self.assertEqual(before,Path(server.PUBLIC,'catalog.json').read_bytes())
        self.assertEqual(self.request_raw('GET','/api/feedback')[0],404)
        self.assertEqual(self.request_raw('GET','/api/private-review')[0],404)
        self.assertEqual(self.request_raw('GET','/review')[0],404)
        self.assertEqual(self.request_raw('GET','/data/feedback.json')[0],404)

    def test_requests_accept_new_states_without_requiring_contact_details(self):
        status,data=self.request('POST','/api/feedback',{
            'type':'float-request','state':'Colorado','riverName':'Example River',
            'putIn':'Public Launch','takeOut':'Public Landing','message':'Please research this float.'
        })
        self.assertEqual(status,201)
        entry=server._load_feedback()[0]
        self.assertEqual(entry['state'],'Colorado')
        self.assertEqual(entry['email'],'')
        self.assertEqual(entry['status'],'pending')

    def test_feedback_rejects_invalid_context_and_values(self):
        body={'type':'correction','riverId':'madison-upper','sectionId':'not-real','category':'other','message':'Check this'}
        self.assertEqual(self.request('POST','/api/feedback',body)[0],400)
        body['sectionId']='';body['email']='invalid'
        self.assertEqual(self.request('POST','/api/feedback',body)[0],400)
        body['email']='';body['sourceUrl']='javascript:alert(1)'
        self.assertEqual(self.request('POST','/api/feedback',body)[0],400)
        body['sourceUrl']='https://[invalid'
        self.assertEqual(self.request('POST','/api/feedback',body)[0],400)
        body['sourceUrl']='';body['message']='x'*2001
        self.assertEqual(self.request('POST','/api/feedback',body)[0],400)
        self.assertEqual(server._load_feedback(),[])

    def test_feedback_capacity_and_storage_errors_do_not_claim_success(self):
        body={'type':'float-request','state':'Colorado','riverName':'Test','putIn':'A','takeOut':'B','message':'Test only'}
        with patch.object(server,'MAX_FEEDBACK',0):
            self.assertEqual(self.request('POST','/api/feedback',body)[0],503)
        with patch.object(server,'_save_json',side_effect=OSError('disk unavailable')):
            self.assertEqual(self.request('POST','/api/feedback',body)[0],503)
        self.assertEqual(server._load_feedback(),[])

    def test_feedback_rate_limit_and_honeypot(self):
        body={'type':'float-request','state':'Colorado','riverName':'Test','putIn':'A','takeOut':'B','message':'Test only'}
        self.assertEqual(self.request('POST','/api/feedback',{**body,'website':'spam'})[0],201)
        self.assertEqual(server._load_feedback(),[])
        for _ in range(6): self.assertEqual(self.request('POST','/api/feedback',body)[0],201)
        self.assertEqual(self.request('POST','/api/feedback',body)[0],429)
        self.assertEqual(len(server._load_feedback()),6)
        # Distinct visitors behind the hosting proxy do not share one bucket.
        self.assertEqual(self.request('POST','/api/feedback',{**body,'clientToken':'another-page'})[0],201)
        self.assertNotIn('clientToken',server._load_feedback()[-1])

    def test_gauge_proxy_validates_and_caches_catalog_sites(self):
        reading={'flow':1234,'at':time.time()*1000,'temp':10,'tempAt':time.time()*1000,'series':[],'source':'USGS Water Data API'}
        with patch.object(server,'_download_gauge',return_value=reading) as download:
            self.assertEqual(self.request('GET','/api/gauge?site=06041000')[1]['flow'],1234)
            self.assertEqual(self.request('GET','/api/gauge?site=06041000')[1]['flow'],1234)
            self.assertEqual(download.call_count,1)
        self.assertEqual(self.request('GET','/api/gauge?site=00000000')[0],404)

    def test_reclamation_proxy_only_serves_reviewed_catalog_sources(self):
        reading={'flow':25.2,'at':time.time()*1000,'temp':None,'tempAt':None,'series':[],
                 'source':'Bureau of Reclamation GP Hydromet','provisional':True}
        with patch.object(server,'_download_gauge',return_value=reading) as download:
            self.assertEqual(self.request('GET','/api/gauge?site=USBR%3AGLWY%3AQ')[1]['flow'],25.2)
            self.assertEqual(self.request('GET','/api/gauge?site=USBR%3AGLWY%3AQ')[1]['source'],reading['source'])
            download.assert_called_once_with('USBR:GLWY:Q')
            for key in ('USBR:UNKNOWN:Q','USBR:GLWY:GH','https://example.com/'):
                self.assertEqual(self.request('GET','/api/gauge?site='+key)[0],404)

    def test_colorado_dwr_proxy_only_serves_reviewed_discharge(self):
        reading={'flow':258,'at':time.time()*1000,'series':[],
                 'source':'Colorado Division of Water Resources','provisional':True}
        with patch.object(server,'_download_gauge',return_value=reading) as download:
            for _ in range(2):
                self.assertEqual(self.request('GET','/api/gauge?site=CDWR%3AARKSALCO%3ADISCHRG')[1]['flow'],258)
            download.assert_called_once_with('CDWR:ARKSALCO:DISCHRG')
            for key in ('CDWR:OTHER:DISCHRG','CDWR:ARKSALCO:GAGE_HT'):
                self.assertEqual(self.request('GET','/api/gauge?site='+key)[0],404)

    def test_security_server_identity_and_static_cache_headers(self):
        version=hashlib.sha256(Path(server.PUBLIC,'styles.css').read_bytes()).hexdigest()[:20]
        asset='/styles.css?v='+version
        status,headers,_=self.request_raw('GET',asset)
        self.assertEqual(status,200)
        self.assertEqual(headers['Server'],'FloatETA/1.0')
        self.assertEqual(headers['X-Content-Type-Options'],'nosniff')
        self.assertEqual(headers['Permissions-Policy'],'camera=(), microphone=(), geolocation=(self)')
        self.assertIn('immutable',headers['Cache-Control'])
        self.assertIn('Content-Security-Policy',headers)
        etag=headers['ETag']
        status,_,body=self.request_raw('GET',asset,{'If-None-Match':etag})
        self.assertEqual((status,body),(304,b''))
        self.assertNotIn('immutable',self.request_raw('GET','/styles.css?v=old-version')[1]['Cache-Control'])

    def test_static_and_generated_html_use_current_asset_fingerprints(self):
        for page in ['/', '/about.html', '/directory.html', '/rivers/blackfoot']:
            status,_,body=self.request_raw('GET',page)
            self.assertEqual(status,200)
            links=re.findall(rb'(?:src|href)="(/?[\w-]+\.(?:css|js))\?v=([0-9a-f]{20})"',body)
            self.assertTrue(links,page)
            for asset,digest in links:
                self.assertEqual(digest.decode(),hashlib.sha256(Path(server.PUBLIC,asset.decode().lstrip('/')).read_bytes()).hexdigest()[:20])

    def test_asset_edit_changes_html_url_and_etag_without_manual_version_bump(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(server,'PUBLIC',folder):
            Path(folder,'index.html').write_text('<script src="app.js?v=old"></script>')
            asset=Path(folder,'app.js');asset.write_text('first')
            _,headers,before=self.request_raw('GET','/')
            asset.write_text('second')
            status,after_headers,after=self.request_raw('GET','/',{'If-None-Match':headers['ETag']})
            self.assertEqual(status,200)
            self.assertNotEqual(before,after)
            self.assertNotEqual(headers['ETag'],after_headers['ETag'])

    def test_directory_contains_server_rendered_river_links(self):
        status,_,body=self.request_raw('GET','/directory.html')
        self.assertEqual(status,200)
        self.assertIn(b'/rivers/madison-upper',body)

    def test_state_release_allows_reviewed_lines_with_production_key_only_for_selected_states(self):
        root=Path(self.temp.name)
        (root/'catalog').mkdir()
        settings=root/'catalog/settings.json'
        settings.write_text(json.dumps({'mapRelease':{'states':['MT'],'reviewedRoutes':True}}))
        (root/'public/routes').mkdir(parents=True)
        entries=[{'riverId':'blackfoot','state':'MT'}, {'riverId':'yakima-canyon','state':'WA'}]
        (root/'public/routes/index.json').write_text(json.dumps({'routes':entries}))
        with patch.object(server,'ROOT',str(root)), patch.object(server,'PUBLIC',str(root/'public')), patch.dict(server.os.environ,{'ARCGIS_BASEMAP_API_KEY':'production-key'}):
            self.assertEqual(server._map_config()['routes'], entries[:1])
            settings.write_text(json.dumps({'mapRelease':{'states':[],'reviewedRoutes':True}}))
            self.assertEqual(server._map_config()['routes'], [])
            settings.write_text(json.dumps({'mapRelease':{'states':['MT'],'reviewedRoutes':False}}))
            self.assertNotIn('routes',server._map_config())

    def test_corrupt_report_or_contact_storage_is_preserved_and_returns_503(self):
        for filename,endpoint,body in [
            ('reports.json','/api/reports',{'riverId':'blackfoot','description':'Test','type':'strainer'}),
            ('contacts.json','/api/contact',{'name':'Test','email':'test@example.com','message':'Test'})]:
            path=Path(self.temp.name,filename)
            for content in ('{broken', '{}', '[1]'):
                path.write_text(content)
                self.assertEqual(self.request('POST',endpoint,body)[0],503)
                self.assertEqual(path.read_text(),content)
            if filename=='reports.json':
                self.assertEqual(self.request('GET',endpoint)[0],503)
                self.assertEqual(self.request('POST','/api/reports/123456789abc/confirm')[0],503)

    def test_submission_write_failure_never_reports_success(self):
        with patch.object(server.os,'replace',side_effect=OSError('disk error')):
            self.assertEqual(self.request('POST','/api/reports',{'riverId':'blackfoot','description':'Test'})[0],503)
            self.assertEqual(self.request('POST','/api/contact',{'name':'Test','email':'test@example.com','message':'Test'})[0],503)

    def test_simultaneous_gauge_requests_share_one_upstream_call(self):
        from concurrent.futures import ThreadPoolExecutor
        def fetch(gauge):
            time.sleep(.05)
            return {'flow':100,'at':time.time()*1000,'series':[]}
        with patch.object(server,'_download_gauge',side_effect=fetch) as download:
            with ThreadPoolExecutor(max_workers=5) as pool:
                results=list(pool.map(server._gauge_reading,['12340000']*5))
            self.assertEqual(download.call_count,1)
            self.assertTrue(all(r['flow']==100 for r in results))

    def test_relative_static_paths_cannot_read_private_files(self):
        self.assertEqual(self.request_raw('GET','../server.py')[0],403)
        self.assertEqual(self.request_raw('GET','../map-config.local.json')[0],403)
        self.assertEqual(self.request_raw('GET','../data/feedback.json')[0],403)
