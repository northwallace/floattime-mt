"""State-independent route validation and publication; standard library only.
Passing geometry checks is necessary, but does not grant review or permissions.
"""
import hashlib,json,math,re
from datetime import date
from pathlib import Path
SLUG=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
FEATURES={'display','landOverlay','distanceEstimate','remainingTime'}

def require(ok,message):
    if not ok: raise ValueError(message)

def finite(v): return type(v) in (int,float) and math.isfinite(v)
def distance(a,b):
    x,y=math.radians(a[1]),math.radians(b[1]);dl=math.radians(b[0]-a[0])
    return 12742017.6*math.asin(min(1,math.sqrt(math.sin((y-x)/2)**2+math.cos(x)*math.cos(y)*math.sin(dl/2)**2)))

def geometry_checks(record):
    geometry=record.get('geometry',{});c=geometry.get('coordinates')
    require(geometry.get('type')=='LineString' and isinstance(c,(list,tuple)) and 2<=len(c)<=20000,'Invalid route geometry')
    require(all(isinstance(p,(list,tuple)) and len(p)==2 and all(finite(v) for v in p) and abs(p[0])<=180 and abs(p[1])<=85 for p in c),'Invalid route coordinates')
    lengths=[distance(a,b) for a,b in zip(c,c[1:])]
    miles=sum(lengths)/1609.344
    require(finite(record.get('catalogMiles')) and record['catalogMiles']>0,'Invalid catalog mileage')
    offsets=[]
    for field,end in [('putIn',c[0]),('takeOut',c[-1])]:
        p=record.get(field,{})
        require(finite(p.get('lat')) and finite(p.get('lon')),'Invalid endpoint snapshot')
        offsets.append(distance(end,[p['lon'],p['lat']]))
    difference=abs(miles-record['catalogMiles'])/record['catalogMiles']
    issues=[]
    if any(d<=.001 or d>1000 for d in lengths): issues.append('route-gap-or-duplicate-vertex')
    if max(offsets)>100: issues.append('endpoint-offset-over-100m')
    if difference>.05: issues.append('mileage-difference-over-5-percent')
    d=record.get('direction',{})
    if d.get('method')!='agency-measures-increase-upstream' or not all(finite(d.get(k)) for k in ('putInMeasure','takeOutMeasure')) or d['putInMeasure']<=d['takeOutMeasure']:
        issues.append('downstream-order-unconfirmed')
    return {'routeMiles':round(miles,4),'endpointOffsetsMeters':[round(v,1) for v in offsets],'mileageDifferencePercent':round(difference*100,2),'maxSegmentMeters':round(max(lengths),1),'vertices':len(c)},issues

def safe_file(root,path,prefix):
    require(isinstance(path,str) and path.startswith(prefix+'/') and '..' not in Path(path).parts,'Invalid evidence path')
    resolved=(root/path).resolve();require(root.resolve() in resolved.parents,'Evidence escapes project')
    require(resolved.is_file(),'Missing evidence file: '+path)
    return resolved

