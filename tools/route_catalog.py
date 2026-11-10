"""State-independent route validation and publication; standard library only.
Passing geometry checks is necessary, but does not grant review or permissions.
"""
import hashlib,json,math,re
from datetime import date
from pathlib import Path
try:
    from tools.agency_courses import METHOD as AGENCY_COURSE, valid_direction as valid_agency_direction, validate_agency_course, nearest_position, trim_chain
except ModuleNotFoundError:
    from agency_courses import METHOD as AGENCY_COURSE, valid_direction as valid_agency_direction, validate_agency_course, nearest_position, trim_chain
SLUG=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
FEATURES={'display','landOverlay','distanceEstimate','remainingTime'}
OVERVIEW='river-course-overview'
OVERVIEW_MAX_OFFSET_METERS=1000
OVERVIEW_MAX_REVIEWED_SEGMENT_METERS=2000

def review_signature(record):
    """Bind an overview decision to its geometry, source and access snapshots."""
    fields=('geometry','direction','source','putIn','takeOut','catalogMiles')
    if 'sourceSegmentReview' in record:
        fields += ('sourceSegmentReview',)
    if 'distanceDiscrepancyReview' in record:
        fields += ('distanceDiscrepancyReview',)
    if 'courseAnchors' in record:
        fields += ('courseAnchors',)
    return hashlib.sha256(json.dumps({k:record[k] for k in fields},sort_keys=True,separators=(',',':')).encode()).hexdigest()

def reviewed_distance_discrepancy(record,section,root):
    """Display a checked source course while disputed planning mileage stays held.

    This is never a distance correction or a navigation/timing approval. Require
    the original downstream source vertices and saved imagery, not just a
    re-signed geometry or a larger numerical tolerance.
    """
    review=record.get('distanceDiscrepancyReview')
    if review is None:return False
    require(record.get('scope')==OVERVIEW and record.get('direction',{}).get('method')=='usgs-flow-directed-network',
            'Distance discrepancy requires a source-reconstructed downstream overview')
    require(isinstance(review,dict) and isinstance(section.get('distanceReview'),str) and bool(section['distanceReview'].strip())
            and review.get('planningDistanceReview')==section['distanceReview'],
            'Planning distance review changed; re-review course')
    require(record.get('features')==dict(display=True,landOverlay=False,distanceEstimate=False,remainingTime=False),
            'Disputed planning distance permits display only')
    require(isinstance(review.get('note'),str) and review['note'].strip(),'Distance discrepancy needs a review explanation')
    imagery=review.get('imageryEvidence')
    require(isinstance(imagery,list) and imagery,'Distance discrepancy needs saved imagery review')
    for item in imagery:
        require(isinstance(item,dict),'Invalid distance review imagery')
        path=safe_file(root,item.get('file'),'research')
        require(path.suffix.lower() in ('.png','.jpg','.jpeg','.webp'),'Distance review evidence must be imagery')
        require(hashlib.sha256(path.read_bytes()).hexdigest()==item.get('sha256'),'Distance review imagery changed; re-review required')
    reconstruct_directed_source(record,root)
    return True

def reconstruct_directed_source(record,root):
    """Require original source vertices, including trimmed endpoint features."""
    payload=json.loads(safe_file(root,record['source']['evidenceFile'],'research').read_text())
    require(not payload.get('error') and not payload.get('exceededTransferLimit'),'Incomplete downstream source evidence')
    features={str(f['attributes']['permanent_identifier']):f for f in payload['features']}
    parts=[features[k]['geometry']['paths'][0] for k in record['direction']['featureIds']]
    chain=[]
    for part in parts:
        require(len(part)>=2 and all(len(p)==2 and all(finite(v) for v in p) for p in part),'Invalid downstream source line')
        if chain:require(chain[-1]==part[0],'Source reconstruction cannot invent connectors')
        chain.extend(part if not chain else part[1:])
    coords=record['geometry']['coordinates']
    clip={side:nearest_position(chain,dict(lon=p[0],lat=p[1])) for side,p in [('start',coords[0]),('end',coords[-1])]}
    require(clip['start']['segment']<len(parts[0])-1 and clip['end']['segment']>=len(chain)-len(parts[-1]),
            'Downstream source trim omits a reviewed endpoint feature')
    expected=[]
    # A projected trim can land within sub-millimetre rounding of an existing
    # source vertex. Match the importer's duplicate removal, not a new connector.
    for point in trim_chain(chain,clip)['coordinates']:
        if not expected or distance(expected[-1],point)>.001:expected.append(point)
    require(len(coords)==len(expected) and all(distance(a,b)<.1 for a,b in zip(coords,expected)),
            'Overview geometry differs from original downstream source vertices')

