#!/usr/bin/env python3
"""Normalize research into a local review inventory; never promote evidence."""
import argparse, hashlib, json, shutil
from pathlib import Path
from datetime import date
try:
    from tools.build_catalog import ROOT, build
    from tools.check_agency_bindings import check as check_bindings
except ModuleNotFoundError:
    from build_catalog import ROOT, build
    from check_agency_bindings import check as check_bindings

PACKAGES = {'WA':'Washington/floateta-washington-v2','UT':'Utah/floateta-utah-v1','AZ':'Arizona/floateta-arizona-v1','CO':'Colorado/floateta-colorado-v1.1','WY':'Wyoming/floateta-wyoming-v1'}


def import_evidence(base, root=ROOT):
    manifest=[]
    for code, folder in PACKAGES.items():
        source=base/folder/'research'
        if not source.exists(): continue
        paths=set(source.glob('review-queue*.json')) | set(source.glob('readiness-status.json')) | set(source.glob('access-grades/*.json')) | set(source.glob('pending-map-points/*.json'))
        for path in sorted(paths):
            json.loads(path.read_text())
            dest=root/'research/review-imports'/code/path.relative_to(source)
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
            manifest.append({'state':code,'file':str(dest.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'importedOn':date.today().isoformat()})
    out=root/'research/review-imports/manifest.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(manifest,indent=2)+'\n')


def inventory(root=ROOT):
    catalog=build(root); items=[]; sections=[]
    route_index=json.loads((root/'public/routes/index.json').read_text())
    routes={(r['riverId'],r['sectionId']) for r in route_index['routes']}
    path_reviews={}
    for path in (root/'research/routes').glob('*/review-queue.json'):
        for row in json.loads(path.read_text()).get('sections',[]):
            path_reviews[(row['riverId'],row['sectionId'])]=row
    by_id={p['id']:p for p in catalog['accessPoints']}
    for river in catalog['rivers']:
        for sec in river['sections']:
            identity=river['id']+'/'+sec['id']
            endpoints=[]
            for end in ('putIn','takeOut'):
                point=by_id.get(sec.get(end+'AccessId'))
                endpoints.append({'endpoint':end,'label':sec[end],'accessId':sec.get(end+'AccessId'),'existing':point})
            sections.append({'id':identity,'state':river['state'],'river':river['name'],'riverId':river['id'],'sectionId':sec['id'],'label':sec['putIn']+' → '+sec['takeOut'],'accessMap':sec.get('mapPrecision','withheld'),'released':sec.get('mapReleased',False),'riverPath':identity in {a+'/'+b for a,b in routes},'distance': 'held' if sec.get('distanceReview') or sec.get('accessReview') else 'catalog','timing': 'unavailable' if river.get('timing',{}).get('mode')=='unavailable' or sec.get('distanceReview') or sec.get('accessReview') else 'existing-model','blocker':sec.get('accessReview') or sec.get('mapPendingReason') or sec.get('distanceReview') or '', 'endpoints':endpoints})
            row=sections[-1];review=path_reviews.get((river['id'],sec['id']),{})
            row['riverPathIssues']=[] if row['riverPath'] else review.get('issues') or ['geometry-review-required']
            row['riverPathNextAction']='' if row['riverPath'] else review.get('detail') or 'Review endpoint precision, downstream continuity, finer river geometry and catalog mileage; passing import checks does not release a path.'
    # Imported state packages are already local. Discover their review evidence
    # without adding another Desktop folder name whenever a state is added.
    local = set()
    for state in catalog['states']:
        folder = root/'research'/state['id']
        for pattern in ('review-queue*.json', 'readiness-status.json', 'access-grades/*.json', 'pending-map-points/*.json'):
            local.update(folder.glob(pattern))
    imported = [path for path in (root/'research/review-imports').rglob('*.json')
                if root/'research'/path.relative_to(root/'research/review-imports') not in local]
    paths = imported + list(local) + list((root/'research/MT').glob('access-review-*/section-review.json')) + list((root/'research').glob('*/local-review-*/decisions.json'))
    for path in sorted(paths):
        if path.name=='manifest.json':continue
        payload=json.loads(path.read_text())
        base = root/'research/review-imports' if path.is_relative_to(root/'research/review-imports') else root/'research'
        code=payload.get('state') or path.relative_to(base).parts[0]
        # Keep complete original objects alongside normalized lookup fields.
        groups=[]
        if isinstance(payload,dict):
            for key in ('items','pending','points','candidates','sections','rivers'):
                value=payload.get(key)
                if isinstance(value,dict):groups.extend((name,record) for name,record in value.items())
                elif isinstance(value,list):groups.extend((str(record.get('subject') or record.get('label') or record.get('id') or i),record) for i,record in enumerate(value) if isinstance(record,dict))
            if not groups: groups=[(path.stem,payload)]
        for name,record in groups:
            key=hashlib.sha256((str(path.relative_to(root))+'#'+name).encode()).hexdigest()[:16]
            items.append({'id':'research-'+key,'state':code,'subject':name,'sourceFile':str(path.relative_to(root)),'blocker':record.get('blocker') or record.get('grade') or 'research-review','nextAction':record.get('nextAction') or record.get('action') or record.get('note') or 'Review the source evidence and affected sections.','evidence':record,'accessIds':[p['id'] for p in catalog['accessPoints'] if p['state']==code and (p['name']==name or name in p.get('aliases',[]))]})
    source_index = root/'catalog/agency_sources/index.json'
    if source_index.exists():
        for source in json.loads(source_index.read_text())['sources']:
            file = root/source['bindings']
            bindings = json.loads(file.read_text())
            results = check_bindings(bindings, root)
            for binding, result in zip(bindings, results):
                items.append({'id':'agency-'+source['id']+'-'+binding['accessId'],
                    'state':source['state'], 'subject':binding['name'],
                    'sourceFile':source['bindings'], 'accessIds':[binding['accessId']],
                    'blocker':'' if result['status']=='unchanged' else 'agency-source-changed',
                    'nextAction':result['reason'], 'evidence':{'binding':binding, 'sourceCheck':result}})
    return {'version':1,'generatedOn':date.today().isoformat(),'sections':sections,'research':items}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--packages',type=Path);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    if args.packages:import_evidence(args.packages)
    data=inventory();out=ROOT/'research/national-review.json'
    targets={out:json.dumps(data,indent=2,ensure_ascii=False)+'\n'}
    for state in sorted({s['state'] for s in data['sections']}):
        rows=[s for s in data['sections'] if s['state']==state]
        targets[ROOT/f'research/readiness/{state}.json']=json.dumps({'version':1,'state':state,'generatedOn':data['generatedOn'],'sections':rows},indent=2,ensure_ascii=False)+'\n'
    for path,content in targets.items():
        if args.check:
            if not path.exists() or path.read_text()!=content:raise ValueError('Review inventory stale: run tools/build_review_queue.py')
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
    print(f"Review inventory: {len(data['sections'])} sections, {len(data['research'])} research items")
if __name__=='__main__':main()
