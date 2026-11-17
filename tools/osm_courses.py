"""Source fidelity for display-only courses from original OSM river ways.

OSM mapping order and a reviewed source selection describe a river overview;
they do not establish public access, a safe channel, distance or travel time.
Production validation uses only the standard library and saved source bytes.
"""
import hashlib,json,math
from pathlib import Path
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit, parse_qs
try:
    from tools.agency_courses import nearest_position, trim_chain
except ModuleNotFoundError:
    from agency_courses import nearest_position, trim_chain

METHOD = 'osm-original-river-way-order'
LICENSE = dict(name='ODbL 1.0', url='https://opendatacommons.org/licenses/odbl/1-0/',
               attribution='© OpenStreetMap contributors',
               attributionUrl='https://www.openstreetmap.org/copyright')


def require(ok, message):
    if not ok:raise ValueError(message)


def osm_source(raw):
    require(isinstance(raw, bytes) and len(raw)<=32_000_000, 'OSM snapshot is missing or too large')
    require(b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(), 'OSM snapshot cannot contain XML entities')
    try:root=ET.fromstring(raw)
    except ET.ParseError as error:raise ValueError('Invalid OSM source XML') from error
    require(root.tag=='osm' and root.get('version')=='0.6', 'OSM snapshot must use native API 0.6 format')
    nodes={};ways={}
    for element in root.findall('node'):
        key=element.get('id');require(key and key.isdigit() and key not in nodes, 'OSM node ID is invalid or duplicated')
        try:xy=[float(element.get('lon')),float(element.get('lat'))]
        except (ValueError,TypeError) as error:raise ValueError('Invalid OSM node coordinates') from error
        require(all(math.isfinite(v) for v in xy) and abs(xy[0])<=180 and abs(xy[1])<=85,'Invalid OSM node coordinates')
        nodes[key]=xy
    for element in root.findall('way'):
        tags={t.get('k'):t.get('v') for t in element.findall('tag')}
        if tags.get('waterway')!='river':continue
        key=element.get('id');require(key and key.isdigit() and key not in ways, 'OSM river way ID is invalid or duplicated')
        version=element.get('version');require(version and version.isdigit() and int(version)>0,'OSM way version missing')
        refs=[n.get('ref') for n in element.findall('nd')]
        require(len(refs)>=2 and all(n in nodes for n in refs), 'OSM river way has missing source nodes')
        ways[key]=dict(version=int(version),nodes=refs,tags=tags,timestamp=element.get('timestamp'))
    require(nodes and ways,'OSM snapshot contains no complete river ways')
    return nodes,ways


def source_chain(raw, parts):
    nodes,ways=osm_source(raw)
    require(isinstance(parts,list) and 1<=len(parts)<=1000,'OSM source parts required')
    chain=[];refs=[];seen=set()
    for part in parts:
        require(isinstance(part,dict) and set(part)=={'wayId','wayVersion','fromNodeIndex','toNodeIndex'},'Invalid OSM source part')
        key=part['wayId'];require(isinstance(key,str) and key in ways,'OSM source river way missing')
        way=ways[key];require(type(part['wayVersion']) is int and part['wayVersion']==way['version'],'OSM source way version changed')
        start,end=part['fromNodeIndex'],part['toNodeIndex']
        require(type(start) is int and type(end) is int and 0<=start<end<len(way['nodes']), 'OSM parts must retain original river-way order')
        require(way['tags'].get('tidal')!='yes' and way['tags'].get('flow_direction') not in ('both','-1','reverse'),'OSM river flow order needs separate review')
        segment=way['nodes'][start:end+1]
        if refs:
            require(refs[-1]==segment[0], 'OSM source parts cannot invent a connector')
            segment=segment[1:]
        require(not (seen & set(segment)) and len(segment)==len(set(segment)), 'OSM source path contains a node loop')
        seen.update(segment);refs.extend(segment);chain.extend(nodes[n] for n in segment)
    return chain


def valid_direction(direction):
    return direction.get('method')==METHOD and isinstance(direction.get('parts'),list) and bool(direction['parts']) and isinstance(direction.get('clip'),dict)


