#!/usr/bin/env python3
"""Fetch explicit USGS regional snapshots; verify before extracting local GIS data.
Usage: python3 tools/fetch_nhd_archives.py --manifest research/routes/nhd-archives.json --output /tmp/nhd --regions 1018 1404
The manifest must supply each official URL, byte count and independently reviewed ZIP SHA-256.
"""
import argparse, hashlib, json, shutil, urllib.request, zipfile
from pathlib import Path

def digest(path):
    with path.open('rb') as source:
        h=hashlib.sha256()
        for chunk in iter(lambda:source.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def fetch(meta,region,folder):
    m=meta[region]
    if not region.isdigit() or len(region)!=4 or not m['url'].startswith('https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/HU4/GPKG/'):
        raise ValueError('Require an explicit official USGS HU4 archive')
    archive=folder/(region+'.zip');dest=folder/(region+'.gpkg');receipt=folder/(region+'.verified.json')
    if not archive.exists() or archive.stat().st_size!=m['zipBytes']:
        temp=archive.with_suffix('.download')
        request=urllib.request.Request(m['url'],headers={'Range':f'bytes=0-{m["zipBytes"]-1}'})
        with urllib.request.urlopen(request,timeout=60) as source,temp.open('wb') as out:shutil.copyfileobj(source,out)
        if digest(temp)!=m['zipSha256']:raise ValueError('Downloaded source differs from reviewed manifest: '+region)
        temp.replace(archive)
    if digest(archive)!=m['zipSha256']:raise ValueError('Archive changed: '+region)
    # Always re-extract from the verified ZIP. A pre-existing .gpkg is not evidence of integrity.
    with zipfile.ZipFile(archive) as source:
        names=[n for n in source.namelist() if n.endswith('.gpkg')]
        if len(names)!=1:raise ValueError('Expected one GeoPackage per archive')
        temp=dest.with_suffix('.extract')
        with source.open(names[0]) as data,temp.open('wb') as out:shutil.copyfileobj(data,out)
        temp.replace(dest)
    receipt.write_text(json.dumps({'archiveUrl':m['url'],'archiveSha256':m['zipSha256'],'gpkgSha256':digest(dest)},indent=2)+'\n')
    print(region+' verified',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--regions',nargs='+',required=True);a=p.parse_args()
    meta=json.loads(a.manifest.read_text())['hu4'];a.output.mkdir(parents=True,exist_ok=True)
    for region in a.regions:fetch(meta,region,a.output)
