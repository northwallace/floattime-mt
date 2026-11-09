#!/usr/bin/env python3
"""Stage high-resolution, flow-directed USGS river paths. Never auto-approves.
python tools/import_nhd_routes.py --state WY --gpkg-dir /path/to/verified/archives
Uses named-river and unnamed flowlines within the access-point envelope plus a 0.06 degree margin.
Ambiguous branches, gaps and reversed endpoints stay in review. Use
--overview-candidates to stage display-only candidates near approximate access
areas. They still require a separate overview review; this command never approves.
"""
import argparse, hashlib, json, sys, sqlite3, urllib.parse, urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from functools import lru_cache
from shapely.geometry import LineString, Point, mapping
from shapely.ops import transform, substring
from shapely import from_wkb
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.build_catalog import build
from tools.route_catalog import geometry_checks, distance, OVERVIEW_MAX_OFFSET_METERS
SERVICE='https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/6'
QUERY_POLICY='named-and-unnamed-flowlines-v1'


def river_names(stream):
    """Explicit named tributaries for trips that cross a documented confluence.

    This only broadens source discovery. Branches still require review, and
    every candidate remains disabled until its geometry is checked.
    """
    primary=stream.get('riverName')
    names=stream.get('riverNames',[primary])
    if (not isinstance(primary,str) or not primary.strip() or
            not isinstance(names,list) or not 1<=len(names)<=8 or
            any(not isinstance(n,str) or not n.strip() or len(n)>160 for n in names) or
            len(set(names))!=len(names) or primary not in names):
        raise ValueError('River names must explicitly include the primary river and unique named tributaries')
    return sorted(names)


@lru_cache(maxsize=32)
def verified_archive(gpkg,expected_zip_hash):
    receipt=json.loads(gpkg.with_suffix('.verified.json').read_text())
    from tools.fetch_nhd_archives import digest
    if receipt['archiveSha256']!=expected_zip_hash or digest(gpkg)!=receipt['gpkgSha256']:
        raise ValueError('Local GeoPackage differs from its verified source archive')
    return receipt


def network(payload,project):
    edges={};adj=defaultdict(list)
    for f in payload['features']:
        a={k.lower():v for k,v in f['attributes'].items()}
        if a.get('flowdir')!=1 or a.get('ftype') not in (460,558):continue
        paths=f['geometry']['paths']
        if len(paths)!=1:continue
        points=paths[0];coords=[]
        for p in points:
            if not coords or p[:2]!=coords[-1]:coords.append(p[:2])
        if len(coords)<2:continue
        key=str(a['permanent_identifier']);start=tuple(round(v,7) for v in coords[0]);end=tuple(round(v,7) for v in coords[-1])
        line=transform(project,LineString(coords))
        edges[key]={'line':line,'coordinates':coords,'start':start,'end':end}
        adj[start].append(key)
    return edges,adj


def directed_route(edges,adj,section,project,unproject,*,overview=False):
    selected=[];offsets=[]
    # An overview stages river geometry near a facility, not a landing connection.
    # Keep the original access snapshots; review must explain offsets over 100 m.
    max_offset=OVERVIEW_MAX_OFFSET_METERS if overview else 100
    for end in ('putIn','takeOut'):
        p=section[end+'Coords'];pt=Point(project(p['lon'],p['lat']))
        distances=sorted((e['line'].distance(pt),key) for key,e in edges.items())
        if not distances or distances[0][0]>max_offset:raise ValueError(f'Access is more than {max_offset} m from the directed river network')
        # A nearby second branch is not grounds for moving a reviewed landing.
        key=distances[0][1];selected.append((key,edges[key]['line'].project(pt)));offsets.append(distances[0][0])
    (start,a),(finish,b)=selected;paths=[];stack=[(start,[start],0)]
    max_m=section['miles']*1609.344*1.5+2000
    while stack and len(paths)<2:
        key,seen,length=stack.pop()
        if key==finish:
            if key!=start or b>a:paths.append(seen)
            continue
        if length>max_m or len(seen)>1500:continue
        for nxt in adj.get(edges[key]['end'],[]):
            if nxt not in seen:stack.append((nxt,seen+[nxt],length+edges[key]['line'].length))
    if len(paths)!=1:raise ValueError('River network is disconnected, reversed or has multiple downstream channel paths')
    ids=paths[0];coords=[]
    for i,key in enumerate(ids):
        line=edges[key]['line'];part=substring(line,a if i==0 else 0,b if i==len(ids)-1 else line.length)
        if part.geom_type!='LineString':continue
        for p in transform(unproject,part).coords:
            # Adjacent source edges can repeat a join with sub-millimetre rounding.
            # Remove only that redundant vertex; metre-scale gaps still fail review.
            if not coords or distance(coords[-1],p)>.001:coords.append(list(p))
    result=LineString(coords)
    if not result.is_simple:raise ValueError('Self-intersecting river path')
    return mapping(result),{'method':'usgs-flow-directed-network','featureIds':ids,'putInOffsetMeters':offsets[0],'takeOutOffsetMeters':offsets[1],'putInSourceStationMeters':a,'takeOutSourceStationMeters':b}


