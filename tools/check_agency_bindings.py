#!/usr/bin/env python3
"""Check reviewed access/source bindings for agency changes. Never edit catalog pins.

python3 tools/check_agency_bindings.py research/expansion-20261029/OR-agency-bindings.json
Refresh the configured agency source first. Exit 1 means a binding needs review.
"""
import argparse
import hashlib
import json
from pathlib import Path
from functools import lru_cache
import re

ROOT = Path(__file__).resolve().parents[1]


def digest(feature):
    return hashlib.sha256(json.dumps(feature, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def check(bindings, root=ROOT):
    root = root.resolve()

    @lru_cache(maxsize=None)
    def payload(relative, checksum):
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Source snapshot must stay inside the research workspace')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != checksum:
            raise ValueError('Source snapshot was modified')
        return json.loads(raw)

    @lru_cache(maxsize=None)
    def index(relative, checksum, field):
        result = {}
        for feature in payload(relative, checksum)['features']:
            result.setdefault(feature['attributes'].get(field), []).append(feature)
        return result

    @lru_cache(maxsize=None)
    def latest(source_id):
        if not re.fullmatch(r'[A-Z]{2}-[a-z0-9-]+', source_id):
            raise ValueError('Invalid source ID')
        return json.loads((root / 'research/agency-sources' / source_id / 'latest.json').read_text())

    results = []
    for binding in bindings:
        status, reason = 'unchanged', 'Reviewed agency feature unchanged.'
        field, value = binding['featureField'], binding['featureId']
        original = index(binding['sourceSnapshot'], binding['sourceSha256'], field).get(value, [])
        if len(original) != 1 or digest(original[0]) != binding['featureSha256']:
            raise ValueError('Binding does not match its reviewed source feature')
        receipt = latest(binding['sourceId'])
        current = index(receipt['file'], receipt['sha256'], field).get(value, [])
        if len(current) != 1:
            status, reason = 'needs-review', 'Agency feature disappeared or became ambiguous.'
        elif digest(current[0]) != binding['featureSha256']:
            status, reason = 'needs-review', 'Agency attributes or coordinates changed; compare with the saved review.'
        if binding.get('decision') not in ('access-verified', 'verified'):
            status, reason = 'needs-review', 'Candidate has no completed access review.'
        results.append({'accessId':binding['accessId'], 'name':binding['name'], 'sourceId':binding['sourceId'], 'status':status, 'reason':reason})
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bindings', type=Path)
    args = parser.parse_args()
    results = check(json.loads(args.bindings.read_text()))
    print(json.dumps(results, indent=2))
    raise SystemExit(any(r['status'] != 'unchanged' for r in results))
