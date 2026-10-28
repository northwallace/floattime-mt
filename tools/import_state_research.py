#!/usr/bin/env python3
"""Stage a research package locally; dry-run unless --apply is supplied.

Usage: python3 tools/import_state_research.py /path/to/package [--apply]
Legacy research layouts from WA/UT/AZ are supported. Uncalibrated timing is
removed, never filled with defaults. Imports fail on cross-state ID collisions.
"""
import argparse
import json
import shutil
import tempfile
from pathlib import Path
from build_catalog import ROOT, build, require


def read(path):
    return json.loads(path.read_text())


def prepare(package, root):
    state_files = list(package.glob('*-state-entry.json'))
    if not state_files and (package/'catalog/state.json').exists():
        state_files = [package/'catalog/state.json']
    require(len(state_files) == 1, 'Package must have one state-entry JSON')
    state = read(state_files[0]); code = state['id']
    settings = read(root/'catalog/settings.json')
    existing = next((s for s in settings['states'] if s['id'] == code), None)
    if existing:
        require(existing['slug'] == state['slug'], 'State slug cannot change during import')
    else:
        settings['states'].append(state)
    (root/'catalog/settings.json').write_text(json.dumps(settings, indent=2)+'\n')
    timing_path = package/f'research/trip-times/timing-status-{code}.json'
    timings = read(timing_path).get('rivers', {}) if timing_path.exists() else {}
    for file in sorted((package/'catalog/rivers').glob('*.json')):
        river = read(file)
        require(river['state'] == code, 'Wrong river state: '+file.name)
        dest = root/'catalog/rivers'/file.name
        require(not dest.exists() or read(dest)['state'] == code, 'Cross-state river ID collision: '+file.name)
        status = timings.get(river['id'], {})
        # Existing app-supported explicit timing wins; legacy recommendations
        # never authorize a placeholder or a range to become a flow model.
        if river.get('timing', {}).get('mode') != 'model' and (
            not status or status.get('refSpeedIsPlaceholder') or status.get('recommendation') != 'publish'
        ):
            river['timing'] = {'mode': 'unavailable', 'note': 'A reviewed speed/flow calibration has not been established. Access and guide information remain available.'}
            river['refFlowCfs'] = None
            river['refSpeedMph'] = None
        dest.write_text(json.dumps(river, indent=2, ensure_ascii=False)+'\n')
    shutil.copyfile(package/f'catalog/map_points/{code}.json', root/f'catalog/map_points/{code}.json')
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    package = args.package.resolve()
    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        shutil.copytree(ROOT/'catalog', temp/'catalog')
        code = prepare(package, temp)
        catalog = build(temp)
        incoming = [r for r in catalog['rivers'] if r['state'] == code]
        print(f'{code}: {len(incoming)} rivers; {sum(len(r["sections"]) for r in incoming)} sections; '
              f'{sum(r.get("timing", {}).get("mode") == "unavailable" for r in incoming)} rivers without a live timing model.')
        if not args.apply:
            print('Dry run passed. Use --apply to stage locally.')
            return
        # All records pass the real builder before any catalog mutation.
        for file in (temp/'catalog/rivers').glob('*.json'):
            if read(file)['state'] == code:
                shutil.copyfile(file, ROOT/'catalog/rivers'/file.name)
        shutil.copyfile(temp/f'catalog/map_points/{code}.json', ROOT/f'catalog/map_points/{code}.json')
        shutil.copyfile(temp/'catalog/settings.json', ROOT/'catalog/settings.json')
        research = ROOT/'research'/code
        research.mkdir(parents=True, exist_ok=True)
        # Store research and evidence locally; never execute package scripts.
        shutil.copytree(package/'research', research, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for name in ('FINAL_REPORT.md', 'CHANGELOG.md', 'MANIFEST.json'):
            if (package/name).exists(): shutil.copyfile(package/name, research/name)
        print('Staged locally. Rebuild with python3 tools/build_catalog.py; no deployment performed.')


if __name__ == '__main__':
    main()