def validate_course_anchors(record,root):
    anchors=record.get('courseAnchors')
    if anchors is None:return
    require(record.get('scope')==OVERVIEW and record.get('direction',{}).get('method')=='usgs-flow-directed-network',
            'Course anchors are limited to downstream river overviews')
    require(isinstance(anchors,dict) and anchors and set(anchors)<={'putIn','takeOut'},'Invalid course anchors')
    payload=json.loads(safe_file(root,record['source']['evidenceFile'],'research').read_text())
    require(payload.get('queryPolicy')=='named-and-unnamed-flowlines-v1','Course anchors require complete named and unnamed source coverage')
    ids=record['direction']['featureIds']
    for side,row in anchors.items():
        require(isinstance(row,dict) and row.get('featureId')==ids[0 if side=='putIn' else -1],
                'Course anchor differs from its endpoint source feature')
        require(isinstance(row.get('reason'),str) and row['reason'].strip(),'Course anchor needs a review reason')
        imagery=row.get('imageryEvidence')
        require(isinstance(imagery,list) and imagery,'Course anchor needs saved imagery review')
        for item in imagery:
            require(isinstance(item,dict),'Invalid course anchor evidence')
            path=safe_file(root,item.get('file'),'research')
            require(path.suffix.lower() in ('.png','.jpg','.jpeg','.webp'),'Course anchor evidence must be imagery')
            require(hashlib.sha256(path.read_bytes()).hexdigest()==item.get('sha256'),'Course anchor imagery changed; re-review required')
    require(not any(record.get('features',{}).get(k) for k in ('landOverlay','distanceEstimate','remainingTime')),
            'Course anchors permit river display only')
    reconstruct_directed_source(record,root)

def reviewed_source_segments(record,root):
    """A long original agency segment can be real straight water, not a gap.

    This exception requires source reconstruction elsewhere in validate(), plus
    explicit imagery review of every long segment. Never interpolate vertices
    to evade the ordinary gap check or extend this to navigation routes.
    """
    rows=record.get('sourceSegmentReview')
    if rows is None:return []
    require(record.get('scope')==OVERVIEW and record.get('direction',{}).get('method')==AGENCY_COURSE,
            'Long segment review requires a source-reconstructed agency overview')
    coords=record['geometry']['coordinates']
    lengths=[distance(a,b) for a,b in zip(coords,coords[1:])]
    require(all(.001<d<=OVERVIEW_MAX_REVIEWED_SEGMENT_METERS for d in lengths),
            'Long segment review cannot accept duplicates or segments beyond 2000 metres')
    expected=[i for i,d in enumerate(lengths) if d>1000]
    require(isinstance(rows,list) and bool(expected) and len(rows)==len(expected),
            'Every long source segment needs exactly one review')
    indices=[]
    for row in rows:
        require(isinstance(row,dict) and type(row.get('segment')) is int,'Invalid long source segment index')
        indices.append(row['segment'])
        require(isinstance(row.get('note'),str) and row['note'].strip(),'Long source segment needs an imagery verdict')
        evidence=row.get('imageryEvidence')
        require(isinstance(evidence,list) and evidence,'Long source segment needs saved imagery evidence')
        for item in evidence:
            require(isinstance(item,dict),'Invalid long source segment evidence')
            path=safe_file(root,item.get('file'),'research')
            require(path.suffix.lower() in ('.png','.jpg','.jpeg','.webp'),'Long source segment evidence must be imagery')
            require(hashlib.sha256(path.read_bytes()).hexdigest()==item.get('sha256'),
                    'Long source segment imagery changed; re-review required')
    require(sorted(indices)==expected,'Long source segment reviews do not match geometry')
    return expected