def validate_osm_review(record,root):
    require(root is not None,'Reviewed OSM course needs saved review evidence')
    def evidence(item,image=False):
        require(isinstance(item,dict) and isinstance(item.get('file'),str) and item['file'].startswith('research/'), 'OSM review evidence path required')
        path=(root/item['file']).resolve()
        require(path.is_relative_to((root/'research').resolve()) and path.is_file(),'OSM review evidence missing or outside research')
        if image:require(path.suffix.lower() in ('.jpg','.jpeg','.png','.webp'),'OSM visual evidence must be an image')
        require(hashlib.sha256(path.read_bytes()).hexdigest()==item.get('sha256'),'OSM review evidence changed; re-review required')
        return path
    review=record.get('osmReview',{})
    rows=review.get('parts',[])
    require(isinstance(rows,list) and [r.get('part') for r in rows]==record['direction']['parts'],'Every OSM source part needs its own review')
    for row in rows:
        require(isinstance(row.get('reason'),str) and row['reason'].strip(),'OSM source part needs a review reason')
        images=row.get('imageryEvidence');require(isinstance(images,list) and images,'OSM source part needs saved imagery')
        for item in images:evidence(item,True)
    full=json.loads(evidence(review.get('fullCourse')).read_text())
    require(full.get('status')=='reviewed-overview' and full.get('sourceSha256')==record['source']['sha256'], 'OSM full-course review does not match source')
    geometry_hash=hashlib.sha256(json.dumps(record['geometry'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    require(full.get('geometrySha256')==geometry_hash,'OSM full-course imagery review belongs to different geometry')
    images=full.get('imagery',[]);ids=[r.get('id') for r in images]
    require(images and all(isinstance(i,str) and i for i in ids) and len(ids)==len(set(ids)) and sorted(full.get('reviewedFrameIds',[]))==sorted(ids),'OSM full-course review must cover every saved frame')
    for item in images:evidence(dict(file=item.get('file'),sha256=item.get('imageSha256')),True)


def validate_osm_course(record, raw, root=None):
    require(record.get('scope')=='river-course-overview','OSM courses are display-only river overviews')
    require(not any(record.get('features',{}).get(k) for k in ('landOverlay','distanceEstimate','remainingTime')),'OSM course cannot enable land or timing features')
    require(record.get('license')==LICENSE,'OSM attribution and ODbL license metadata required')
    url=urlsplit(record['source']['url']);query=parse_qs(url.query)
    require(url.scheme=='https' and url.netloc=='api.openstreetmap.org' and url.path=='/api/0.6/map' and set(query)=={'bbox'},'OSM course needs its original native API map source')
    try:bounds=[float(v) for v in query['bbox'][0].split(',')]
    except (ValueError,TypeError):bounds=[]
    require(len(bounds)==4 and all(math.isfinite(v) for v in bounds) and -180<=bounds[0]<bounds[2]<=180 and -85<=bounds[1]<bounds[3]<=85 and (bounds[2]-bounds[0])*(bounds[3]-bounds[1])<=.25,'OSM source extent is invalid or too broad')
    direction=record['direction'];require(valid_direction(direction),'Invalid OSM river-way direction record')
    chain=source_chain(raw,direction['parts'])
    snapshot_bounds=ET.fromstring(raw).find('bounds')
    try:saved=[float(snapshot_bounds.get(k)) for k in ('minlon','minlat','maxlon','maxlat')]
    except (AttributeError,TypeError,ValueError):saved=[]
    require(len(saved)==4 and all(abs(a-b)<=1e-6 for a,b in zip(saved,bounds)), 'OSM snapshot bounds differ from its source request')
    clip={label:nearest_position(chain,record[side]) for label,side in [('start','putIn'),('end','takeOut')]}
    require(direction['clip']==clip,'OSM source trim no longer matches access-area snapshots')
    expected=trim_chain(chain,clip)
    require(record.get('geometry')==expected,'Displayed OSM course differs from original source nodes or trim')
    require(all(bounds[0]<=x<=bounds[2] and bounds[1]<=y<=bounds[3] for x,y in expected['coordinates']),
            'OSM course extends outside the queried river corridor')
    if record.get('status')=='reviewed':validate_osm_review(record,root)