def local_extract(river,stream,folder,gpkg_dir,archive_manifest):
    names=river_names(stream)
    points=[s[k] for s in river['sections'] for k in ('putInCoords','takeOutCoords') if k in s]
    if not points:raise ValueError('No mapped endpoints')
    west=min(p['lon'] for p in points)-.06;east=max(p['lon'] for p in points)+.06
    south=min(p['lat'] for p in points)-.06;north=max(p['lat'] for p in points)+.06
    features={};archives=[]
    meta=json.loads((ROOT/archive_manifest).read_text())['hu4']
    for gpkg in sorted(gpkg_dir.glob('*.gpkg')):
        h=gpkg.stem
        if h not in meta:continue
        receipt=verified_archive(gpkg,meta[h]['zipSha256'])
        conn=sqlite3.connect('file:'+str(gpkg)+'?mode=ro',uri=True)
        # USGS snapshots use both SHAPE/OBJECTID and geom/fid. Read the
        # GeoPackage schema instead of assuming the older field names.
        geom=conn.execute("SELECT column_name,srs_id FROM gpkg_geometry_columns WHERE table_name='NHDFlowline'").fetchone()
        primary=[c[1] for c in conn.execute('PRAGMA table_info(NHDFlowline)') if c[5]]
        if not geom or geom[1] not in (4269,4326) or len(primary)!=1:
            conn.close();raise ValueError('Unsupported regional flowline geometry or coordinate system')
        def identifier(name):return '"'+name.replace('"','""')+'"'
        geometry_column=identifier(geom[0]);index=identifier('rtree_NHDFlowline_'+geom[0]);key=identifier(primary[0])
        sql=f"""SELECT t.permanent_identifier,t.gnis_name,t.flowdir,t.ftype,t.reachcode,t.{geometry_column}
          FROM NHDFlowline t JOIN {index} r ON t.{key}=r.id
          WHERE r.minx<=? AND r.maxx>=? AND r.miny<=? AND r.maxy>=?
          AND (t.gnis_name IN ("""+','.join('?' for _ in names)+""") OR t.gnis_name IS NULL OR t.gnis_name='') AND t.ftype IN (460,558)"""
        count=0
        for row in conn.execute(sql,(east,west,north,south,*names)):
            attrs=dict(zip(('permanent_identifier','gnis_name','flowdir','ftype','reachcode'),row[:5]));blob=row[5]
            offset=8+[0,32,48,48,64][(blob[3]>>1)&7];geom=from_wkb(blob[offset:])
            lines=list(geom.geoms) if geom.geom_type=='MultiLineString' else [geom]
            features[str(row[0])]={'attributes':attrs,'geometry':{'paths':[[list(p[:2]) for p in line.coords] for line in lines]}}
            count+=1
        conn.close()
        if count:archives.append({**meta[h],**receipt})
    if not features:raise ValueError('No source flowlines in the available regional archives')
    scope={'riverName':stream['riverName'],'bounds':f'{west},{south},{east},{north}'}
    if len(names)>1:scope['riverNames']=names
    payload={'checkedOn':date.today().isoformat(),'queryPolicy':QUERY_POLICY,'queryScope':scope,'sourceUrl':archives[0]['url'],'archives':archives,'crs':'NAD83 geographic (EPSG:4269); approximately WGS84 at map scale','features':list(features.values())}
    path=folder/(river['id']+'.json');path.write_text(json.dumps(payload,separators=(',',':'))+'\n');return path,payload