def validate_overview(record,section,metrics,issues,root):
    review=record.get('overviewReview',{})
    require(review.get('signature')==review_signature(record),'River-course overview changed; re-review required')
    accepted=review.get('acceptedIssues',{})
    allowed={'endpoint-offset-over-100m','mileage-difference-over-5-percent'}
    if reviewed_source_segments(record,root):allowed.add('route-gap-or-duplicate-vertex')
    require(set(accepted)==set(issues) and set(issues)<=allowed,'Overview has unresolved geometry checks')
    require(all(isinstance(v,str) and v.strip() for v in accepted.values()),'Overview exceptions need reasons')
    discrepancy=reviewed_distance_discrepancy(record,section,root)
    require(max(metrics['endpointOffsetsMeters'])<=OVERVIEW_MAX_OFFSET_METERS and (metrics['mileageDifferencePercent']<=20 or discrepancy),'Overview extends beyond reviewed access vicinity or mileage bounds')
    require(not section.get('distanceReview') or discrepancy,'Overview needs an explicit planning distance review')
    require(review.get('routeReview')==section.get('routeReview'),'Overview barrier review changed')
    require(isinstance(review.get('note'),str) and review['note'].strip(),'Overview limitations required')
    connections=review.get('connections',{})
    require(set(connections)=={'putIn','takeOut'},'Overview must describe both access connections')
    for connection in connections.values():
        require(connection.get('status')=='not-mapped' and isinstance(connection.get('note'),str) and connection['note'].strip(),'Overview must not claim an exact landing connection')
    require(not record['features']['landOverlay'],'Overview cannot imply a reviewed land-access corridor')

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
    measured = (d.get('method')=='agency-measures-increase-upstream'
                and all(finite(d.get(k)) for k in ('putInMeasure','takeOutMeasure'))
                and d['putInMeasure']>d['takeOutMeasure'])
    downstream = (d.get('method')=='usgs-downstream-mainstem'
                  and all(finite(d.get(k)) for k in ('putInChainageMeters','takeOutChainageMeters'))
                  and 0<=d['putInChainageMeters']<d['takeOutChainageMeters']
                  and isinstance(d.get('featureIds'),list) and bool(d['featureIds'])
                  and all(isinstance(v,str) and v.isdigit() for v in d['featureIds']))
    directed = (d.get('method')=='usgs-flow-directed-network'
                and isinstance(d.get('featureIds'),list) and bool(d['featureIds'])
                and all(isinstance(v,str) and bool(v) for v in d['featureIds'])
                and all(finite(d.get(k)) and d[k]>=0 for k in ('putInOffsetMeters','takeOutOffsetMeters')))
    if not (measured or downstream or directed or valid_agency_direction(d)):
        issues.append('downstream-order-unconfirmed')
    return {'routeMiles':round(miles,4),'endpointOffsetsMeters':[round(v,1) for v in offsets],'mileageDifferencePercent':round(difference*100,2),'maxSegmentMeters':round(max(lengths),1),'vertices':len(c)},issues

def safe_file(root,path,prefix):
    require(isinstance(path,str) and path.startswith(prefix+'/') and '..' not in Path(path).parts,'Invalid evidence path')
    resolved=(root/path).resolve();require(root.resolve() in resolved.parents,'Evidence escapes project')
    require(resolved.is_file(),'Missing evidence file: '+path)
    return resolved

