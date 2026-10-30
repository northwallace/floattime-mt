"""Small directory index and lazy per-river assets for national growth."""
import hashlib,json


def outputs(catalog):
    assets={};summaries=[]
    for river in catalog['rivers']:
        text=json.dumps(river,ensure_ascii=False,separators=(',',':'))+'\n'
        digest=hashlib.sha256(text.encode()).hexdigest()[:20]
        file=f'catalog/rivers/{river["id"]}.{digest}.json'
        assets['public/'+file]=text
        summary={k:river[k] for k in ('id','name','state','lat','lon')}
        summary['sections']=[{k:s[k] for k in ('id','putIn','takeOut')} for s in river['sections']]
        summary['file']=file;summaries.append(summary)
    index={k:catalog[k] for k in ('version','states','craft','mapRelease')};index['rivers']=summaries
    access_index = {p['id']:{'file':f"map_points/{p['state']}.json",'name':p['name'],'aliases':p.get('aliases',[])} for p in catalog['accessPoints']}
    assets['catalog/access-index.json']=json.dumps({'version':1,'points':access_index},ensure_ascii=False,indent=2)+'\n'
    source_index={'version':1,'settings':'settings.json','accessIndex':'access-index.json','routeIndex':'routes/index.json','mapPoints':[f"map_points/{s['id']}.json" for s in catalog['states']],'rivers':[f"rivers/{r['id']}.json" for r in catalog['rivers']]}
    source_index['agencySourceIndex'] = 'agency_sources/index.json'
    assets['catalog/source-index.json']=json.dumps(source_index,indent=2)+'\n'
    assets['public/catalog-index.json']=json.dumps(index,ensure_ascii=False,separators=(',',':'))+'\n'
    return assets


def write_or_check(root,catalog,check=False):
    assets=outputs(catalog)
    for name,text in assets.items():
        path=root/name
        if check:
            if not path.exists() or path.read_text()!=text:raise ValueError('Generated catalog assets stale: '+name)
        else:
            path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix('.tmp');temp.write_text(text);temp.replace(path)
    for path in (root/'public/catalog/rivers').glob('*.json'):
        if str(path.relative_to(root)) not in assets:
            if check:raise ValueError('Stale river asset: '+path.name)
            path.unlink()
