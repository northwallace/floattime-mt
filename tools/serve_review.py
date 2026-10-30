#!/usr/bin/env python3
"""Private loopback-only review workspace. Never served by the production app.
python3 tools/serve_review.py --port 8777
Shares the normal local planner/assets; review decisions never edit the catalog.
"""
import argparse, json, os, secrets, sys, time
from pathlib import Path
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from tools.build_review_queue import inventory
TOKEN=secrets.token_urlsafe(32)
UI=Path(__file__).parent/'review_ui'


def review_data():
    data=inventory()
    data['submissions']=server._load_feedback()
    path=Path(server.DATA_DIR)/'review-decisions.json'
    data['decisions']=server._load_records(str(path))
    data['token']=TOKEN
    return data


class ReviewHandler(server.Handler):
    def _do_GET(self):
        path=urlsplit(self.path).path
        if path in ('/api/private-review', '/review', '/review.js') and self.headers.get('Host') not in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'):
            self._send_json({'error':'Local host required'},403);return
        if path=='/api/private-review':
            self._send_json(review_data());return
        if path in ('/review','/review.js'):
            file=UI/('index.html' if path=='/review' else 'review.js')
            self._send_bytes(file.read_bytes(),'text/html; charset=utf-8' if path=='/review' else 'text/javascript; charset=utf-8');return
        super()._do_GET()
    def _do_POST(self):
        if urlsplit(self.path).path!='/api/private-review/decision':return super()._do_POST()
        # Non-simple header and unguessable per-process token prevent cross-site writes.
        if self.headers.get('X-Review-Token')!=TOKEN:
            self._send_json({'error':'Review token required'},403);return
        origin=self.headers.get('Origin')
        if origin and origin!=f'http://127.0.0.1:{self.server.server_port}':
            self._send_json({'error':'Local origin required'},403);return
        body=self._read_body_json()
        if not isinstance(body,dict) or body.get('status') not in ('needs-research','reviewed','rejected') or not isinstance(body.get('note'),str) or not 1<=len(body['note'].strip())<=2000:
            self._send_json({'error':'Choose a status and add a review note'},400);return
        data=review_data();allowed={x['id'] for kind in ('sections','research','submissions') for x in data[kind]}
        if body.get('id') not in allowed:self._send_json({'error':'Unknown review item'},400);return
        record={k:body[k] for k in ('id','status','note')};record['reviewedAt']=time.time()
        with server._lock:
            path=str(Path(server.DATA_DIR)/'review-decisions.json');entries=server._load_records(path);entries.append(record);server._save_json(path,entries)
        self._send_json({'ok':True,'decision':record},201)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=8777);args=parser.parse_args()
    http=server.ThreadingHTTPServer(('127.0.0.1',args.port),ReviewHandler)
    print(f'Private review: http://127.0.0.1:{args.port}/review',flush=True)
    try:http.serve_forever()
    except KeyboardInterrupt:pass
    finally:http.server_close()
if __name__=='__main__':main()
