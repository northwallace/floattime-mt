#!/usr/bin/env python3
"""
FloatTime MT — development/production server.
Serves the static site from ./public and a small JSON API for
community obstruction reports, persisted to ./data/reports.json.

No dependencies beyond the Python 3 standard library.

Run:  python3 server.py  [PORT]   (default 8000)
"""

import json
import os
import re
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(ROOT, "public")
DATA_DIR = os.path.join(ROOT, "data")
REPORTS_FILE = os.path.join(DATA_DIR, "reports.json")

_lock = threading.Lock()

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".ico": "image/x-icon",
    ".webmanifest": "application/manifest+json",
}

VALID_TYPES = {"strainer", "diversion", "fence", "low-bridge", "debris", "other"}
MAX_REPORTS = 500
EXPIRY_DAYS = 45  # reports hide after this many days unless re-confirmed


def _load_reports():
    try:
        with open(REPORTS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_reports(reports):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = REPORTS_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(reports, f, indent=2)
    os.replace(tmp, REPORTS_FILE)


def _clean(text, max_len):
    """Strip control chars and clamp length. Front end also escapes on render."""
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", str(text or ""))
    return text.strip()[:max_len]


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "FloatTimeMT/1.0"

    # ---------- helpers ----------

    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path):
        try:
            with open(path, "rb") as f:
                body = f.read()
        except (FileNotFoundError, IsADirectoryError):
            self.send_error(404, "Not found")
            return
        ext = os.path.splitext(path)[1].lower()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _read_body_json(self):
        try:
            length = min(int(self.headers.get("Content-Length", 0)), 64 * 1024)
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            return None

    # ---------- routes ----------

    def do_GET(self):
        path = self.path.split("?", 1)[0]

        if path == "/api/reports":
            with _lock:
                reports = _load_reports()
            # Hide reports marked cleared by 3+ people, and reports with no
            # activity (creation or "still there" confirmation) in EXPIRY_DAYS.
            cutoff = time.time() - EXPIRY_DAYS * 86400
            visible = [
                r for r in reports
                if r.get("clearedVotes", 0) < 3
                and max(r.get("createdAt", 0), r.get("lastConfirmedAt", 0)) >= cutoff
            ]
            visible.sort(key=lambda r: r.get("createdAt", 0), reverse=True)
            self._send_json(visible)
            return

        if path == "/api/health":
            self._send_json({"ok": True, "time": time.time()})
            return

        # static files
        if path == "/":
            path = "/index.html"
        safe = os.path.normpath(path).lstrip("/")
        full = os.path.join(PUBLIC, safe)
        if not full.startswith(PUBLIC):
            self.send_error(403, "Forbidden")
            return
        self._send_file(full)

    def do_POST(self):
        path = self.path.split("?", 1)[0]

        if path == "/api/reports":
            body = self._read_body_json()
            if not isinstance(body, dict):
                self._send_json({"error": "Invalid JSON body"}, 400)
                return

            river = _clean(body.get("river"), 80)
            section = _clean(body.get("section"), 120)
            rtype = _clean(body.get("type"), 20)
            location = _clean(body.get("location"), 160)
            description = _clean(body.get("description"), 600)
            reporter = _clean(body.get("reporter"), 40) or "Anonymous"

            if not river or not description:
                self._send_json({"error": "River and description are required"}, 400)
                return
            if rtype not in VALID_TYPES:
                rtype = "other"

            report = {
                "id": uuid.uuid4().hex[:12],
                "river": river,
                "section": section,
                "type": rtype,
                "location": location,
                "description": description,
                "reporter": reporter,
                "createdAt": time.time(),
                "confirmVotes": 0,
                "clearedVotes": 0,
            }
            with _lock:
                reports = _load_reports()
                reports.append(report)
                _save_reports(reports[-MAX_REPORTS:])
            self._send_json(report, 201)
            return

        m = re.fullmatch(r"/api/reports/([0-9a-z]{12})/(confirm|cleared)", path)
        if m:
            rid, action = m.group(1), m.group(2)
            with _lock:
                reports = _load_reports()
                target = next((r for r in reports if r["id"] == rid), None)
                if not target:
                    self._send_json({"error": "Report not found"}, 404)
                    return
                key = "confirmVotes" if action == "confirm" else "clearedVotes"
                target[key] = target.get(key, 0) + 1
                if action == "confirm":
                    # a "still there" vote resets the expiry clock
                    target["lastConfirmedAt"] = time.time()
                _save_reports(reports)
            self._send_json(target)
            return

        self.send_error(404, "Not found")

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"FloatTime MT running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
