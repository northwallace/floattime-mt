"""GIS import checks run in the development GIS environment, never on the server."""
import copy, unittest
try:
    from shapely.geometry import LineString
    from tools.import_nhd_routes import network, directed_route
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
    def route(self,features,section=None):
        edges,adj=network({'features':features},self.project)
        return directed_route(edges,adj,section or self.section,self.project,self.unproject)
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
            with self.assertRaises(ValueError):self.route(features,section)
    def test_offset_or_undirected_source_stays_held(self):
        f=self.feature('a',[[0,0],[.02,0]]);f['attributes']['flowdir']=0
        with self.assertRaises(ValueError):self.route([f])
        with self.assertRaises(ValueError):self.route([self.feature('a',[[0,.002],[.02,.002]])])
    def test_nldi_source_gap_splits_instead_of_drawing_connector(self):
        data={'features':[{'properties':{'nhdplus_comid':str(i)},'geometry':{'type':'LineString','coordinates':c}} for i,c in enumerate([[[0,0],[.005,0]],[[.015,0],[.02,0]]])]}
        chains=source_chains(data);self.assertEqual(len(chains),2)
        with self.assertRaises(ValueError):clip_route(chains,self.section,self.project,self.unproject)
