#!/usr/bin/env python3
"""Build a local-only Blackfoot route pilot from cached official GIS evidence.
Dev dependencies: shapely, pyproj. Never promotes a route to production.
Run: python tools/build_route_pilot.py [--refresh-land]
"""
import argparse,json,urllib.request,urllib.parse
from pathlib import Path
from datetime import date
from shapely.geometry import LineString, Point, shape, mapping
from shapely.ops import transform, substring
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'research/MT/route-pilot-20261027'
SOURCE='https://fwp-gis.mt.gov/arcgis/rest/services/refrnc/hydrography/MapServer/20'
DNRC='https://gis.dnrc.mt.gov/arcgis/rest/services/TLMD/AccessMap/FeatureServer'

def build(refresh=False):
    raw=json.loads((EVIDENCE/'blackfoot-source.json').read_text())
    features=raw['response']['features']
    assert len(features)==1 and not raw['response'].get('exceededTransferLimit')
    f=features[0]; assert f['attributes']['LLID']=='1138907468712' and len(f['geometry']['paths'])==1
    project=Transformer.from_crs(4326,32612,always_xy=True).transform
    unproject=Transformer.from_crs(32612,4326,always_xy=True).transform
    line=transform(project,LineString([p[:2] for p in f['geometry']['paths'][0]]))
    river=json.loads((ROOT/'public/catalog.json').read_text())
    river=next(r for r in river['rivers'] if r['id']=='blackfoot')
    section=next(s for s in river['sections'] if s['id']=='johnsrud-weigh-station')
    endpoints=[section[k+'Coords'] for k in ['putIn','takeOut']]
    points=[Point(project(p['lon'],p['lat'])) for p in endpoints]
    measures=[line.project(p) for p in points]
    offsets=[line.distance(p) for p in points]
    assert max(offsets)<100, 'Endpoint too far from agency centerline; review manually'
    # FWP line runs upstream from the mouth. Pilot must run downstream.
    assert measures[0]>measures[1]
    route=substring(line,*measures)
    miles=route.length/1609.344
    assert abs(miles-section['miles'])/section['miles']<.05
    corridor=route.buffer(150)
    geo=mapping(transform(unproject,route)); bounds=transform(unproject,corridor).bounds
    clipped=[]; source_count=0
    for layer,category,label in [(0,'no','No public access'),(1,'public','Public access'),(2,'special','Special conditions')]:
        path=EVIDENCE/f'dnrc-{layer}.json'
        params=dict(f='geojson',where='1=1',geometry=','.join(map(str,bounds)),geometryType='esriGeometryEnvelope',inSR=4326,outSR=4326,spatialRel='esriSpatialRelIntersects',outFields='TractID,Acres,Access_Type,Access_Type_Spcl,Verified',returnGeometry='true')
        if refresh or not path.exists():
            req=urllib.request.Request(DNRC+f'/{layer}/query',data=urllib.parse.urlencode(params).encode())
            payload=json.load(urllib.request.urlopen(req,timeout=40))
            assert 'error' not in payload and not payload.get('exceededTransferLimit'), 'Incomplete DNRC response'
            path.write_text(json.dumps({'checkedOn':str(date.today()),'requestUrl':DNRC+f'/{layer}/query','parameters':params,'response':payload},indent=2))
        evidence=json.loads(path.read_text()); payload=evidence['response']
        assert not payload.get('exceededTransferLimit') and 'error' not in payload
        source_count+=len(payload['features'])
        for feature in payload['features']:
            polygon=transform(project,shape(feature['geometry']))
            assert polygon.is_valid, 'Agency polygon invalid; review before use'
            cut=polygon.intersection(corridor)
            if cut.is_empty or cut.area<1: continue
            if cut.geom_type not in ('Polygon','MultiPolygon'): continue
            clipped.append({'type':'Feature','geometry':mapping(transform(unproject,cut)),'properties':{**feature['properties'],'mapAccess':category,'mapAccessLabel':label}})
    result={'version':1,'status':'local-pilot','riverId':'blackfoot','sectionId':section['id'],
      'sourceName':'Montana FWP hydrography (PNW centerline)','sourceUrl':SOURCE,'sourceObjectId':63907,'streamId':'1138907468712','checkedOn':raw['checkedOn'],
      'note':'Approximate agency centerline, not a surveyed or recommended navigable channel. Current channels and landing positions may differ.',
      'putIn':endpoints[0],'takeOut':endpoints[1],'endpointOffsetsMeters':[round(v,1) for v in offsets],
      'catalogMiles':section['miles'],'routeMiles':round(miles,4),'geometry':geo,
      'corridorMeters':150,'landSourceUrl':DNRC,'landCheckedOn':evidence['checkedOn'],
      'landNote':'Only portions of DNRC trust-land polygons within 150 metres of the approximate river line are shown. Display edges are clipped, not property boundaries or proof of river access.',
      'land':{'type':'FeatureCollection','features':clipped},'landFeaturesBeforeFilter':source_count}
    dest=ROOT/'public/route-pilots/blackfoot-johnsrud-weigh-station.json'
    dest.write_text(json.dumps(result,separators=(',',':'))+'\n')
    (ROOT/'catalog/route_pilots/index.json').write_text(json.dumps({'version':1,'routes':[{'riverId':result['riverId'],'sectionId':result['sectionId'],'file':'route-pilots/'+dest.name,'status':'local-pilot'}]},indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['routeMiles','endpointOffsetsMeters','landFeaturesBeforeFilter']}));print('Clipped land polygons:',len(clipped),'route vertices:',len(geo['coordinates']))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--refresh-land',action='store_true');build(parser.parse_args().refresh_land)
