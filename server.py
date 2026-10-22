#!/usr/bin/env python3
"""
Float ETA — development/production server.
Serves the static site from ./public and a small JSON API for
community obstruction reports and contact messages.

No dependencies beyond the Python 3 standard library.

Run:  python3 server.py  [PORT]   (default 8000)
"""

import json
import hashlib
import socket
import os
import re
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import seo

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(ROOT, "public")
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(ROOT, "data"))
REPORTS_FILE = os.path.join(DATA_DIR, "reports.json")
CONTACTS_FILE = os.path.join(DATA_DIR, "contacts.json")
MAX_CONTACTS = 200
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

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
    ".xml": "application/xml; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
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


def _save_json(path, obj):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, path)


def _save_reports(reports):
    _save_json(REPORTS_FILE, reports)


def _load_contacts():
    try:
        with open(CONTACTS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _clean(text, max_len):
    """Strip control chars and clamp length. Front end also escapes on render."""
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", str(text or ""))
    return text.strip()[:max_len]


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "FloatETA/1.0"

    # ---------- helpers ----------

    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if not getattr(self, "_head_only", False):
            self.wfile.write(body)

    def _send_file(self, path):
        try:
            with open(path, "rb") as f:
                body = f.read()
        except (FileNotFoundError, IsADirectoryError):
            self._send_bytes(seo.not_found_html(), "text/html; charset=utf-8", status=404)
            return
        ext = os.path.splitext(path)[1].lower()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if not getattr(self, "_head_only", False):
            self.wfile.write(body)

    def _send_bytes(self, body, content_type, status=200, cache="no-cache"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        if not getattr(self, "_head_only", False):
            self.wfile.write(body)

    def _read_body_json(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0 or length > 64 * 1024:
                self.close_connection = True
                return None
            self.connection.settimeout(10)
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError, socket.timeout):
            return None

    # ---------- routes ----------

    def do_HEAD(self):
        # AdSense/Googlebot often HEAD the homepage first; default is 501.
        self._head_only = True
        self.do_GET()

    def do_GET(self):
        path = self.path.split("?", 1)[0]

        if path == "/api/reports":
            with _lock:
                reports = _load_reports()
            # Clear votes are advisory; never erase a hazard from anonymous votes.
            # Hide records with no activity in EXPIRY_DAYS.
            cutoff = time.time() - EXPIRY_DAYS * 86400
            visible = [
                r for r in reports
                if max(r.get("createdAt", 0), r.get("lastConfirmedAt", 0)) >= cutoff
            ]
            visible.sort(key=lambda r: r.get("createdAt", 0), reverse=True)
            self._send_json([{k: v for k, v in r.items() if not k.startswith("_")} for r in visible])
            return

        if path == "/api/health":
            self._send_json({"ok": True, "time": time.time()})
            return

        if path == "/sitemap.xml":
            self._send_bytes(seo.sitemap_xml(), "application/xml; charset=utf-8", cache="public, max-age=3600")
            return

        state_code = seo.STATE_BY_SLUG.get(path.strip("/").removesuffix(".html"))
        if state_code:
            self._send_bytes(seo.state_html(state_code), "text/html; charset=utf-8", cache="public, max-age=300")
            return

        if path in ("/rivers", "/rivers/"):
            self.send_response(301)
            self.send_header("Location", "/directory.html")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if path.startswith("/rivers/"):
            river = seo.find_river(path[len("/rivers/"):])
            if river:
                self._send_bytes(seo.river_html(river), "text/html; charset=utf-8", cache="public, max-age=300")
                return
            self._send_bytes(seo.not_found_html(), "text/html; charset=utf-8", status=404)
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

            river_id = _clean(body.get("riverId"), 100)
            candidates = [r for r in seo.load_rivers() if
                          (r["id"] == river_id if river_id else r["name"] == body.get("river"))]
            record = candidates[0] if len(candidates) == 1 else None
            river = record["name"] if record else ""
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
                "riverId": record["id"],
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

        if path == "/api/contact":
            body = self._read_body_json()
            if not isinstance(body, dict):
                self._send_json({"error": "Invalid JSON body"}, 400)
                return
            name = _clean(body.get("name"), 80)
            email = _clean(body.get("email"), 120).lower()
            message = _clean(body.get("message"), 2000)
            if not name or not email or not message:
                self._send_json({"error": "Name, email, and message are required"}, 400)
                return
            if not EMAIL_RE.match(email):
                self._send_json({"error": "That email does not look valid"}, 400)
                return
            entry = {
                "id": uuid.uuid4().hex[:12],
                "name": name,
                "email": email,
                "message": message,
                "createdAt": time.time(),
            }
            with _lock:
                contacts = _load_contacts()
                contacts.append(entry)
                _save_json(CONTACTS_FILE, contacts[-MAX_CONTACTS:])
            self._send_json({"ok": True}, 201)
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
                # Deduplicate one vote per connection address per report. Do not
                # trust forwarding headers supplied by arbitrary clients. This
                # is a basic abuse guard, not proof of independent people.
                voter = hashlib.sha256((rid + self.client_address[0]).encode()).hexdigest()
                voters = target.setdefault("_voters", [])
                if voter in voters:
                    self._send_json({"error": "A vote from this address was already recorded"}, 409)
                    return
                voters.append(voter)
                key = "confirmVotes" if action == "confirm" else "clearedVotes"
                target[key] = target.get(key, 0) + 1
                if action == "confirm":
                    # a "still there" vote resets the expiry clock
                    target["lastConfirmedAt"] = time.time()
                _save_reports(reports)
            self._send_json({k: v for k, v in target.items() if not k.startswith("_")})
            return

        self.send_error(404, "Not found")

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    # Port priority: command-line arg > PORT env var (used by Render) > 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = int(os.environ.get("PORT", 8000))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Float ETA running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