def download(river,stream,folder,refresh):
    names=river_names(stream)
    path=folder/(river['id']+'.json')
    points=[s[k] for s in river['sections'] for k in ('putInCoords','takeOutCoords') if k in s]
    if not points:raise ValueError('No mapped endpoints')
    # Include unnamed alternatives, as local archives do. A name-only query can
    # hide a side channel and falsely make the downstream graph appear unique.
    lo=min(p['lon'] for p in points);hi=max(p['lon'] for p in points);bottom=min(p['lat'] for p in points);top=max(p['lat'] for p in points)
    margin=.06
    box=f'{lo-margin},{bottom-margin},{hi+margin},{top+margin}'
    scope={'riverName':stream['riverName'],'bounds':box}
    if len(names)>1:scope['riverNames']=names
    if path.exists():
        raw=path.read_bytes();cached=json.loads(raw)
        if not refresh and cached.get('queryPolicy')==QUERY_POLICY and cached.get('queryScope')==scope:
            return path,cached
        # Preserve prior source evidence before changing the working cache.
        digest=hashlib.sha256(raw).hexdigest();snapshot=folder/(river['id']+'-'+digest[:16]+'.json')
        if snapshot.exists() and snapshot.read_bytes()!=raw:
            raise ValueError('Existing source snapshot does not match its content hash')
        if not snapshot.exists():snapshot.write_bytes(raw)
    named=' OR '.join("gnis_name='"+name.replace("'","''")+"'" for name in names)
    params={'f':'json','where':f"({named} OR gnis_name IS NULL OR gnis_name='') AND ftype IN (460,558)", 'geometry':box,'geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'permanent_identifier,gnis_name,flowdir,ftype,reachcode','outSR':4326,'returnGeometry':'true','resultRecordCount':1000}
    features=[];urls=[]
    for offset in range(0,20000,1000):
        params['resultOffset']=offset;url=SERVICE+'/query?'+urllib.parse.urlencode(params)
        with urllib.request.urlopen(url,timeout=35) as response:data=json.load(response)
        if data.get('error'):raise ValueError(str(data['error']))
        features.extend(data.get('features',[]));urls.append(url)
        if not data.get('exceededTransferLimit'):break
    else:raise ValueError('Source result limit reached')
    if not features:raise ValueError('No source flowlines')
    payload={'checkedOn':date.today().isoformat(),'queryPolicy':QUERY_POLICY,'queryScope':scope,'sourceUrl':SERVICE,'requests':urls,'features':features}
    path.write_text(json.dumps(payload,separators=(',',':'))+'\n');return path,payload


def run(state,refresh=False,gpkg_dir=None,source_config=None,overview_candidates=False):
    config=json.loads((source_config or ROOT/f'catalog/routes/sources/{state}.json').read_text());folder=ROOT/f'research/routes/{state}/hr-sources';folder.mkdir(parents=True,exist_ok=True)
    if config.get('state')!=state:raise ValueError('Source configuration state mismatch')
    catalog=build();state_rivers=[r for r in catalog['rivers'] if r['state']==state]
    streams={rid:s for s in config['streams'] for rid in s['riverIds']}
    known={r['id'] for r in state_rivers}
    if not streams or set(streams)-known:
        raise ValueError('Route source configuration must name existing rivers in this state')
    rivers=[r for r in state_rivers if r['id'] in streams]
    project=Transformer.from_crs(4326,config['projectedCrs'],always_xy=True).transform;unproject=Transformer.from_crs(config['projectedCrs'],4326,always_xy=True).transform
    def fetch(r):
        try:return r,(local_extract(r,streams[r['id']],folder,gpkg_dir,config['archiveManifest']) if gpkg_dir else download(r,streams[r['id']],folder,refresh)),None
        except Exception as e:return r,None,str(e)
    candidates=[];rows=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for river,result,error in pool.map(fetch,rivers):
            if result:
                path,payload=result;digest=hashlib.sha256(path.read_bytes()).hexdigest();snapshot=folder/(river['id']+'-'+digest[:16]+'.json')
                if not snapshot.exists():snapshot.write_bytes(path.read_bytes())
                edges,adj=network(payload,project)
            for s in river['sections']:
                row={'riverId':river['id'],'sectionId':s['id'],'issues':[]}
                if not s.get('mapReleased'):row.update(issues=['access-map-withheld'],detail=s.get('accessReview') or s.get('mapPendingReason'))
                elif s.get('routeReview'):row.update(issues=['route-review-required'],detail=s['routeReview'])
                elif s.get('mapPrecision')!='exact' and not overview_candidates:row.update(issues=['approximate-access-points'],detail='Stage an overview candidate separately; an area marker does not verify a landing connection.')
                elif error:row.update(issues=['source-unavailable'],detail=error)
                else:
                    try:
                        overview=overview_candidates and s.get('mapPrecision')!='exact'
                        geometry,direction=directed_route(edges,adj,s,project,unproject,overview=overview)
                        record={'version':1,'state':state,'riverId':river['id'],'sectionId':s['id'],'status':'candidate','source':{'name':'USGS National Hydrography Dataset — High Resolution','url':payload['sourceUrl'],'checkedOn':payload['checkedOn'],'streamId':streams[river['id']]['riverName'],'evidenceFile':str(snapshot.relative_to(ROOT)),'sha256':digest},'putIn':{'name':s['putIn'],**s['putInCoords']},'takeOut':{'name':s['takeOut'],**s['takeOutCoords']},'catalogMiles':s['miles'],'geometry':geometry,'direction':direction,'features':{'display':False,'landOverlay':False,'distanceEstimate':False,'remainingTime':False},'note':'Approximate mapped river centerline, not a recommended navigation channel. Channels, hazards and conditions change. Does not enable GPS time remaining or replace planning mileage.'}
                        if s.get('mapPrecision')!='exact':record['scope']='river-course-overview'
                        metrics,issues=geometry_checks(record)
                        if s.get('distanceReview'):issues.append('catalog-distance-under-review')
                        record['checks']={'metrics':metrics,'issues':issues};candidates.append(record);row.update(record['checks'])
                    except (ValueError,KeyError,TypeError) as exc:row.update(issues=['source-needs-review'],detail=str(exc))
                rows.append(row)
            print(river['id'],error or 'source checked',flush=True)
    for name,key,new_rows in [('hr-candidates.json','routes',candidates),('hr-review-queue.json','sections',rows)]:
        output=folder.parent/name
        # A focused river run must not erase research for the rest of the state.
        # Replace all selected-river rows, including candidates that now fail.
        preserved=[]
        if output.exists() and set(streams)!=known:
            previous=json.loads(output.read_text())
            if previous.get('state')!=state:raise ValueError('Existing route research state mismatch')
            preserved=[row for row in previous[key] if row['riverId'] not in streams]
        output.write_text(json.dumps({'version':1,'state':state,key:preserved+new_rows},indent=2)+'\n')
    print('High-resolution candidates',len(candidates),'passing checks',sum(not r['checks']['issues'] for r in candidates))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--state',required=True);p.add_argument('--refresh',action='store_true');p.add_argument('--gpkg-dir',type=Path);p.add_argument('--source-config',type=Path);p.add_argument('--overview-candidates',action='store_true');a=p.parse_args();run(a.state,a.refresh,a.gpkg_dir,a.source_config,a.overview_candidates)
