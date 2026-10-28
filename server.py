#!/usr/bin/env python3
"""
Float ETA — development/production server.
Serves the static site from ./public and a small JSON API for
community obstruction reports and contact messages.

No dependencies beyond the Python 3 standard library.

Run:  python3 server.py  [PORT]   (default 8000)
"""

import json
import math
import hashlib
import socket
import os
import re
import sys
import threading
import time
import uuid
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlsplit

import seo

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(ROOT, "public")
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(ROOT, "data"))
REPORTS_FILE = os.path.join(DATA_DIR, "reports.json")
CONTACTS_FILE = os.path.join(DATA_DIR, "contacts.json")
FEEDBACK_FILE = os.path.join(DATA_DIR, "feedback.json")
MAX_FEEDBACK = 5000
_feedback_attempts = {}
MAX_CONTACTS = 200
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_lock = threading.Lock()
_gauge_lock = threading.Lock()
_gauge_cache = {}
_gauge_fetch_locks = {}
GAUGE_TTL = 300
GAUGE_STALE_TTL = 3600
USGS_CONTINUOUS = "https://api.waterdata.usgs.gov/ogcapi/v1/collections/continuous/items"

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

ASSET_LINK = re.compile(r'''((?:src|href)=["'])(/?[A-Za-z0-9_-]+\.(?:css|js))(?:\?v=[^"']*)?(["'])''')


def _fingerprint_html(body):
    """Serve current asset URLs without requiring editors to bump version strings."""
    text = body.decode('utf-8') if isinstance(body, bytes) else body
    def replace(match):
        try:
            with open(os.path.join(PUBLIC, match[2].lstrip('/')), 'rb') as f:
                digest = hashlib.sha256(f.read()).hexdigest()[:20]
        except OSError:
            return match[0]
        return f'{match[1]}{match[2]}?v={digest}{match[3]}'
    return ASSET_LINK.sub(replace, text).encode('utf-8')


def _map_config():
    """Only the browser-safe basemap key is exposed; never return arbitrary config."""
    key = os.environ.get("ARCGIS_BASEMAP_API_KEY", "").strip()
    local = {}
    if not key:
        try:
            with open(os.path.join(ROOT, "map-config.local.json")) as f:
                local = json.load(f)
                key = local.get("arcgisApiKey", "")
        except (OSError, ValueError, AttributeError):
            key = ""
    if not isinstance(key, str) or not key.strip():
        return None
    config = {"arcgisApiKey": key.strip()}
    # Explicit local opt-in. Production environment credentials never enable it.
    if local.get("routePilotEnabled") is True:
        try:
            with open(os.path.join(ROOT, "catalog", "route_pilots", "index.json")) as f:
                config["routePilots"] = json.load(f)["routes"]
        except (OSError, ValueError, KeyError, TypeError):
            pass  # Keep ordinary maps available if the local pilot index is absent.
    try:
        with open(os.path.join(ROOT, 'catalog', 'settings.json')) as f:
            release = json.load(f).get('mapRelease', {})
    except (OSError, ValueError):
        release = {}
    if release.get('reviewedRoutes') is True or local.get("routeMapsEnabled") is True:
        try:
            with open(os.path.join(PUBLIC, "routes", "index.json")) as f:
                routes = json.load(f)["routes"]
                config["routes"] = [entry for entry in routes if entry.get('state') in release.get('states', [])] if release.get('reviewedRoutes') is True else routes
        except (OSError, ValueError, KeyError, TypeError):
            pass
    return config


class StorageUnavailable(ValueError):
    """A storage problem must never be treated as an empty submission queue."""


def _load_records(path):
    try:
        with open(path, 'r') as f:
            records = json.load(f)
        if not isinstance(records, list) or not all(isinstance(row, dict) for row in records):
            raise ValueError('Invalid record storage')
        return records
    except FileNotFoundError:
        return []
    except (OSError, ValueError) as exc:
        raise StorageUnavailable('Submission storage unavailable') from exc


def _load_reports():
    return _load_records(REPORTS_FILE)


