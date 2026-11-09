"""GIS import checks run in the development GIS environment, never on the server."""
import copy, hashlib, io, json, sqlite3, tempfile, unittest
from urllib.parse import parse_qs,urlparse
from pathlib import Path
from unittest.mock import patch
try:
    from shapely.geometry import LineString
    from shapely import to_wkb
    from tools.import_nhd_routes import network, directed_route, run, download, local_extract, river_names, QUERY_POLICY
    from tools.import_nldi_routes import source_chains, clip_route
except ImportError:
    network = None

@unittest.skipIf(network is None, 'Development-only shapely/pyproj are not installed')
class RouteImporterTests(unittest.TestCase):
    def setUp(self):
        self.project=lambda x,y:(float(x)*100000,float(y)*100000)
        self.unproject=lambda x,y:(float(x)/100000,float(y)/100000)
        self.section={'putInCoords':{'lon':0,'lat':0},'takeOutCoords':{'lon':.02,'lat':0},'miles':1.24}
    def feature(self,key,points):
        return {'attributes':{'permanent_identifier':key,'flowdir':1,'ftype':460},'geometry':{'paths':[points]}}
    def route(self,features,section=None,*,overview=False):
        edges,adj=network({'features':features},self.project)
        return directed_route(edges,adj,section or self.section,self.project,self.unproject,overview=overview)
    def test_connected_directed_network_clips_at_landings(self):
        geom,direction=self.route([self.feature('a',[[0,0],[.01,0]]),self.feature('b',[[.01,0],[.03,0]])])
        self.assertEqual(list(geom['coordinates'][-1]),[.02,0])
        self.assertEqual(direction['featureIds'],['a','b'])
    def test_never_join_gap_reverse_or_choose_ambiguous_channel(self):
        base=[self.feature('a',[[0,0],[.005,0]]),self.feature('b',[[.005,0],[.015,0]]),self.feature('c',[[.015,0],[.025,0]])]
        gap=copy.deepcopy(base);gap[1]['geometry']['paths'][0][0]=[.006,0]
        branch=base+[self.feature('side',[[.005,0],[.01,.002],[.015,0]])]
        reverse=copy.deepcopy(self.section);reverse['putInCoords'],reverse['takeOutCoords']=reverse['takeOutCoords'],reverse['putInCoords']
        for features,section in [(gap,None),(branch,None),(base,reverse)]:
            for overview in (False,True):
                with self.assertRaises(ValueError):self.route(features,section,overview=overview)
    def test_offset_or_undirected_source_stays_held(self):
        f=self.feature('a',[[0,0],[.02,0]]);f['attributes']['flowdir']=0
        with self.assertRaises(ValueError):self.route([f])
        with self.assertRaises(ValueError):self.route([self.feature('a',[[0,.002],[.02,.002]])])
    def test_overview_stages_facility_offsets_without_moving_access_points(self):
        before=copy.deepcopy(self.section)
        features=[self.feature('a',[[0,.002],[.03,.002]])]
        with self.assertRaisesRegex(ValueError,'100 m'):self.route(features)
        geom,direction=self.route(features,overview=True)
        self.assertAlmostEqual(direction['putInOffsetMeters'],200)
        self.assertAlmostEqual(direction['takeOutOffsetMeters'],200)
        self.assertAlmostEqual(direction['putInSourceStationMeters'],0)
        self.assertAlmostEqual(direction['takeOutSourceStationMeters'],2000)
        self.assertEqual(self.section,before)
        self.assertEqual(list(geom['coordinates'][0]),[0,.002])
        self.assertEqual(list(geom['coordinates'][-1]),[.02,.002])
        with self.assertRaisesRegex(ValueError,'1000 m'):
            self.route([self.feature('far',[[0,.011],[.03,.011]])],overview=True)
    def test_submillimeter_source_join_does_not_become_a_duplicate_segment(self):
        features=[self.feature('a',[[0,0],[.01,0]]),self.feature('b',[[.010000005,0],[.03,0]])]
        geometry,_=self.route(features)
        self.assertEqual(len(geometry['coordinates']),3)
        self.assertEqual(list(geometry['coordinates'][-1]),[.02,0])

    def test_online_import_exposes_unnamed_branch_and_preserves_old_evidence(self):
        base=[self.feature('a',[[0,0],[.005,0]]),self.feature('b',[[.005,0],[.015,0]]),self.feature('c',[[.015,0],[.025,0]])]
        for f in base:f['attributes']['gnis_name']="Test's River"
        side=self.feature('side',[[.005,0],[.01,.002],[.015,0]])
        side['attributes']['gnis_name']=None
        self.route(base)  # A name-only source misleadingly appears unique.
        river={'id':'test-river','sections':[self.section]};stream={'riverName':"Test's River"}
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);old=json.dumps({'features':base}).encode()
            (folder/'test-river.json').write_bytes(old)
            def respond(url,timeout):
                where=parse_qs(urlparse(url).query)['where'][0]
                self.assertIn("gnis_name='Test''s River'",where)
                self.assertIn('gnis_name IS NULL',where)
                self.assertIn("gnis_name=''",where)
                return io.BytesIO(json.dumps({'features':base+[side]}).encode())
            with patch('tools.import_nhd_routes.urllib.request.urlopen',side_effect=respond) as fetch:
                path,payload=download(river,stream,folder,False)
            self.assertEqual(fetch.call_count,1)
            self.assertEqual(payload['queryPolicy'],QUERY_POLICY)
            snapshot=folder/('test-river-'+hashlib.sha256(old).hexdigest()[:16]+'.json')
            self.assertEqual(snapshot.read_bytes(),old)
            with self.assertRaisesRegex(ValueError,'multiple downstream'):
                self.route(payload['features'])
            with patch('tools.import_nhd_routes.urllib.request.urlopen',side_effect=AssertionError('Unexpected fetch')):
                self.assertEqual(download(river,stream,folder,False)[1],payload)

    def test_extending_river_sections_refreshes_bounded_source_cache(self):
        river={'id':'test-river','sections':[copy.deepcopy(self.section)]};stream={'riverName':'Test River'}
        payload={'features':[self.feature('a',[[0,0],[.03,0]])]}
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            with patch('tools.import_nhd_routes.urllib.request.urlopen',side_effect=lambda *a,**k:io.BytesIO(json.dumps(payload).encode())) as fetch:
                _,first=download(river,stream,folder,False)
                river['sections'][0]['takeOutCoords']['lon']=.08
                _,second=download(river,stream,folder,False)
            self.assertEqual(fetch.call_count,2)
            self.assertNotEqual(first['queryScope']['bounds'],second['queryScope']['bounds'])

    def test_explicit_tributary_refreshes_source_and_connects_the_trip(self):
        """Minam-like trips need their named tributary, without inventing a join."""
        tributary=self.feature('tributary',[[0,0],[.01,0]])
        tributary['attributes']['gnis_name']='Tributary River'
        main=self.feature('main',[[.01,0],[.03,0]])
        main['attributes']['gnis_name']='Main River'
        river={'id':'test-river','sections':[self.section]}
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            def respond(url,timeout):
                where=parse_qs(urlparse(url).query)['where'][0]
                self.assertIn('gnis_name IS NULL',where)
                self.assertIn("gnis_name=''",where)
                features=[main,tributary] if "gnis_name='Tributary River'" in where else [main]
                return io.BytesIO(json.dumps({'features':features}).encode())
            with patch('tools.import_nhd_routes.urllib.request.urlopen',side_effect=respond) as fetch:
                path,first=download(river,{'riverName':'Main River'},folder,False)
                original=path.read_bytes()
                with self.assertRaisesRegex(ValueError,'100 m'):
                    self.route(first['features'])
                stream={'riverName':'Main River','riverNames':['Tributary River','Main River']}
                _,second=download(river,stream,folder,False)
                _,direction=self.route(second['features'])
                self.assertEqual(direction['featureIds'],['tributary','main'])
                self.assertEqual(second['queryScope']['riverNames'],['Main River','Tributary River'])
                snapshot=folder/('test-river-'+hashlib.sha256(original).hexdigest()[:16]+'.json')
                self.assertEqual(snapshot.read_bytes(),original)
                stream['riverNames'].reverse()
                self.assertEqual(download(river,stream,folder,False)[1],second)
                self.assertEqual(fetch.call_count,2)
                self.assertNotIn('status',second)  # Discovery cannot approve a route.

    def test_tributary_names_must_explicitly_include_primary(self):
        for names in [[],['Other River'],['Main River','Main River'],
                      'Main River',['Main River',None],['Main River',''],
                      ['Main River']+[str(i) for i in range(8)]]:
            with self.subTest(names=names),self.assertRaises(ValueError):
                river_names({'riverName':'Main River','riverNames':names})

    def test_regional_extract_includes_named_tributary_and_unnamed_channels(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);gpkg=root/'1234.gpkg';db=sqlite3.connect(gpkg)
            db.execute('CREATE TABLE gpkg_geometry_columns (table_name TEXT,column_name TEXT,srs_id INTEGER)')
            db.execute("INSERT INTO gpkg_geometry_columns VALUES ('NHDFlowline','SHAPE',4269)")
            db.execute('CREATE TABLE NHDFlowline (OBJECTID INTEGER PRIMARY KEY,permanent_identifier TEXT,gnis_name TEXT,flowdir INTEGER,ftype INTEGER,reachcode TEXT,SHAPE BLOB)')
            db.execute('CREATE TABLE rtree_NHDFlowline_SHAPE (id INTEGER,minx REAL,maxx REAL,miny REAL,maxy REAL)')
            shape=b'GP'+bytes([0,0,0,0,0,0])+to_wkb(LineString([[0,0],[.03,0]]))
            for i,name in enumerate(['Main River','Tributary River',None,'','Unrelated River'],1):
                db.execute('INSERT INTO NHDFlowline VALUES (?,?,?,?,?,?,?)',(i,str(i),name,1,460,'123',shape))
                db.execute('INSERT INTO rtree_NHDFlowline_SHAPE VALUES (?,?,?,?,?)',(i,0,.03,0,0))
            db.commit();db.close()
            (root/'manifest.json').write_text(json.dumps({'hu4':{'1234':{'url':'https://example.org/1234.zip','zipSha256':'abc'}}}))
            stream={'riverName':'Main River','riverNames':['Main River','Tributary River']}
            with patch('tools.import_nhd_routes.ROOT',root),patch('tools.import_nhd_routes.verified_archive',return_value={}):
                _,payload=local_extract({'id':'test-river','sections':[self.section]},stream,root,root,'manifest.json')
            self.assertEqual({f['attributes']['gnis_name'] for f in payload['features']},{'Main River','Tributary River',None,''})
            self.assertEqual(payload['queryScope']['riverNames'],['Main River','Tributary River'])
            self.assertEqual(payload['queryScope']['bounds'],'-0.06,-0.06,0.08,0.06')
            db=sqlite3.connect(gpkg)
            db.execute('ALTER TABLE NHDFlowline RENAME COLUMN OBJECTID TO fid')
            db.execute('ALTER TABLE NHDFlowline RENAME COLUMN SHAPE TO geom')
            db.execute('ALTER TABLE rtree_NHDFlowline_SHAPE RENAME TO rtree_NHDFlowline_geom')
            db.execute("UPDATE gpkg_geometry_columns SET column_name='geom'")
            db.commit();db.close()
            with patch('tools.import_nhd_routes.ROOT',root),patch('tools.import_nhd_routes.verified_archive',return_value={}):
                _,modern=local_extract({'id':'test-river','sections':[self.section]},stream,root,root,'manifest.json')
            self.assertEqual(modern['features'],payload['features'])
            db=sqlite3.connect(gpkg);db.execute('UPDATE gpkg_geometry_columns SET srs_id=3857');db.commit();db.close()
            with patch('tools.import_nhd_routes.ROOT',root),patch('tools.import_nhd_routes.verified_archive',return_value={}):
                with self.assertRaisesRegex(ValueError,'coordinate system'):
                    local_extract({'id':'test-river','sections':[self.section]},stream,root,root,'manifest.json')

    def test_nldi_source_gap_splits_instead_of_drawing_connector(self):
        data={'features':[{'properties':{'nhdplus_comid':str(i)},'geometry':{'type':'LineString','coordinates':c}} for i,c in enumerate([[[0,0],[.005,0]],[[.015,0],[.02,0]]])]}
        chains=source_chains(data);self.assertEqual(len(chains),2)
        with self.assertRaises(ValueError):clip_route(chains,self.section,self.project,self.unproject)

    def test_focused_import_preserves_other_rivers_and_clears_stale_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);folder=root/'research/routes/ID';folder.mkdir(parents=True)
            other={'riverId':'other','sectionId':'keep','geometry':{'type':'LineString','coordinates':[[1,2],[3,4]]}}
            selected={'riverId':'selected','sectionId':'retry'}
            for filename,key in [('hr-candidates.json','routes'),('hr-review-queue.json','sections')]:
                (folder/filename).write_text(json.dumps({'version':1,'state':'ID',key:[other,selected]}))
            config=root/'source.json';config.write_text(json.dumps({'state':'ID','projectedCrs':'EPSG:5070','streams':[{'riverName':'Selected River','riverIds':['selected']}]}))
            rivers=[{'id':name,'state':'ID','sections':[{'id':sid,'mapReleased':True,'mapPrecision':'exact'}]} for name,sid in [('selected','retry'),('other','keep')]]
            with patch('tools.import_nhd_routes.ROOT',root),patch('tools.import_nhd_routes.build',return_value={'rivers':rivers}),patch('tools.import_nhd_routes.download',side_effect=ValueError('source temporarily unavailable')) as fetch:
                run('ID',source_config=config)
            self.assertEqual([call.args[0]['id'] for call in fetch.call_args_list],['selected'])
            candidates=json.loads((folder/'hr-candidates.json').read_text())['routes']
            self.assertEqual(candidates,[other])
            queue=json.loads((folder/'hr-review-queue.json').read_text())['sections']
            self.assertEqual(queue[0],other)
            self.assertEqual(queue[1]['riverId'],'selected')
            self.assertEqual(queue[1]['issues'],['source-unavailable'])