def validate(record,catalog,root):
    require(record.get('version')==1,'Invalid route version')
    require(record.get('scope','landing-to-landing') in ('landing-to-landing',OVERVIEW),'Invalid route scope')
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
    if record.get('direction',{}).get('method') == AGENCY_COURSE:
        validate_agency_course(record,section,json.loads(evidence.read_text()),root)
    if record.get('direction',{}).get('method')=='usgs-downstream-mainstem':
        require(source['url'].startswith('https://api.water.usgs.gov/nldi/linked-data/comid/') and '/navigation/DM/flowlines?' in source['url'],'Downstream route requires USGS mainstem evidence')
        payload=json.loads(evidence.read_text())
        available={str(f.get('properties',{}).get('nhdplus_comid')):f for f in payload.get('features',[])}
        ids=record['direction']['featureIds']
        require(len(ids)==len(set(ids)), 'Route contains a network loop')
        require(set(ids)<=available.keys(),'Route feature missing from source evidence')
        previous=None
        for key in ids:
            geometry=available[key].get('geometry',{})
            require(geometry.get('type')=='LineString','Invalid mainstem source geometry')
            line=geometry['coordinates']
            if previous is not None:require(distance(previous,line[0])<1,'Mainstem source path is disconnected or reversed')
            previous=line[-1]
    if record.get('direction',{}).get('method')=='usgs-flow-directed-network':
        require(source['url']=='https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/6' or source['url'].startswith('https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/HU4/GPKG/'),'Directed route requires USGS high-resolution source')
        payload=json.loads(evidence.read_text());features={str(f['attributes']['permanent_identifier']):f for f in payload.get('features',[])}
        ids=record['direction']['featureIds'];require(len(ids)==len(set(ids)),'Route contains a network loop')
        previous=None
        for key in ids:
            require(key in features,'Route feature missing from source evidence');f=features[key]
            require(f['attributes']['flowdir']==1 and len(f['geometry']['paths'])==1,'Flow direction is not established')
            line=f['geometry']['paths'][0]
            if previous is not None:require(distance(previous,line[0])<1,'Directed source path is disconnected')
            previous=line[-1]
        direction=record['direction']
        station_keys=('putInSourceStationMeters','takeOutSourceStationMeters')
        if any(k in direction for k in station_keys):
            require(all(finite(direction.get(k)) and direction[k]>=0 for k in station_keys),'Invalid source-line station distances')
            start_station,end_station=(direction[k] for k in station_keys)
        else:
            # Legacy imports named along-line stations OffsetMeters. Preserve their
            # meaning; new imports record perpendicular offsets separately.
            start_station,end_station=direction['putInOffsetMeters'],direction['takeOutOffsetMeters']
        if len(ids)==1:require(start_station<end_station,'Single-feature route is reversed')
    flags=record.get('features',{})
    require(set(flags)==FEATURES and all(type(v) is bool for v in flags.values()),'Invalid route feature flags')
    # These are reserved, separately reviewed future capabilities; never enabled by map review.
    require(not flags['remainingTime'] and not flags['distanceEstimate'],'GPS ETA and calculator distance adoption are deferred')
    require(not flags['landOverlay'] or flags['display'],'Land corridor requires route display')
    metrics,issues=geometry_checks(record)
    validate_course_anchors(record,root)
    require(record.get('checks',{}).get('metrics')==metrics,'Route metrics stale; rebuild candidate')
    require(isinstance(record['checks'].get('issues'),list),'Route check issues required')
    if record['status']!='reviewed':
        require(not any(flags.values()),'Unreviewed route cannot enable features');return section,metrics
    if record.get('direction',{}).get('method')=='usgs-downstream-mainstem':
        cross=record.get('resolutionReview',{})
        comparison=safe_file(root,cross.get('file'),'research')
        require(hashlib.sha256(comparison.read_bytes()).hexdigest()==cross.get('sha256'),'Resolution review changed; re-review route')
        payload=json.loads(comparison.read_text())
        require(payload.get('sampleSpacingMeters')==25,'Invalid resolution review sampling')
        match=next((r for r in payload['routes'] if r['riverId']==record['riverId'] and r['sectionId']==record['sectionId']),None)
        require(match is not None and finite(match.get('maxOffset')) and match['maxOffset']<=75,'Generalized source needs finer geometry')
        geometry_hash=hashlib.sha256(json.dumps(record['geometry'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
        require(match.get('geometrySha256')==geometry_hash,'Resolution review belongs to a different route')
        fine=safe_file(root,match.get('highResolutionEvidenceFile'),'research')
        require(hashlib.sha256(fine.read_bytes()).hexdigest()==match.get('highResolutionSha256'),'High-resolution comparison evidence changed')
    overview=record.get('scope')==OVERVIEW
    if overview:
        require(record['checks']['issues']==issues,'Overview check issues stale')
        validate_overview(record,section,metrics,issues,root)
    else:
        require('distanceDiscrepancyReview' not in record,'Distance discrepancy is for river-course overviews only')
        require(not issues and not record['checks']['issues'],'Reviewed route has unresolved checks')
        require(section.get('mapPrecision')=='exact','Reviewed route needs eligible access points')
        require(not section.get('routeReview'), 'Reviewed route has an unresolved route/portage review')
    require(section.get('mapPilot') and (not section.get('distanceReview') or overview) and not section.get('accessReview'),'Reviewed route needs eligible access points')
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
            if record.get('scope')==OVERVIEW:
                public.update(scope=OVERVIEW,overview={k:record['overviewReview'][k] for k in ('note','connections','routeReview')})
                if 'sourceSegmentReview' in record:
                    public['overview']['longSourceSegments']=[r['segment'] for r in record['sourceSegmentReview']]
                if 'distanceDiscrepancyReview' in record:
                    public['overview']['planningDistanceReview']=record['distanceDiscrepancyReview']['planningDistanceReview']
            public['land']=None
            if record['features']['landOverlay']:
                land=record['landEvidence'];public.update(land=json.loads((root/land['file']).read_text()),corridorMeters=land['corridorMeters'],landCheckedOn=land['checkedOn'],landSourceUrl=land['url'],landNote='Only portions of trust-land polygons within 150 metres of the approximate river line are shown. Clipped display edges are not property boundaries or proof of river access.')
            outputs['public/'+asset]=json.dumps(public,separators=(',',':'))+'\n'
            entries.append({'riverId':key[0],'sectionId':key[1],'state':state,'file':asset,'features':record['features']})
            if record.get('scope')==OVERVIEW:entries[-1]['scope']=OVERVIEW
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
