#!/usr/bin/env python3
"""Measure generalized candidate offsets from finer USGS data; never approve.
python tools/compare_route_resolution.py --state WY
Requires development-only shapely and pyproj. Network proximity does not prove a
navigable channel. Keep review separate and retain immutable comparison evidence.
"""
import argparse,hashlib,json,sys
from pathlib import Path
from shapely.geometry import LineString
from shapely.ops import transform,unary_union
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[1]
def run(state):
    folder=ROOT/f'research/routes/{state}';config=json.loads((ROOT/f'catalog/routes/sources/{state}.json').read_text())
    project=Transformer.from_crs(4326,config['projectedCrs'],always_xy=True).transform;cache={};rows=[]
    for r in json.loads((folder/'candidates.json').read_text())['routes']:
        if r['checks']['issues']:continue
        rid=r['riverId']
        if rid not in cache:
            source=folder/'hr-sources'/(rid+'.json');raw=source.read_bytes();sha=hashlib.sha256(raw).hexdigest();snapshot=source.with_name(rid+'-'+sha[:16]+'.json')
            if not snapshot.exists():snapshot.write_bytes(raw)
            data=json.loads(raw)
            network=unary_union([transform(project,LineString(p)) for f in data['features'] if f['attributes']['flowdir']==1 for p in f['geometry']['paths']])
            cache[rid]=(network,str(snapshot.relative_to(ROOT)),sha)
        network,evidence,sha=cache[rid];line=transform(project,LineString(r['geometry']['coordinates']));n=max(2,int(line.length/25)+1)
        offsets=sorted(line.interpolate(i/n,normalized=True).distance(network) for i in range(n+1))
        rows.append({'riverId':rid,'sectionId':r['sectionId'],'geometrySha256':hashlib.sha256(json.dumps(r['geometry'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),'highResolutionEvidenceFile':evidence,'highResolutionSha256':sha,'maxOffset':round(max(offsets),1),'p95Offset':round(offsets[int(.95*n)],1)})
    result={'version':1,'state':state,'sampleSpacingMeters':25,'method':'Generalized candidate sampled at no more than 25 m intervals against the official high-resolution network. Proximity checks display accuracy only, not navigability or choice of channel.','routes':rows}
    raw=(json.dumps(result,indent=2)+'\n').encode();path=folder/'resolution-comparison.json';path.write_bytes(raw)
    immutable=folder/('resolution-comparison-'+hashlib.sha256(raw).hexdigest()[:16]+'.json');immutable.write_bytes(raw)
    print(str(immutable.relative_to(ROOT)),len(rows),'comparisons')
    return immutable
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--state',required=True);run(p.parse_args().state)
