"""Copy the catalog and its route evidence without assuming one archive folder."""
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def copy_catalog(destination):
    shutil.copytree(ROOT / 'catalog', destination / 'catalog')
    shutil.copytree(ROOT / 'research/routes', destination / 'research/routes')
    # Measured distances have their own immutable source, independent of any
    # displayed route. A catalog fixture must carry that evidence as well.
    for river_file in (ROOT / 'catalog/rivers').glob('*.json'):
        for section in json.loads(river_file.read_text()).get('sections', []):
            evidence = section.get('distanceEvidence', {}).get('measurement', {})
            if evidence.get('evidenceFile'):
                relative = Path(evidence['evidenceFile'])
                source = (ROOT / relative).resolve()
                if relative.is_absolute() or not source.is_relative_to(ROOT / 'research'):
                    raise ValueError('Distance fixture evidence must remain in research')
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    index = json.loads((ROOT / 'catalog/routes/index.json').read_text())
    for state_file in index['states'].values():
        state = json.loads((ROOT / 'catalog/routes' / state_file).read_text())
        for route_file in state['routes']:
            route = json.loads((ROOT / 'catalog/routes' / route_file).read_text())
            evidence = [route['source']['evidenceFile']]
            for review in route.get('sourceSegmentReview', []):
                evidence.extend(item['file'] for item in review['imageryEvidence'])
            evidence.extend(item['file'] for item in route.get('distanceDiscrepancyReview', {}).get('imageryEvidence', []))
            for file in evidence:
                relative = Path(file)
                source = (ROOT / relative).resolve()
                if relative.is_absolute() or not source.is_relative_to(ROOT / 'research'):
                    raise ValueError('Route fixture evidence must remain in research')
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
