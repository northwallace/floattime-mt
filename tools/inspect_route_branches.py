#!/usr/bin/env python3
"""Inspect downstream alternatives without choosing a channel automatically.

Outputs local research only. Optional --choices is a JSON list of explicit
{node: [lon, lat], featureId: str, reason: str} decisions from imagery review.
Even with choices, the resulting route is a candidate with all features false.
Optional --anchors selects reviewed river source features near an access area;
it never moves an access pin, supplies a shore connector or hides downstream forks.
Requires the same optional GIS dependencies as import_nhd_routes.py.
"""
import argparse,hashlib,json,math,sys
from collections import defaultdict
from pathlib import Path
from pyproj import CRS,Transformer
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.import_nhd_routes import network,directed_route,source_endpoints
from tools.route_catalog import geometry_checks,OVERVIEW_MAX_OFFSET_METERS


def check_source_coverage(payload,section):
    """Do not snap a newly added endpoint to the edge of an older query."""
    bounds=payload.get('queryScope',{}).get('bounds')
    if bounds is None:return  # Older regional archives have no query envelope.
    try:
        west,south,east,north=map(float,bounds.split(','))
        if not all(math.isfinite(v) for v in (west,south,east,north)) or not (west<east and south<north):
            raise ValueError()
    except (AttributeError,TypeError,ValueError):
        raise ValueError('Source query bounds are invalid')
    for side in ('putIn','takeOut'):
        p=section[side+'Coords']
        if not (west<=p['lon']<=east and south<=p['lat']<=north):
            raise ValueError(f'{side} is outside the saved source query; expand coverage before selecting a river course')


def downstream_inventory(edges,adj,section,project,anchors=None):
    selected=source_endpoints(edges,section,project,OVERVIEW_MAX_OFFSET_METERS,anchors)
    start,finish=(p['featureId'] for p in selected)
    if start==finish and selected[0]['sourceStationMeters']>=selected[1]['sourceStationMeters']:
        raise ValueError('Endpoint order is reversed on the source line')
    reverse=defaultdict(list)
    for key,edge in edges.items():reverse[edge['end']].append(key)
    def reachable(first,last,backward=False):
        seen=set();stack=[first]
        while stack:
            key=stack.pop()
            if key in seen:continue
            seen.add(key)
            if key!=last:stack.extend((reverse if backward else adj).get(edges[key]['start' if backward else 'end'],[]))
        return seen
    viable=reachable(start,finish)&reachable(finish,start,True)
    if start not in viable or finish not in viable:raise ValueError('No downstream source connection between selected access areas')
    branches=[]
    for node,ids in sorted(adj.items(),key=lambda item:(item[0][1],item[0][0])):
        choices=sorted(k for k in ids if k in viable)
        if len(choices)>1:branches.append(dict(node=list(node),choices=choices))
    return dict(putIn=selected[0],takeOut=selected[1],viableEdges=sorted(viable),branches=branches)


def choose_downstream_path(edges,adj,inventory,choices):
    if not isinstance(choices,list):raise ValueError('Choices must be a list')
    available={tuple(row['node']):set(row['choices']) for row in inventory['branches']}
    decisions={}
    for row in choices:
        if not isinstance(row,dict) or not isinstance(row.get('node'),list) or len(row['node'])!=2:
            raise ValueError('Choice requires its source junction coordinate')
        node=tuple(row['node']);key=row.get('featureId')
        if node not in available or key not in available[node] or node in decisions:
            raise ValueError('Unknown, duplicate or mismatched branch choice')
        if not isinstance(row.get('reason'),str) or not row['reason'].strip():raise ValueError('Each branch choice needs a review reason')
        decisions[node]=key
    start=inventory['putIn']['featureId'];finish=inventory['takeOut']['featureId']
    viable=set(inventory['viableEdges']);ids=[];used=set();key=start
    while True:
        if key in ids:raise ValueError('Selected source path contains a loop')
        ids.append(key)
        if key==finish:break
        node=edges[key]['end'];options=[k for k in adj.get(node,[]) if k in viable]
        if len(options)>1:
            if node not in decisions:raise ValueError('An encountered branch needs an explicit reviewed choice')
            used.add(node);key=decisions[node]
        elif len(options)==1:key=options[0]
        else:raise ValueError('Selected source path is disconnected')
    if used!=set(decisions):raise ValueError('Choices include a junction not encountered by this route')
    return ids


