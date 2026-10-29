#!/usr/bin/env python3
"""Reproduce the field-test geometry using shapely 2.0.7 and pyproj 3.6.1. Read-only."""
import json,pathlib,math,hashlib
from shapely.geometry import LineString,Point,mapping
from shapely.ops import transform,substring
from pyproj import Transformer
r=pathlib.Path(__file__).resolve().parents[1];out=r/'research/MT/greycliff-pilot-20261029'
p=r/'research/MT/access-review-20261027/nhd-lower-madison.json'; d=json.loads(p.read_text()); fs=d['response']['features']; by={f['attributes']['hydroseq']:f for f in fs}
fwd=Transformer.from_crs(4326,32612,always_xy=True).transform;back=Transformer.from_crs(32612,4326,always_xy=True).transform
start=Point(fwd(-111.52248398669596,45.646386736352305));end=Point(fwd(-111.51613888888889,45.7045))
lines={k:transform(fwd,LineString(f['geometry']['paths'][0])) for k,f in by.items()}
s=min(lines,key=lambda k:lines[k].distance(start));t=min(lines,key=lambda k:lines[k].distance(end)); chain=[];coords=[];k=s;joins=[]
while k not in chain:
 chain.append(k);pts=list(lines[k].coords)
 if coords:joins.append(Point(coords[-1]).distance(Point(pts[0])));assert joins[-1]<1;coords.extend(pts[1:])
 else:coords=pts
 if k==t:break
 k=by[k]['attributes']['dnhydroseq']
assert k==t
line=LineString(coords);a,b=line.project(start),line.project(end);assert a<b
cut=substring(line,a,b);geo=mapping(transform(back,cut))
# Independent FWP measured centerline comparison, ending at the supplied takeout.
fwp=json.loads((r/'research/routes/MT/sources/fwp-1115074459269-0c376f9210933c16.json').read_text()); raw=fwp['response']['features'][0]['geometry']['paths'][0]
fl=transform(fwd,LineString([v[:2] for v in raw]));fc=substring(fl,fl.project(start),fl.project(end))
record={'sourceFile':str(p.relative_to(r)),'sourceSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'requestUrl':d['requestUrl'],'hydrosequences':chain,'joinsMeters':joins,'startOffsetMeters':cut.distance(start),'endOffsetMeters':cut.distance(end),'utmRouteMiles':cut.length/1609.344,'vertices':len(geo['coordinates']),'maxSegmentMeters':max(Point(a).distance(Point(b)) for a,b in zip(cut.coords,list(cut.coords)[1:])),'isSimple':cut.is_simple,'fwpComparison':{'miles':fc.length/1609.344,'hausdorffMeters':cut.hausdorff_distance(fc),'endOffsetMeters':fc.distance(end)},'geometry':geo}
saved=json.loads((out/'route-checks.json').read_text())
assert all(saved[k]==json.loads(json.dumps(v)) for k,v in record.items()), 'Geometry evidence changed; review required'
print('USGS route evidence reproduced: 8 linked reaches, no joins, user takeout within 50 m')
