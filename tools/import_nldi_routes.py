#!/usr/bin/env python3
"""Stage USGS downstream-mainstem lines; never approves routes or changes miles.

python tools/import_nldi_routes.py --state WY
Config and archived source URLs are explicit so the adapter can be reused by state.
Development dependencies match import_river_routes.py: shapely, pyproj.
"""
import argparse, hashlib, json, sys
from pathlib import Path
from shapely.geometry import LineString, Point, mapping
from shapely.ops import transform, substring
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.build_catalog import build
from tools.route_catalog import distance, geometry_checks


def source_chains(payload):
    """Preserve agency direction. Split gaps; never draw a connector across them."""
    chains=[];coordinates=[];ids=[]
    for feature in payload.get('features',[]):
        geometry=feature.get('geometry',{})
        if geometry.get('type')!='LineString':
            raise ValueError('Mainstem source must contain LineStrings')
        points=geometry.get('coordinates',[])
        if len(points)<2:raise ValueError('Empty source flowline')
        identity=str(feature.get('properties',{}).get('nhdplus_comid',''))
        if not identity.isdigit():raise ValueError('Source flowline has no COMID')
        if coordinates and distance(coordinates[-1],points[0])>1:
            chains.append((coordinates,ids));coordinates=[];ids=[]
        ids.append(identity)
        for p in points:
            if not coordinates or distance(coordinates[-1],p)>.001:coordinates.append(p[:2])
    if coordinates:chains.append((coordinates,ids))
    if not chains:raise ValueError('Empty mainstem response')
    return chains


def clip_route(chains, section, project, unproject):
    points=[Point(project(s['lon'],s['lat'])) for s in [section['putInCoords'],section['takeOutCoords']]]
    choices=[]
    for coordinates,ids in chains:
        line=transform(project,LineString(coordinates))
        offsets=[line.distance(p) for p in points]
        if max(offsets)>100:continue
        a,b=[line.project(p) for p in points]
        if b<=a:continue
        cut=substring(line,a,b)
        if cut.geom_type!='LineString' or not cut.is_simple:continue
        choices.append((mapping(transform(unproject,cut)),a,b,ids))
    if len(choices)!=1:raise ValueError('No unique connected downstream line within 100 m of both endpoints')
    return choices[0]


def run(state,root=ROOT):
    config=json.loads((root/f'catalog/routes/sources/{state}.json').read_text())
    if config.get('state')!=state or config.get('adapter')!='usgs-nldi-downstream':raise ValueError('Unsupported source configuration')
    folder=root/f'research/routes/{state}';(folder/'sources').mkdir(parents=True,exist_ok=True)
    project=Transformer.from_crs(4326,config['projectedCrs'],always_xy=True).transform
    unproject=Transformer.from_crs(config['projectedCrs'],4326,always_xy=True).transform
    by_river={};failures={}
    for stream in config['streams']:
        try:
            path=root/stream['evidenceFile'];raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
            if digest!=stream['sha256']:raise ValueError('Configured source snapshot changed')
            chains=source_chains(json.loads(raw))
            snapshot=folder/'sources'/('nldi-'+stream['streamId']+'-'+digest[:16]+'.json')
            if not snapshot.exists():snapshot.write_bytes(raw)
            for rid in stream['riverIds']:by_river[rid]=(stream,snapshot,digest,chains)
        except (ValueError,KeyError,OSError) as exc:
            for rid in stream['riverIds']:failures[rid]=str(exc)
    candidates=[];rows=[]
    for river in build(root)['rivers']:
        if river['state']!=state:continue
        for section in river['sections']:
            row={'riverId':river['id'],'sectionId':section['id'],'issues':[]}
            if not section.get('mapReleased'):
                row.update(issues=['access-map-withheld'],detail=section.get('accessReview') or section.get('mapPendingReason') or section.get('mapReleaseNote'));rows.append(row);continue
            if section.get('mapPrecision')!='exact':
                row.update(issues=['approximate-access-points'],detail='Keep facility-area markers; a dotted route needs reviewed landings.');rows.append(row);continue
            if river['id'] not in by_river:
                row.update(issues=['source-unavailable'],detail=failures.get(river['id'],'Source not configured'));rows.append(row);continue
            stream,path,digest,chains=by_river[river['id']]
            try:
                geometry,a,b,ids=clip_route(chains,section,project,unproject)
                record={'version':1,'state':state,'riverId':river['id'],'sectionId':section['id'],'status':'candidate',
                    'source':{'name':'USGS NLDI / NHDPlus V2 downstream mainstem','url':stream['url'],'checkedOn':stream['checkedOn'],'streamId':stream['streamId'],'evidenceFile':str(path.relative_to(root)),'sha256':digest},
                    'putIn':{'name':section['putIn'],**section['putInCoords']},'takeOut':{'name':section['takeOut'],**section['takeOutCoords']},'catalogMiles':section['miles'],'geometry':geometry,
                    'direction':{'method':'usgs-downstream-mainstem','putInChainageMeters':a,'takeOutChainageMeters':b,'featureIds':ids},
                    'features':{'display':False,'landOverlay':False,'distanceEstimate':False,'remainingTime':False},
                    'note':'Approximate USGS mainstem centerline. River bends and side channels may differ from this generalized line. Not a recommended navigation channel or surveyed landing-to-landing distance.'}
                metrics,issues=geometry_checks(record)
                if section.get('distanceReview'):issues.append('catalog-distance-under-review')
                record['checks']={'metrics':metrics,'issues':sorted(set(issues))};candidates.append(record);row.update(record['checks'])
            except (ValueError,TypeError,KeyError) as exc:row.update(issues=['source-needs-review'],detail=str(exc))
            rows.append(row)
    (folder/'candidates.json').write_text(json.dumps({'version':1,'state':state,'routes':candidates},indent=2)+'\n')
    (folder/'review-queue.json').write_text(json.dumps({'version':1,'state':state,'sourceFailures':failures,'sections':rows},indent=2)+'\n')
    print(json.dumps({'sections':len(rows),'candidates':len(candidates),'passingChecks':sum(not r['checks']['issues'] for r in candidates),'sourceFailures':failures}))
    return candidates,rows

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--state',required=True);args=parser.parse_args();run(args.state)
