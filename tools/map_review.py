"""Section-specific map approval fingerprints. Changed evidence needs re-review."""
import hashlib, json


def fingerprint(river, section, put_in, take_out):
    fields=('id','putIn','takeOut','putInAccessId','takeOutAccessId','miles','difficulty','accessReview','distanceReview','routeReview','notices','notes','distanceEvidence')
    payload={'riverId':river['id'],'state':river['state'],'section':{k:section[k] for k in fields if k in section},'putIn':put_in,'takeOut':take_out}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def current_fingerprints(catalog, *, state=None, river_id=None, section_id=None):
    """Report signatures from normalized records; never approve or write maps."""
    points={point['id']:point for point in catalog['accessPoints']}
    rows=[]
    for river in catalog['rivers']:
        if state and river['state']!=state or river_id and river['id']!=river_id:
            continue
        for section in river['sections']:
            if section_id and section['id']!=section_id:
                continue
            ends=[points.get(section.get(end+'AccessId')) for end in ('putIn','takeOut')]
            if any(point is None for point in ends):
                raise ValueError(f"{river['id']}/{section['id']}: normalized access IDs are required to compute a review fingerprint")
            rows.append({
                'state':river['state'],'riverId':river['id'],'sectionId':section['id'],
                'label':section['putIn']+' → '+section['takeOut'],
                'accessStatuses':[point.get('status') if point else None for point in ends],
                'mapReleased':section.get('mapReleased',False),
                'fingerprint':fingerprint(river,section,*ends),
            })
    return rows


if __name__=='__main__':
    import argparse,sys
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from tools.build_catalog import build
    parser=argparse.ArgumentParser(description='Print current map review fingerprints using normalized access records. Does not approve or change maps.')
    parser.add_argument('--state');parser.add_argument('--river');parser.add_argument('--section')
    args=parser.parse_args()
    if args.section and not args.river:parser.error('--section requires --river')
    try:
        rows=current_fingerprints(build(),state=args.state,river_id=args.river,section_id=args.section)
    except ValueError as exc:
        parser.error(str(exc))
    if not rows:parser.error('No matching sections')
    print(json.dumps({'approvalGranted':False,'sections':rows},ensure_ascii=False,indent=2))
