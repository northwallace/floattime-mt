#!/usr/bin/env python3
"""Validate source records and build the shared browser/SEO catalog. No packages required."""
import argparse
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import re

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')

def require(ok, message):
    if not ok:
        raise ValueError(message)

def build(root=ROOT):
    settings = json.loads((root / 'catalog/settings.json').read_text())
    states = settings['states']
    codes, slugs = set(), set()
    for st in states:
        require(re.fullmatch('[A-Z]{2}', st['id']) and st['id'] not in codes, 'Invalid/duplicate state ID')
        require(SLUG.fullmatch(st['slug']) and st['slug'] not in slugs, 'Invalid/duplicate state slug')
        require(st['name'] and st['agency'] and st['agencyUrl'].startswith('https://'), 'State metadata missing')
        codes.add(st['id']); slugs.add(st['slug'])
    craft_ids = set()
    for c in settings['craft']:
        require(SLUG.fullmatch(c['id']) and c['id'] not in craft_ids and c['label'], 'Invalid/duplicate craft')
        require(isinstance(c['mult'], (int, float)) and 0 < c['mult'] <= 3, 'Invalid craft multiplier')
        craft_ids.add(c['id'])
    require(bool(craft_ids), 'At least one craft is required')
    rivers, ids = [], set()
    for path in sorted((root / 'catalog/rivers').glob('*.json')):
        r = json.loads(path.read_text())
        prefix = path.name + ': '
        require(SLUG.fullmatch(r['id']) and r['id'] == path.stem and r['id'] not in ids, prefix + 'ID must be unique and match filename')
        ids.add(r['id'])
        require(r['state'] in codes, prefix + 'Unknown state')
        for field in ('name', 'gaugeName', 'blurb'):
            require(isinstance(r[field], str) and r[field].strip(), prefix + field + ' required')
        require(isinstance(r['gauge'], str) and re.fullmatch(r'\d{8,15}', r['gauge']), prefix + 'Gauge must be an 8–15 digit string')
        try: ZoneInfo(r['timezone'])
        except (ZoneInfoNotFoundError, ValueError): raise ValueError(prefix + 'Invalid IANA timezone')
        for key, low, high in [('lat', -90, 90), ('lon', -180, 180), ('refFlowCfs', 0, 10000000), ('refSpeedMph', 0, 30)]:
            v = r[key]
            require(type(v) in (int, float) and math.isfinite(v) and low < v <= high, prefix + 'Invalid ' + key)
        require(isinstance(r['sections'], list) and len(r['sections']) > 0, prefix + 'Sections required')
        section_ids = set()
        for sec in r['sections']:
            require(SLUG.fullmatch(sec['id']) and sec['id'] not in section_ids, prefix + 'Invalid/duplicate section ID')
            section_ids.add(sec['id'])
            for key in ('putIn', 'takeOut', 'difficulty', 'notes'):
                require(isinstance(sec[key], str) and sec[key].strip(), prefix + 'Section ' + key + ' required')
            require(type(sec['miles']) in (int, float) and math.isfinite(sec['miles']) and 0 < sec['miles'] <= 2000, prefix + 'Invalid mileage')
        require(isinstance(r.get("multiDay", False), bool), prefix + "multiDay must be true or false")
        r["multiDay"] = r.get("multiDay", False)
        rivers.append(r)
    require(bool(rivers), 'No rivers found')
    rivers.sort(key=lambda r: (r['state'], r['name'].casefold()))
    return {'version': 1, 'states': states, 'craft': settings['craft'], 'rivers': rivers}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate and verify generated output is current')
    args = parser.parse_args()
    payload = json.dumps(build(), ensure_ascii=False, indent=2) + '\n'
    target = ROOT / 'public/catalog.json'
    if args.check:
        require(target.exists() and target.read_text() == payload, 'Run python3 tools/build_catalog.py to update public/catalog.json')
    else:
        temp = target.with_suffix('.tmp'); temp.write_text(payload); temp.replace(target)
    print(f'Catalog valid: {len(json.loads(payload)["rivers"])} rivers')

if __name__ == '__main__': main()