def _save_json(path, obj):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(obj, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except OSError as exc:
        raise StorageUnavailable('Submission could not be saved') from exc


def _save_reports(reports):
    _save_json(REPORTS_FILE, reports)


def _load_contacts():
    return _load_records(CONTACTS_FILE)


def _load_feedback():
    return _load_records(FEEDBACK_FILE)


def _clean(text, max_len):
    """Strip control chars and clamp length. Front end also escapes on render."""
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", str(text or ""))
    return text.strip()[:max_len]


def _allowed_gauges():
    return {river["gauge"] for river in seo.load_rivers()}


def _download_gauge(gauge):
    """Return seven days of discharge/temperature from the modern USGS API."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)
    params = {
        "f": "json",
        "monitoring_location_id": f"USGS-{gauge}",
        "parameter_code": "00060,00010",
        "datetime": f"{start.isoformat(timespec='seconds')}/{end.isoformat(timespec='seconds')}",
        "limit": "10000",
    }
    api_key = os.environ.get("USGS_API_KEY", "").strip()
    if api_key:
        params["api_key"] = api_key
    request = urllib.request.Request(
        f"{USGS_CONTINUOUS}?{urlencode(params)}",
        headers={"Accept": "application/geo+json, application/json", "User-Agent": "FloatETA/2.0 (https://www.floateta.com/)"},
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        payload = json.load(response)
    values = {"00060": [], "00010": []}
    for feature in payload.get("features", []):
        props = feature.get("properties") or {}
        code = str(props.get("parameter_code") or "")
        if code not in values:
            continue
        try:
            value = float(props["value"])
            stamp = datetime.fromisoformat(str(props["time"]).replace("Z", "+00:00")).timestamp() * 1000
        except (KeyError, TypeError, ValueError):
            continue
        if not math.isfinite(value) or not math.isfinite(stamp):
            continue
        if code == "00060" and value < 0:
            continue
        if code == "00010" and not -5 < value < 60:
            continue
        values[code].append((stamp, value))
    for records in values.values():
        records.sort()
    flow = values["00060"][-1] if values["00060"] else (None, None)
    temp = values["00010"][-1] if values["00010"] else (None, None)
    return {
        "flow": flow[1], "at": flow[0], "temp": temp[1], "tempAt": temp[0],
        "series": [{"t": stamp, "q": value} for stamp, value in values["00060"]],
        "source": "USGS Water Data API",
    }


def _gauge_reading(gauge):
    with _gauge_lock:
        fetch_lock = _gauge_fetch_locks.setdefault(gauge, threading.Lock())
    with fetch_lock:
        return _cached_gauge_reading(gauge)


def _cached_gauge_reading(gauge):
    now = time.time()
    with _gauge_lock:
        entry = _gauge_cache.get(gauge)
        if entry and now - entry["fetchedAt"] < GAUGE_TTL:
            return entry["data"]
    try:
        data = _download_gauge(gauge)
    except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        with _gauge_lock:
            entry = _gauge_cache.get(gauge)
            if entry and now - entry["fetchedAt"] < GAUGE_STALE_TTL:
                return {**entry["data"], "stale": True}
        raise
    with _gauge_lock:
        _gauge_cache[gauge] = {"fetchedAt": now, "data": data}
    return data


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "FloatETA/1.0"
    sys_version = ""

    def version_string(self):
        return self.server_version

    def _security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=(self)")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com; style-src 'self' 'unsafe-inline' https://unpkg.com; "
            "img-src 'self' data: blob: https://ibasemaps-api.arcgis.com https://static-map-tiles-api.arcgis.com; font-src 'self' data:; "
            "connect-src 'self' https://api.open-meteo.com https://ibasemaps-api.arcgis.com https://static-map-tiles-api.arcgis.com https://gis.dnrc.mt.gov; "
            "frame-src https://www.openstreetmap.org; worker-src blob:"
        )

    # ---------- helpers ----------

    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        self.end_headers()
        if not getattr(self, "_head_only", False):
            self.wfile.write(body)

    def _send_file(self, path, versioned=None):
        try:
            with open(path, "rb") as f:
                body = f.read()
        except (FileNotFoundError, IsADirectoryError):
            self._send_bytes(seo.not_found_html(), "text/html; charset=utf-8", status=404)
            return
        ext = os.path.splitext(path)[1].lower()
        if ext == '.html':
            body = _fingerprint_html(body)
        etag = '"' + hashlib.sha256(body).hexdigest()[:20] + '"'
        if versioned == etag.strip('"') and ext in {".css", ".js"}:
            cache = "public, max-age=31536000, immutable"
        elif ext in {".css", ".js"}:
            cache = "public, max-age=3600, must-revalidate"
        elif ext in {".png", ".jpg", ".svg", ".ico", ".webmanifest"}:
            cache = "public, max-age=604800"
        else:
            cache = "no-cache"
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", cache)
            self._security_headers()
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        self.send_header("ETag", etag)
        self._security_headers()
        self.end_headers()
        if not getattr(self, "_head_only", False):
            self.wfile.write(body)

    def _send_bytes(self, body, content_type, status=200, cache="no-cache"):
        if content_type.startswith('text/html'):
            body = _fingerprint_html(body)
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        self._security_headers()
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
        try:
            self._do_GET()
        except StorageUnavailable:
            self._send_json({"error": "Submission storage is temporarily unavailable. Please try again later."}, 503)

    def _do_GET(self):
        parsed = urlsplit(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/map-config":
            config = _map_config()
            self._send_json(config or {"error": "Satellite maps are not configured"}, 200 if config else 503)
            return

        if path == "/api/gauge":
            gauge = (query.get("site") or [""])[0]
            if gauge not in _allowed_gauges():
                self._send_json({"error": "Unknown gauge"}, 404)
                return
            try:
                self._send_json(_gauge_reading(gauge))
            except Exception:
                self._send_json({"error": "USGS gauge service is temporarily unavailable"}, 502)
            return

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
            self._security_headers()
            self.end_headers()
            return

        if path == "/directory.html":
            self._send_bytes(seo.directory_html(), "text/html; charset=utf-8", cache="public, max-age=300")
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
        self._send_file(full, versioned=query.get("v", [None])[0])

    def do_POST(self):
        try:
            self._do_POST()
        except StorageUnavailable:
            self._send_json({"error": "Submission storage is temporarily unavailable. Please try again later."}, 503)

    def _do_POST(self):
        path = self.path.split("?", 1)[0]

        if path == '/api/feedback':
            body = self._read_body_json()
            if not isinstance(body, dict):
                self._send_json({'error': 'Invalid JSON body'}, 400)
                return
            if body.get('website'):
                self._send_json({'ok': True}, 201)
                return
            limits = {'type': 20, 'riverId': 100, 'sectionId': 100, 'category': 30,
                      'state': 80, 'riverName': 160, 'putIn': 160, 'takeOut': 160,
                      'message': 2000, 'sourceUrl': 1000, 'name': 80, 'email': 120, 'clientToken': 36}
            if any(key in body and (not isinstance(body[key], str) or len(body[key]) > limit)
                   for key, limit in limits.items()):
                self._send_json({'error': 'Some fields are invalid or too long'}, 400)
                return
            fields = {key: _clean(body.get(key), limit) for key, limit in limits.items()}
            kind = fields['type']
            if kind not in ('correction', 'float-request') or not fields['message']:
                self._send_json({'error': 'Choose a suggestion type and describe your suggestion'}, 400)
                return
            if fields['email'] and not EMAIL_RE.match(fields['email']):
                self._send_json({'error': 'Enter a valid email or leave it blank'}, 400)
                return
            try:
                url = urlsplit(fields['sourceUrl'])
            except ValueError:
                self._send_json({'error': 'The source link is invalid'}, 400)
                return
            if fields['sourceUrl'] and (url.scheme not in ('http', 'https') or not url.netloc):
                self._send_json({'error': 'The source link must be an HTTP or HTTPS URL'}, 400)
                return
            entry = {key: fields[key] for key in ('type', 'message', 'sourceUrl', 'name', 'email')}
            entry['email'] = fields['email'].lower()
            if kind == 'correction':
                river = next((r for r in seo.load_rivers() if r['id'] == fields['riverId']), None)
                section = next((s for s in river['sections'] if s['id'] == fields['sectionId']), None) if river else None
                if not river or (fields['sectionId'] and not section):
                    self._send_json({'error': 'Choose a valid river and section'}, 400)
                    return
                if fields['category'] not in ('map-location', 'distance', 'timing', 'access', 'difficulty', 'other'):
                    self._send_json({'error': 'Choose what needs correcting'}, 400)
                    return
                entry.update(riverId=river['id'], riverName=river['name'], state=river['state'],
                             sectionId=section['id'] if section else '', category=fields['category'],
                             putIn=section['putIn'] if section else '', takeOut=section['takeOut'] if section else '')
            else:
                if not all(fields[key] for key in ('state', 'riverName', 'putIn', 'takeOut')):
                    self._send_json({'error': 'State, river, put-in and take-out are required'}, 400)
                    return
                entry.update({key: fields[key] for key in ('state', 'riverName', 'putIn', 'takeOut')})
            entry.update(id=uuid.uuid4().hex[:12], status='pending', createdAt=time.time())
            try:
                with _lock:
                    now = time.time()
                    for address in list(_feedback_attempts):
                        _feedback_attempts[address] = [t for t in _feedback_attempts[address] if now-t < 600]
                        if not _feedback_attempts[address]: del _feedback_attempts[address]
                    # Per-page token avoids a reverse proxy's shared connection
                    # address imposing one six-message limit on all visitors.
                    # This is a basic abuse guard, not proof of user identity.
                    bucket = (self.client_address[0], fields['clientToken'])
                    attempts = _feedback_attempts.get(bucket, [])
                    if len(attempts) >= 6:
                        self._send_json({'error': 'Please wait a few minutes before sending another suggestion'}, 429)
                        return
                    entries = _load_feedback()
                    if len(entries) >= MAX_FEEDBACK:
                        self._send_json({'error': 'Suggestions are temporarily unavailable. Please try again later.'}, 503)
                        return
                    entries.append(entry)
                    _save_json(FEEDBACK_FILE, entries)
                    _feedback_attempts[bucket] = attempts + [now]
            except (OSError, ValueError):
                self._send_json({'error': 'Your suggestion could not be saved. Please try again later.'}, 503)
                return
            self._send_json({'ok': True, 'id': entry['id']}, 201)
            return

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
