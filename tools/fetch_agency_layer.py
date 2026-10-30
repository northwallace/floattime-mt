#!/usr/bin/env python3
"""Archive complete public ArcGIS point layers for review, never catalog promotion.

python3 tools/fetch_agency_layer.py --source OR-boating-access
The agency_sources configuration must link to the agency's own discovery page.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def get(url, params):
    with urllib.request.urlopen(url + '?' + urllib.parse.urlencode({'f':'json', **params}), timeout=35) as response:
        payload = json.load(response)
    if not isinstance(payload, dict) or payload.get('error'):
        raise ValueError('Agency service returned an error')
    return payload


def download(config, request=get):
    url = config['url']
    if not re.fullmatch(r'https://[^?#]+/(?:FeatureServer|MapServer)/\d+', url):
        raise ValueError('Expected a public HTTPS ArcGIS layer URL')
    meta = request(url, {})
    oid = meta.get('objectIdField') or next((f['name'] for f in meta.get('fields', []) if f['type']=='esriFieldTypeOID'), None)
    if meta.get('geometryType') != 'esriGeometryPoint' or not oid:
        raise ValueError('This importer requires a point layer with an object ID')
    fields = config.get('fields')
    available = {f['name'] for f in meta.get('fields', [])}
    if not isinstance(fields, list) or not fields or not all(isinstance(f, str) and f in available for f in fields):
        raise ValueError('Explicit public attribute allowlist required; source schema changed')
    fields = list(dict.fromkeys([oid, *fields]))
    result = request(url+'/query', {'where':config.get('where','1=1'), 'returnIdsOnly':'true'})
    ids = result.get('objectIds')
    if not isinstance(ids,list) or result.get('exceededTransferLimit') or len(ids)!=len(set(ids)):
        raise ValueError('Incomplete or duplicate agency ID inventory')
    features = {}
    for offset in range(0,len(ids),200):
        batch = ids[offset:offset+200]
        data = request(url+'/query', {'objectIds':','.join(map(str,batch)), 'outFields':','.join(fields), 'outSR':4326, 'returnGeometry':'true'})
        if data.get('exceededTransferLimit') or not isinstance(data.get('features'),list):
            raise ValueError('Agency feature response is truncated')
        found = set()
        for feature in data['features']:
            identifier = feature.get('attributes',{}).get(oid)
            point = feature.get('geometry') or {}
            if identifier not in batch or identifier in found or identifier in features:
                raise ValueError('Unexpected or duplicate agency feature')
            if not all(type(point.get(k)) in (int,float) and math.isfinite(point[k]) and abs(point[k])<=limit for k,limit in [('x',180),('y',90)]):
                raise ValueError('Missing or invalid point coordinate; review source')
            # Enforce the allowlist locally too: some services ignore outFields.
            clean = {'attributes':{k:v for k,v in feature['attributes'].items() if k in fields}, 'geometry':{'x':point['x'],'y':point['y']}}
            found.add(identifier); features[identifier] = clean
        if found != set(batch):
            raise ValueError('Agency omitted requested features; refusing partial snapshot')
    # Check the inventory again so edits during pagination cannot silently omit sites.
    final = request(url+'/query', {'where':config.get('where','1=1'), 'returnIdsOnly':'true'})
    if final.get('exceededTransferLimit') or sorted(final.get('objectIds',[])) != sorted(ids):
        raise ValueError('Agency inventory changed during download; retry')
    public_meta = {k:meta[k] for k in ('name','description','geometryType','copyrightText','editingInfo') if k in meta}
    public_meta['fields'] = [f for f in meta.get('fields',[]) if f['name'] in fields]
    return {'metadata':public_meta, 'objectIdField':oid, 'features':[features[i] for i in sorted(ids)]}


def archive(root, config, data):
    folder = root/'research/agency-sources'/config['id']
    folder.mkdir(parents=True,exist_ok=True)
    content = (json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()
    digest = hashlib.sha256(content).hexdigest()
    file = folder/(digest+'.json')
    if file.exists() and file.read_bytes() != content:
        raise ValueError('Existing immutable snapshot was modified')
    if not file.exists(): file.write_bytes(content)
    previous = folder/'latest.json'
    changes = None
    if previous.exists():
        old = json.loads(previous.read_text()); old_file=root/old['file']
        if hashlib.sha256(old_file.read_bytes()).hexdigest()!=old['sha256']:
            raise ValueError('Previous snapshot was modified')
        old_data=json.loads(old_file.read_text());oid=data['objectIdField']
        before={str(f['attributes'][oid]):f for f in old_data['features']};after={str(f['attributes'][oid]):f for f in data['features']}
        changes={'added':sorted(after.keys()-before.keys()),'removed':sorted(before.keys()-after.keys()),'changed':sorted(k for k in before.keys()&after.keys() if before[k]!=after[k])}
    receipt={'version':1,'source':config,'retrievedAt':datetime.now(timezone.utc).isoformat(),'file':str(file.relative_to(root)),'sha256':digest,'features':len(data['features']),'changes':changes,'reviewStatus':'research-only'}
    previous.write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',required=True);args=parser.parse_args()
    if not re.fullmatch(r'[A-Z]{2}-[a-z0-9-]+',args.source):parser.error('Invalid source ID')
    config=json.loads((ROOT/'catalog/agency_sources'/f'{args.source}.json').read_text())
    if config.get('id')!=args.source or not config.get('discoveryUrl','').startswith('https://'):raise ValueError('Source provenance required')
    receipt=archive(ROOT,config,download(config))
    print(json.dumps({k:receipt[k] for k in ('file','features','changes','reviewStatus')},indent=2))
