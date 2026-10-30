#!/usr/bin/env python3
"""Check every assigned station through the app's real flow adapter; never edit it.

Example: python3 tools/audit_gauges.py --base-url http://127.0.0.1:8780 --state WY
Exit 1 means at least one station needs review; zero flow is valid but not floatable.
"""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import urlopen
try:
    from tools.flow_sources import flow_key, gauge_relationship
except ModuleNotFoundError:
    from flow_sources import flow_key, gauge_relationship

def classify(data, now_ms):
    flow, stamp = data.get('flow'), data.get('at')
    numeric = lambda value: type(value) in (int, float) and math.isfinite(value)
    if not numeric(flow) or not numeric(stamp) or flow < 0:
        return {'status': 'no-discharge', 'flow': None, 'ageMinutes': None}
    age = (now_ms - stamp) / 60000
    status = 'current' if -5 <= age <= 120 else 'stale-or-invalid-time'
    return {'status': status, 'flow': flow, 'ageMinutes': round(age, 1),
            'meetsFlowFreshnessCheck': status == 'current' and flow > 0,
            'staleCache': bool(data.get('stale'))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--state', help='Optional two-letter state filter')
    parser.add_argument('--river', action='append', help='Optional river ID filter; repeat to check a review batch')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--delay', type=float, default=1.5, help='Seconds between stations (minimum 0.5)')
    args = parser.parse_args()
    base = args.base_url.rstrip('/')
    parsed = urlsplit(base)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        parser.error('Use an HTTP(S) base URL without credentials, query or fragment')
    with urlopen(base + '/catalog.json', timeout=20) as response:
        catalog = json.load(response)
    rivers = [r for r in catalog['rivers'] if (not args.state or r['state'] == args.state.upper()) and (not args.river or r['id'] in args.river)]
    if not rivers:
        parser.error('No rivers match this filter')
    sites = sorted({key for r in rivers if (key := flow_key(r))})
    rows = [{'gauge': None, 'rivers': [r['id']], 'status': 'reference-only' if gauge_relationship(r) == 'other-river-reference' else 'unassigned',
             'meetsFlowFreshnessCheck': False} for r in rivers if not flow_key(r)]
    for i, site in enumerate(sites):
        if i:
            time.sleep(max(.5, args.delay))
        row = {'gauge': site, 'rivers': [r['id'] for r in rivers if flow_key(r) == site]}
        try:
            with urlopen(base + '/api/gauge?' + urlencode({'site': site}), timeout=20) as response:
                row.update(classify(json.load(response), time.time() * 1000))
        except HTTPError as error:
            row.update(status='request-failed', httpStatus=error.code)
        except (OSError, ValueError) as error:
            row.update(status='request-failed', error=type(error).__name__)
        rows.append(row)
        print(f'{i+1}/{len(sites)} {site}: {row["status"]}', flush=True)
        if row.get('httpStatus') == 429:
            # Do not turn an upstream quota response into a storm of retries.
            rows.extend({'gauge': s, 'status': 'not-checked-rate-limit', 'rivers': [r['id'] for r in rivers if flow_key(r) == s]} for s in sites[i+1:])
            break
    result = {'checkedAt': datetime.now(timezone.utc).isoformat(), 'baseUrl': base,
              'note': 'Point-in-time discharge check. Current data does not verify station suitability, access, safety or timing calibration.', 'gauges': rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    return 0 if all(r['status'] in ('current', 'unassigned', 'reference-only') for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
