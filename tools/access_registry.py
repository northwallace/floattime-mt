"""Permanent access identity helpers shared by migration and state imports."""
import json
import uuid


def new_id(state, name):
    # Deterministic for first import only. Persist this value across renames.
    return 'acc-' + uuid.uuid5(uuid.NAMESPACE_URL, 'https://floateta.com/access/'+state+'/'+name).hex[:20]


def migrate(root):
    registries = {}
    for path in sorted((root/'catalog/map_points').glob('*.json')):
        data = json.loads(path.read_text())
        for name, point in data['points'].items():
            point.setdefault('id', new_id(data['state'], name))
            point.setdefault('aliases', [])
        registries[data['state']] = (path, data)
    known_ids = {p['id'] for _, d in registries.values() for p in d['points'].values()}
    for path in sorted((root/'catalog/rivers').glob('*.json')):
        river = json.loads(path.read_text())
        code = river['state']
        if code not in registries:
            registries[code] = (root/f'catalog/map_points/{code}.json', {'version':2,'state':code,'auditedRivers':{},'points':{}})
        for section in river['sections']:
            for end in ('putIn','takeOut'):
                if section.get(end+'AccessId') in known_ids:
                    continue
                ref = section.get(end+'Point', {'state':code,'name':section[end]})
                points = registries[ref['state']][1]['points']
                point = points.setdefault(ref['name'], {'status':'pending','note':'No sourced access record has been added yet.','id':new_id(ref['state'],ref['name']),'aliases':[]})
                section.setdefault(end+'AccessId', point['id'])
        path.write_text(json.dumps(river,ensure_ascii=False,indent=2)+'\n')
    for path,data in registries.values():
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


if __name__ == '__main__':
    from pathlib import Path
    migrate(Path(__file__).resolve().parents[1])
