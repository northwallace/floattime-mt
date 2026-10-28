#!/usr/bin/env python3
"""Stage agency river lines for review. Never modifies reviewed routes or mileage.
Development dependencies: shapely==2.0.7, pyproj==3.6.1.
Usage: python tools/import_river_routes.py --state MT [--refresh]
"""
import argparse, hashlib, json, math, sys, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from shapely.geometry import LineString, Point, mapping
from shapely.ops import transform, substring
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.build_catalog import build
from tools.route_catalog import geometry_checks

def fetch_source(config, stream, refresh, folder):
    path=folder / ('fwp-'+stream['streamId']+'.json')
    params={'f':'json','where':config['idField']+"='"+stream['streamId']+"'",'outFields':'NAME,LLID,OBJECTID,MILES,BEGMEAS,ENDMEAS,DATASOURCE','outSR':4326,'returnM':'true','returnGeometry':'true'}
    url=config['serviceUrl']+'/query?'+urllib.parse.urlencode(params)
    if refresh or not path.exists():
        response=json.load(urllib.request.urlopen(url,timeout=45))
        if response.get('error') or response.get('exceededTransferLimit'): raise ValueError('Incomplete agency response')
        payload={'checkedOn':str(date.today()),'requestUrl':url,'response':response}
        path.write_text(json.dumps(payload,separators=(',',':'))+'\n')
    payload=json.loads(path.read_text())
    # Keep immutable snapshots: refreshing the download cache cannot rewrite evidence
    # attached to an already reviewed route.
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    snapshot=folder/'sources'/('fwp-'+stream['streamId']+'-'+digest[:16]+'.json')
    snapshot.parent.mkdir(exist_ok=True)
    if not snapshot.exists(): snapshot.write_bytes(path.read_bytes())
    return stream,snapshot,payload

def run(state, refresh=False):
    config=json.loads((ROOT/f'catalog/routes/sources/{state}.json').read_text())
    if config['state']!=state or config['adapter']!='arcgis-measured-line': raise ValueError('Unsupported source adapter')
    folder=ROOT/f'research/routes/{state}';folder.mkdir(parents=True,exist_ok=True)
    sources={}; failures={}
    def load(stream):
        try: return fetch_source(config,stream,refresh,folder),None
        except Exception as exc: return (stream,None,None),type(exc).__name__+': '+str(exc)
    with ThreadPoolExecutor(max_workers=3) as pool:
        for (stream,path,payload),error in pool.map(load,config['streams']):
            for rid in stream['riverIds']:
                if error: failures[rid]=error
                else: sources[rid]=(stream,path,payload)
    project=Transformer.from_crs(4326,config['projectedCrs'],always_xy=True).transform
    unproject=Transformer.from_crs(config['projectedCrs'],4326,always_xy=True).transform
    candidates=[]; summary=[]
    for river in build()['rivers']:
        if river['state']!=state: continue
        for section in river['sections']:
            key=river['id']+'/'+section['id']; row={'riverId':river['id'],'sectionId':section['id'],'issues':[]}
            if section.get('accessReview'):
                row['issues']=['catalog-access-under-review']
                row['detail']=section['accessReview']
                summary.append(row);continue
            if not section.get('mapPilot'):
                row['issues']=['access-points-pending']
                row['detail']=section.get('mapPendingReason','A sourced access record is needed before tracing this section.')
                summary.append(row);continue
            if river['id'] not in sources:
                row['issues']=['source-unavailable' if river['id'] in failures else 'source-not-configured'];summary.append(row);continue
            stream,path,payload=sources[river['id']]
            try:
                response=payload['response'];features=response['features']
                if response.get('error') or response.get('exceededTransferLimit') or len(features)!=1: raise ValueError('Ambiguous or incomplete source')
                feature=features[0]; paths=feature['geometry']['paths']; attrs=feature['attributes']
                if attrs[config['idField']]!=stream['streamId'] or len(paths)!=1: raise ValueError('Stream ID mismatch or disconnected source paths')
                vertices=paths[0]
                if not all(len(p)==3 and all(isinstance(v,(float,int)) and math.isfinite(v) for v in p) for p in vertices): raise ValueError('Source has missing river measures')
                if any(b[2]<a[2] for a,b in zip(vertices,vertices[1:])): raise ValueError('Non-monotonic source river measures')
                line=transform(project,LineString([p[:2] for p in vertices]))
                endpoints=[section[k+'Coords'] for k in ('putIn','takeOut')]
                points=[Point(project(p['lon'],p['lat'])) for p in endpoints]
                distances=[line.project(p) for p in points]
                cut=substring(line,*distances)
                if cut.geom_type!='LineString': raise ValueError('Endpoints collapse to the same river position')
                cumulative=[0]
                for a,b in zip(line.coords,list(line.coords)[1:]): cumulative.append(cumulative[-1]+Point(a).distance(Point(b)))
                def measure(d):
                    import bisect
                    i=min(len(cumulative)-1,max(1,bisect.bisect_left(cumulative,d)))
                    t=(d-cumulative[i-1])/(cumulative[i]-cumulative[i-1]) if cumulative[i]>cumulative[i-1] else 0
                    return vertices[i-1][2]+t*(vertices[i][2]-vertices[i-1][2])
                record={'version':1,'state':state,'riverId':river['id'],'sectionId':section['id'],'status':'candidate',
                    'source':{'name':config['sourceName']+' ('+str(attrs.get('DATASOURCE',''))+')','url':config['serviceUrl'],'checkedOn':payload['checkedOn'],'streamId':stream['streamId'],'objectId':attrs['OBJECTID'],'evidenceFile':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},
                    'putIn':{'name':section['putIn'],**endpoints[0]},'takeOut':{'name':section['takeOut'],**endpoints[1]},'catalogMiles':section['miles'],
                    'geometry':mapping(transform(unproject,cut)),
                    'direction':{'method':'agency-measures-increase-upstream','putInMeasure':measure(distances[0]),'takeOutMeasure':measure(distances[1])},
                    'features':{'display':False,'landOverlay':False,'distanceEstimate':False,'remainingTime':False},
                    'note':'Approximate agency centerline. Not a surveyed landing-to-landing or recommended navigable channel. Side channels and current conditions may differ.'}
                metrics,issues=geometry_checks(record)
                if not cut.is_simple: issues.append('self-intersecting-route')
                if section.get('distanceReview'): issues.append('catalog-distance-under-review')
                if section.get('accessReview'): issues.append('catalog-access-under-review')
                if section.get('mapPrecision')!='exact': issues.append('approximate-access-points')
                record['checks']={'metrics':metrics,'issues':sorted(set(issues))}
                candidates.append(record);row.update(record['checks'])
            except (KeyError,ValueError,TypeError,IndexError) as exc:
                row['issues']=['source-needs-review'];row['detail']=str(exc)
            summary.append(row)
    (folder/'candidates.json').write_text(json.dumps({'version':1,'state':state,'routes':candidates},indent=2)+'\n')
    (folder/'review-queue.json').write_text(json.dumps({'version':1,'state':state,'sourceFailures':failures,'sections':summary},indent=2)+'\n')
    for row in summary:
        print(row['riverId']+'/'+row['sectionId'],json.dumps(row.get('metrics',{})),','.join(row['issues']) or 'checks-pass; review required')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--state',required=True);parser.add_argument('--refresh',action='store_true');args=parser.parse_args();run(args.state,args.refresh)
