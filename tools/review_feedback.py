#!/usr/bin/env python3
"""Read the private correction/request queue without exposing a public endpoint.

python3 tools/review_feedback.py
python3 tools/review_feedback.py --id SUBMISSION_ID
python3 tools/review_feedback.py --json
Uses DATA_DIR when set, otherwise the project's data/ folder. Read-only.
"""
import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', help='Show one complete private submission')
    parser.add_argument('--json', action='store_true', help='Print the full private queue as JSON')
    args = parser.parse_args()
    data_dir = Path(os.environ.get('DATA_DIR', Path(__file__).resolve().parents[1]/'data'))
    path = data_dir/'feedback.json'
    try:
        entries = json.loads(path.read_text())
    except FileNotFoundError:
        entries = []
    if args.id:
        entry = next((e for e in entries if e['id'] == args.id), None)
        if entry is None: parser.error('No suggestion with that ID')
        print(json.dumps(entry, indent=2, ensure_ascii=False))
    elif args.json:
        print(json.dumps(entries, indent=2, ensure_ascii=False))
    else:
        print(f'{len(entries)} private suggestions')
        for e in reversed(entries):
            print(f"{e['id']} | {e['status']} | {e['type']} | {e['state']} | {e['riverName']} | {e.get('putIn') or 'Whole river'} → {e.get('takeOut') or '—'}")
        print('Use --id ID to read details. Suggestions never change the catalog automatically.')


if __name__ == '__main__':
    main()