def validate(record,catalog,root):
    require(record.get('version')==1,'Invalid route version')
    require(record.get('status') in ('candidate','reviewed','rejected'),'Invalid route status')
    river=next((r for r in catalog['rivers'] if r['id']==record.get('riverId')),None)
    require(river is not None and river['state']==record.get('state'),'Route river/state mismatch')
    section=next((s for s in river['sections'] if s['id']==record.get('sectionId')),None)
    require(section is not None,'Unknown route section')
    source=record.get('source',{})
    for key in ('name','url','checkedOn','streamId','evidenceFile','sha256'):
        require(isinstance(source.get(key),str) and source[key].strip(),'Missing route source '+key)
    require(source['url'].startswith('https://'),'Route source must be HTTPS')
    require(date.fromisoformat(source['checkedOn'])<=date.today(),'Future route source date')
    evidence=safe_file(root,source['evidenceFile'],'research')
    require(hashlib.sha256(evidence.read_bytes()).hexdigest()==source['sha256'],'Source evidence changed; re-review route')
    flags=record.get('features',{})
    require(set(flags)==FEATURES and all(type(v) is bool for v in flags.values()),'Invalid route feature flags')
    # These are reserved, separately reviewed future capabilities; never enabled by map review.
    require(not flags['remainingTime'] and not flags['distanceEstimate'],'GPS ETA and calculator distance adoption are deferred')
    require(not flags['landOverlay'] or flags['display'],'Land corridor requires route display')
    metrics,issues=geometry_checks(record)
    require(record.get('checks',{}).get('metrics')==metrics,'Route metrics stale; rebuild candidate')
    require(isinstance(record['checks'].get('issues'),list),'Route check issues required')
    if record['status']!='reviewed':
        require(not any(flags.values()),'Unreviewed route cannot enable features');return section,metrics
    require(not issues and not record['checks']['issues'],'Reviewed route has unresolved checks')
    require(section.get('mapPilot') and section.get('mapPrecision')=='exact' and not section.get('distanceReview') and not section.get('accessReview'),'Reviewed route needs eligible access points')
    require(record['catalogMiles']==section['miles'],'Published section mileage changed; re-review route')
    for field in ('putIn','takeOut'):
        p=record[field]
        require(p.get('name')==section[field] and all(p[k]==section[field+'Coords'][k] for k in ('lat','lon')),'Endpoint changed; re-review route')
    review=record.get('review',{})
    for key in ('checkedOn','reviewer','note'):
        require(isinstance(review.get(key),str) and review[key].strip(),'Missing route review '+key)
    require(date.fromisoformat(review['checkedOn'])<=date.today(),'Future route review')
    require(record.get('note'),'Approximate route description required')
    if flags['landOverlay']:
        land=record.get('landEvidence',{})
        require(land.get('corridorMeters')==150 and land.get('url','').startswith('https://'),'Invalid land corridor provenance')
        require(date.fromisoformat(land['checkedOn'])<=date.today(),'Future land evidence')
        fp=safe_file(root,land.get('file'),'research')
        require(hashlib.sha256(fp.read_bytes()).hexdigest()==land.get('sha256'),'Land corridor changed; re-review')
        require(isinstance(land.get('inputs'),list) and land['inputs'],'Land source snapshots required')
        for source_input in land['inputs']:
            raw=safe_file(root,source_input.get('file'),'research')
            require(hashlib.sha256(raw.read_bytes()).hexdigest()==source_input.get('sha256'),'Land source evidence changed; re-review')
        payload=json.loads(fp.read_text())
        require(payload.get('type')=='FeatureCollection' and isinstance(payload.get('features'),list),'Invalid land overlay')
        for feature in payload['features']:
            require(feature.get('geometry',{}).get('type') in ('Polygon','MultiPolygon') and feature.get('properties',{}).get('mapAccess') in ('public','no','special'),'Invalid land feature')
        geometry_hash=hashlib.sha256(json.dumps(record['geometry'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
        require(land.get('routeSha256')==geometry_hash,'Land corridor belongs to an old route')
    return section,metrics

def build_outputs(root,catalog):
    index=root/'catalog/routes/index.json'
    if not index.exists(): return {}
    registry=json.loads(index.read_text());require(registry.get('version')==1 and isinstance(registry.get('states'),dict),'Invalid route registry')
    outputs={};entries=[];seen=set()
    for state,filename in sorted(registry['states'].items()):
        require(re.fullmatch('[A-Z]{2}',state) and filename==state+'.json','Invalid route state index')
        manifest=json.loads((index.parent/filename).read_text())
        require(manifest.get('version')==1 and manifest.get('state')==state,'Route state mismatch')
        for file in manifest['routes']:
            path=safe_file(root,'catalog/routes/'+file,'catalog/routes')
            record=json.loads(path.read_text());require(record.get('state')==state,'Route registered under wrong state')
            key=(record.get('riverId'),record.get('sectionId'));require(key not in seen,'Duplicate route section');seen.add(key)
            _,metrics=validate(record,catalog,root)
            if record['status']!='reviewed' or not record['features']['display']:continue
            asset='routes/'+key[0]+'--'+key[1]+'.json'
            public={k:record[k] for k in ('version','state','riverId','sectionId','status','putIn','takeOut','catalogMiles','geometry','features','note')}
            public.update(routeMiles=metrics['routeMiles'],sourceName=record['source']['name'],sourceUrl=record['source']['url'],checkedOn=record['review']['checkedOn'])
            public['land']=None
            if record['features']['landOverlay']:
                land=record['landEvidence'];public.update(land=json.loads((root/land['file']).read_text()),corridorMeters=land['corridorMeters'],landCheckedOn=land['checkedOn'],landSourceUrl=land['url'],landNote='Only portions of trust-land polygons within 150 metres of the approximate river line are shown. Clipped display edges are not property boundaries or proof of river access.')
            outputs['public/'+asset]=json.dumps(public,separators=(',',':'))+'\n'
            entries.append({'riverId':key[0],'sectionId':key[1],'state':state,'file':asset,'features':record['features']})
    outputs['public/routes/index.json']=json.dumps({'version':1,'routes':entries},indent=2)+'\n'
    return outputs

def write_or_check(root,catalog,check=False):
    outputs=build_outputs(root,catalog)
    for path,content in outputs.items():
        dest=root/path
        if check: require(dest.exists() and dest.read_text()==content,'Generated route assets stale: run python3 tools/build_catalog.py')
        else:
            dest.parent.mkdir(parents=True,exist_ok=True);temp=dest.with_suffix('.tmp');temp.write_text(content);temp.replace(dest)
    # Stale public geometry must not remain accessible after a route is withdrawn.
    for path in (root/'public/routes').glob('*.json'):
        if str(path.relative_to(root)) not in outputs:
            if check: raise ValueError('Stale public route asset: '+path.name)
            path.unlink()
    return outputs