def run(river_id,section_id,source_path,output,projected_crs,choices_path=None,anchors_path=None):
    source_path=source_path.resolve();output=output.resolve()
    research=(ROOT/'research').resolve()
    if not source_path.is_relative_to(research) or not output.is_relative_to(research):
        raise ValueError('Source and outputs must stay in local research')
    raw=source_path.read_bytes();payload=json.loads(raw)
    if payload.get('error') or payload.get('exceededTransferLimit'):raise ValueError('Source response is incomplete')
    catalog=json.loads((ROOT/'public/catalog.json').read_text())
    river=next(r for r in catalog['rivers'] if r['id']==river_id)
    section=next(s for s in river['sections'] if s['id']==section_id)
    check_source_coverage(payload,section)
    crs=CRS.from_user_input(projected_crs)
    if not crs.is_projected or any(axis.unit_conversion_factor!=1 for axis in crs.axis_info[:2]):
        raise ValueError('Inspection requires a projected CRS measured in metres')
    project=Transformer.from_crs(4326,projected_crs,always_xy=True).transform
    unproject=Transformer.from_crs(projected_crs,4326,always_xy=True).transform
    edges,adj=network(payload,project)
    if not edges:raise ValueError('Source contains no directed river edges')
    anchors=json.loads(anchors_path.read_text()) if anchors_path is not None else None
    if anchors is not None and payload.get('queryPolicy')!='named-and-unnamed-flowlines-v1':
        raise ValueError('Course anchors require complete named and unnamed source coverage')
    inventory=downstream_inventory(edges,adj,section,project,anchors)
    if anchors is not None:inventory['courseAnchors']=anchors
    source=dict(name='USGS National Hydrography Dataset — High Resolution',url=payload['sourceUrl'],checkedOn=payload['checkedOn'],streamId=payload.get('queryScope',{}).get('riverName',river['name']),evidenceFile=str(source_path.relative_to(ROOT.resolve())),sha256=hashlib.sha256(raw).hexdigest())
    outputs={}
    def save(name,value):outputs[name]=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    inventory.update(riverId=river_id,sectionId=section_id,source=source,projectedCrs=projected_crs,note='Forward/reverse reachability identifies possible source paths. It does not select a navigable or principal channel.')
    save('branch-inventory.json',inventory)
    labels={key:i+1 for i,key in enumerate(inventory['viableEdges'])}
    save('network.geojson',dict(type='FeatureCollection',features=[dict(type='Feature',properties=dict(id=key,label=str(labels[key])),geometry=dict(type='LineString',coordinates=edges[key]['coordinates'])) for key in inventory['viableEdges']]))
    if choices_path is not None:
        choices=json.loads(choices_path.read_text());ids=choose_downstream_path(edges,adj,inventory,choices)
        restricted={key:edges[key] for key in ids};selected_adj=defaultdict(list)
        for key,edge in restricted.items():selected_adj[edge['start']].append(key)
        geometry,direction=directed_route(restricted,selected_adj,section,project,unproject,overview=True,anchors=anchors)
        if direction['featureIds']!=ids:raise ValueError('Clipped source path does not match the reviewed branch choices')
        record=dict(version=1,state=river['state'],riverId=river_id,sectionId=section_id,status='candidate',source=source,
            putIn=dict(name=section['putIn'],**section['putInCoords']),takeOut=dict(name=section['takeOut'],**section['takeOutCoords']),
            catalogMiles=section['miles'],geometry=geometry,direction=direction,scope='river-course-overview',
            features=dict(display=False,landOverlay=False,distanceEstimate=False,remainingTime=False),
            note='Research candidate only. Branch choices require source and imagery review before display; landing connections are not mapped.')
        if anchors is not None:record['courseAnchors']=anchors
        metrics,issues=geometry_checks(record)
        if section.get('distanceReview'):issues.append('catalog-distance-under-review')
        if section.get('routeReview'):issues.append('route-review-required')
        record['checks']=dict(metrics=metrics,issues=issues)
        save('candidate.json',record);save('branch-choices.json',choices)
    # Invalid choices must leave the prior inspection untouched. An inventory-only
    # rerun archives a prior candidate instead of leaving it beside fresh inputs.
    output.mkdir(parents=True,exist_ok=True)
    if choices_path is None:
        for name in ('candidate.json','branch-choices.json'):
            old=output/name
            if old.exists():
                raw=old.read_bytes();archive=output/('previous-'+old.stem+'-'+hashlib.sha256(raw).hexdigest()[:16]+'.json')
                if archive.exists() and archive.read_bytes()!=raw:raise ValueError('Research archive hash collision')
                old.replace(archive)
    for name,text in outputs.items():(output/name).write_text(text)
    print(f"{river_id}/{section_id}: {len(inventory['viableEdges'])} possible edges, {len(inventory['branches'])} forks; research only")

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--river',required=True);p.add_argument('--section',required=True)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--projected-crs',required=True);p.add_argument('--choices',type=Path)
    p.add_argument('--anchors',type=Path,help='Explicit source feature IDs and review reasons for river endpoints; access pins remain unchanged')
    a=p.parse_args();run(a.river,a.section,a.source,a.output,a.projected_crs,a.choices,a.anchors)
