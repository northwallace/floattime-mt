#!/usr/bin/env python3
"""Archive current access sources; HTTP success is evidence retrieval, not approval."""
import argparse, hashlib, json, ssl, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
try:
 from tools.build_catalog import ROOT,build
except ModuleNotFoundError:
 from build_catalog import ROOT,build

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--states',nargs='+',required=True);parser.add_argument('--output',type=Path,help='Separate evidence directory; existing manifests are preserved unless this exact path is reused');args=parser.parse_args()
 catalog=build(); urls={}
 for r in catalog['rivers']:
  if r['state'] not in args.states:continue
  for sec in r['sections']:
   if not sec.get('mapPilot'):continue
   for end in ('putIn','takeOut'):
    p=sec[end+'Access']
    for key in ('sourceUrl','coordinateSourceUrl'):
     if p.get(key):urls.setdefault(p[key],[]).append({'state':r['state'],'riverId':r['id'],'sectionId':sec['id'],'accessId':sec[end+'AccessId']})
 out=args.output or ROOT/('research/source-check-'+datetime.now(timezone.utc).strftime('%Y%m%d'));(out/'raw').mkdir(parents=True,exist_ok=True)
 def fetch(item):
  url,uses=item;record={'url':url,'uses':uses,'checkedAt':datetime.now(timezone.utc).isoformat()}
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'FloatETA-access-review/1.0'})
   with urllib.request.urlopen(req,timeout=18) as res:
    content=res.read(8*1024*1024+1)
    if len(content)>8*1024*1024:raise ValueError('Source too large for this check')
    record.update(status=res.status,finalUrl=res.url,contentType=res.headers.get('Content-Type',''),sha256=hashlib.sha256(content).hexdigest())
    name=hashlib.sha256(url.encode()).hexdigest()[:20]+'-'+record['sha256'][:16]+'.source';(out/'raw'/name).write_bytes(content);record['snapshot']='raw/'+name
    if 'json' in record['contentType'] or content[:1] in (b'{',b'['):
     data=json.loads(content)
     if isinstance(data,dict) and ('error' in data or ('features' in data and not data['features'])):record['error']='GIS source returned an error or no features'
  except Exception as exc:record['error']=str(exc)
  print(('FAIL ' if record.get('error') else 'OK ')+url,flush=True)
  return record
 with ThreadPoolExecutor(max_workers=8) as pool:records=list(pool.map(fetch,urls.items()))
 (out/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
 print(f'{len(records)} sources; {sum(bool(r.get("error")) for r in records)} retrieval failures',flush=True)
if __name__=='__main__':main()
