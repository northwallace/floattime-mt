#!/usr/bin/env python3
"""Build narrow land-display overlays for already reviewed river routes.
Development dependencies: shapely and pyproj; no production dependency.
python tools/build_route_land.py --state MT [--refresh]
"""
import argparse,hashlib,json,sys,urllib.request,urllib.parse
from pathlib import Path
from datetime import date
from concurrent.futures import ThreadPoolExecutor
from shapely.geometry import shape,mapping
from shapely.ops import transform, unary_union
from shapely.validation import make_valid, explain_validity
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.build_catalog import build
from tools.route_catalog import validate

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def normalize_land_polygon(polygon):
    """Remove zero-area self-touch artifacts, never infer new land boundaries.

    Work in projected meters. Area-changing repairs or repairs introducing a
    boundary that was not in the agency geometry still require manual review.
    """
    if polygon.geom_type not in ('Polygon', 'MultiPolygon'):
        raise ValueError('Unexpected source land geometry')
    if polygon.is_valid:
        return polygon, None
    reason = explain_validity(polygon)
    def parts(geometry):
        if geometry.geom_type == 'Polygon':
            return [geometry]
        if hasattr(geometry, 'geoms'):
            return [part for child in geometry.geoms for part in parts(child)]
        return []
    repaired = unary_union(parts(make_valid(polygon)))
    area_delta = abs(repaired.area - polygon.area)
    if (repaired.is_empty or not repaired.is_valid
            or repaired.geom_type not in ('Polygon', 'MultiPolygon')
            or area_delta > .001
            or repaired.boundary.difference(polygon.boundary).length > .01):
        raise ValueError('Invalid source land polygon requires boundary review: ' + reason)
    return repaired, {'method': 'remove-zero-area-self-touch', 'sourceValidity': reason,
                      'areaChangeSquareMeters': area_delta}

def make_overlay(path,config,refresh):
    record=json.loads(path.read_text());land=config['landSource']
    project=Transformer.from_crs(4326,config['projectedCrs'],always_xy=True).transform
    unproject=Transformer.from_crs(config['projectedCrs'],4326,always_xy=True).transform
    route_hash=hashlib.sha256(json.dumps(record['geometry'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    corridor=transform(project,shape(record['geometry'])).buffer(land['corridorMeters'])
    bounds=transform(unproject,corridor).bounds
    folder=ROOT/f'research/routes/{record["state"]}/land'/path.stem/route_hash[:16];folder.mkdir(parents=True,exist_ok=True)
    features=[];inputs=[];dates=[];count=0;normalizations=[]
    for layer in land['layers']:
        cache=folder/f'layer-{layer["id"]}.json'
        params=dict(f='geojson',where='1=1',geometry=','.join(map(str,bounds)),geometryType='esriGeometryEnvelope',inSR=4326,outSR=4326,spatialRel='esriSpatialRelIntersects',outFields=land['outFields'],returnGeometry='true')
        url=land['url']+f'/{layer["id"]}/query'
        if refresh or not cache.exists():
            request=urllib.request.Request(url,data=urllib.parse.urlencode(params).encode())
            response=json.load(urllib.request.urlopen(request,timeout=40))
            if response.get('error') or response.get('exceededTransferLimit'):raise ValueError('Incomplete land response')
            cache.write_text(json.dumps({'checkedOn':str(date.today()),'url':url,'parameters':params,'response':response},separators=(',',':'))+'\n')
        evidence=json.loads(cache.read_text());payload=evidence['response']
        if evidence['parameters']!=params or evidence['url']!=url or payload.get('error') or payload.get('exceededTransferLimit'): raise ValueError('Stale/incomplete land evidence')
        snapshot=folder/f'layer-{layer["id"]}-{sha(cache)[:16]}.json'
        if not snapshot.exists():snapshot.write_bytes(cache.read_bytes())
        inputs.append({'file':str(snapshot.relative_to(ROOT)),'sha256':sha(snapshot)});dates.append(evidence['checkedOn'])
        count+=len(payload['features'])
        for feature in payload['features']:
            polygon=transform(project,shape(feature['geometry']))
            polygon, normalization = normalize_land_polygon(polygon)
            if normalization:
                normalizations.append({**normalization, 'tractId': feature['properties'].get('TractID'),
                                       'inputFile': str(snapshot.relative_to(ROOT))})
            clipped=polygon.intersection(corridor)
            if clipped.is_empty or clipped.area<1:continue
            if clipped.geom_type not in ('Polygon','MultiPolygon'):raise ValueError('Unexpected clipped geometry')
            features.append({'type':'Feature','geometry':mapping(transform(unproject,clipped)),'properties':{**feature['properties'],'mapAccess':layer['category'],'mapAccessLabel':layer['label']}})
    content=json.dumps({'type':'FeatureCollection','features':features},separators=(',',':'))+'\n'
    output=folder/('corridor-'+hashlib.sha256(content.encode()).hexdigest()[:16]+'.json')
    if not output.exists(): output.write_text(content)
    record['landEvidence']={'file':str(output.relative_to(ROOT)),'sha256':sha(output),'routeSha256':route_hash,'url':land['url'],'checkedOn':min(dates),'corridorMeters':land['corridorMeters'],'sourceFeatures':count,'visibleFeatures':len(features),'inputs':inputs}
    if normalizations:record['landEvidence']['normalizations']=normalizations
    record['features']['landOverlay']=True
    path.write_text(json.dumps(record,indent=2)+'\n')
    return f'{path.stem}: {count} source tracts -> {len(features)} near-river tracts'

def run(state,refresh=False):
    config=json.loads((ROOT/f'catalog/routes/sources/{state}.json').read_text());manifest=json.loads((ROOT/f'catalog/routes/{state}.json').read_text())
    paths=[];catalog=build()
    for file in manifest['routes']:
        path=ROOT/'catalog/routes'/file;record=json.loads(path.read_text());validate(record,catalog,ROOT)
        if record['status']=='reviewed' and record['features']['display']:paths.append(path)
    def work(path):
        try:return make_overlay(path,config,refresh)
        except Exception as exc:return path.stem+': not updated: '+type(exc).__name__+': '+str(exc)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(work,paths))
    (ROOT/f'research/routes/{state}/land-review-queue.json').write_text(json.dumps({'state':state,'results':results},indent=2)+'\n')
    for result in results:print(result)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--state',required=True);parser.add_argument('--refresh',action='store_true');args=parser.parse_args();run(args.state,args.refresh)
