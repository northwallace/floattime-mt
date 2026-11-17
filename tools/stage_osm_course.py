#!/usr/bin/env python3
"""Stage an offline OSM river overview from explicit, versioned way selections.

Never downloads, approves or publishes. Source XML, part choices and outputs
must be under research/. All candidate capabilities remain disabled.
"""
import argparse,hashlib,json,sys
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.build_catalog import build
from tools.osm_courses import METHOD,LICENSE,source_chain,validate_osm_course
from tools.agency_courses import nearest_position,trim_chain
from tools.route_catalog import geometry_checks


def run(river_id,section_id,source,source_url,parts_path,output,root=ROOT):
    source=source.resolve();parts_path=parts_path.resolve();output=output.resolve();research=(root/'research').resolve()
    if not all(p.is_relative_to(research) for p in (source,parts_path,output)) or output.exists():
        raise ValueError('Choose saved research inputs and a new research output folder')
    catalog=build(root);river=next(r for r in catalog['rivers'] if r['id']==river_id);section=next(s for s in river['sections'] if s['id']==section_id)
    if not all(section.get(side+'Coords') for side in ('putIn','takeOut')):raise ValueError('Section needs sourced access-area coordinates')
    raw=source.read_bytes();parts=json.loads(parts_path.read_text());chain=source_chain(raw,parts)
    clip={label:nearest_position(chain,section[side+'Coords']) for label,side in [('start','putIn'),('end','takeOut')]}
    record=dict(version=1,state=river['state'],riverId=river_id,sectionId=section_id,status='candidate',scope='river-course-overview',source=dict(name='OpenStreetMap original river ways',url=source_url,checkedOn=date.today().isoformat(),streamId=river['name'],evidenceFile=str(source.relative_to(root)),sha256=hashlib.sha256(raw).hexdigest()),license=dict(LICENSE),putIn=dict(name=section['putIn'],**section['putInCoords']),takeOut=dict(name=section['takeOut'],**section['takeOutCoords']),catalogMiles=section['miles'],geometry=trim_chain(chain,clip),direction=dict(method=METHOD,parts=parts,clip=clip),features=dict(display=False,landOverlay=False,distanceEstimate=False,remainingTime=False),note='Research candidate only. Original OSM river-way nodes and explicit branch choices require full visual review. Edit timestamps are not survey dates. No public access, navigable channel, shoreline connector, distance adoption or timing capability is established.')
    validate_osm_course(record,raw);metrics,issues=geometry_checks(record);record['checks']=dict(metrics=metrics,issues=issues)
    output.mkdir(parents=True);(output/'candidate.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    (output/'source-selection.json').write_text(json.dumps(dict(parts=parts,sourceSha256=record['source']['sha256'],sourceUrl=source_url,capabilitiesEnabled=False),indent=2)+'\n')
    return record


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--river',required=True);p.add_argument('--section',required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--source-url',required=True);p.add_argument('--parts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    try:r=run(a.river,a.section,a.source,a.source_url,a.parts,a.output)
    except (ValueError,OSError,KeyError,StopIteration) as e:p.error(str(e))
    print(json.dumps(dict(status=r['status'],features=r['features'],checks=r['checks']),indent=2))
