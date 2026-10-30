"""
Float ETA SEO pages — sitemap, state directories, and per-river landings.

River copy is read from public/catalog.json so the calculator and Google
see the same catalog. No extra dependencies.
"""

import json
import os
import re
import time
from urllib.parse import urlencode
from tools.flow_sources import flow_label, flow_name, flow_url, flow_description, supports_live_timing

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(ROOT, "public")
SITE = os.environ.get("SITE_URL", "https://www.floateta.com").rstrip("/")

_catalog_cache = None
_catalog_stamp = None


def catalog():
    global _catalog_cache, _catalog_stamp
    path = os.path.join(PUBLIC, "catalog.json")
    stamp = os.stat(path).st_mtime_ns
    if _catalog_cache is None or stamp != _catalog_stamp:
        with open(path, encoding="utf-8") as f:
            _catalog_cache = json.load(f)
        _catalog_stamp = stamp
    return _catalog_cache


def _state_records():
    copy = {
        "MT": {
            "intro": "Plan classic Madison and Yellowstone day floats, Missouri and Bitterroot fishing runs, and remote Smith River trips across Montana.",
            "desc": "Explore Montana float trips on the Madison, Yellowstone, Missouri, Bitterroot, Smith and more with live USGS flow and section times.",
        },
        "ID": {
            "intro": "Compare Salmon, Payette, Lochsa, Selway, Boise and Snake River floats, from easy greenbelt water to multi-day whitewater.",
            "desc": "Explore Idaho float trips on the Salmon, Payette, Lochsa, Selway, Boise and Snake rivers with live USGS flow and section times.",
        },
        "OR": {
            "intro": "Plan Deschutes, Rogue, John Day, Owyhee, Grande Ronde and Portland-area floats with current flow and river-local daylight.",
            "desc": "Explore Oregon float trips on the Deschutes, Rogue, John Day, Owyhee, Grande Ronde and more with live USGS flow and section times.",
        },
        "WA": {
            "intro": "Plan Yakima Canyon, Klickitat, Skagit, Wenatchee, Cowlitz and Olympic Peninsula floats with current flow and river-local daylight.",
            "desc": "Explore Washington float trips on the Yakima, Klickitat, Skagit, Wenatchee, Cowlitz and more with live USGS flow and section times.",
        },
        "UT": {
            "intro": "Explore Green River floats below Flaming Gorge, Colorado River sections near Moab, and San Juan and Labyrinth Canyon trips with access sources and published planning guidance.",
            "desc": "Explore Utah Green, Colorado, San Juan and San Rafael river sections with access maps, agency gauges and available guide times.",
        },
        "AZ": {
            "intro": "Explore Lower Salt and Verde River floats, Gila Box and Colorado River trips with access sources, restrictions and available published guide times.",
            "desc": "Explore Arizona Salt, Verde, Gila and Colorado river sections with access sources, agency gauges and available guide times.",
        },
    }
    def default_intro(state):
        names = list(dict.fromkeys(r['name'].split(' — ', 1)[0].split(' (', 1)[0]
                                  for r in catalog()['rivers'] if r['state'] == state['id']))[:6]
        examples = ', '.join(names)
        return f"Explore {examples} in {state['name']}, with access sources, agency gauges and available planning guidance." if examples else f"Find your next stretch in {state['name']}. Check access and local conditions before launching."

    return {s["id"]: {
        **s, "code": s["id"], "geo": "US-" + s["id"],
        "dirTitle": f'{s["name"]} Rivers to Float | Live USGS Gauges | Float ETA',
        "dirDesc": s.get('description') or copy.get(s["id"], {}).get("desc", default_intro(s)),
        "h1": f'{s["name"]} rivers to float',
        "intro": s.get('intro') or copy.get(s["id"], {}).get("intro", default_intro(s))
    } for s in catalog()["states"]}


STATES = _state_records()
STATE_BY_SLUG = {meta["slug"]: code for code, meta in STATES.items()}


def _state_names():
    names = [m["name"] for m in STATES.values()]
    return ", ".join(names[:-1]) + ", and " + names[-1] if len(names) > 2 else " and ".join(names)


def esc(text):
    import html
    return html.escape(str(text or ""), quote=True)


def catalog_slots(text):
    """Fill explicit static-page slots before delivery, including without JS."""
    import re
    data = catalog()
    links = [f'<a href="/{esc(s["slug"])}">{esc(s["name"])}</a>' for s in data['states']]
    slots = {
        'state-navigation': '\n'.join(links),
        'state-footer': ' · '.join(links),
        'state-coverage': ' · '.join(esc(s['name']) for s in data['states']),
        'river-count': str(len(data['rivers'])),
        'section-count': str(sum(len(r['sections']) for r in data['rivers'])),
    }
    return re.sub(r'<!-- catalog:([a-z-]+) -->.*?<!-- /catalog:\1 -->',
                  lambda m: slots.get(m[1], m[0]), text, flags=re.S)


def load_rivers():
    return catalog()["rivers"]


def _section_distance_label(sections):
    """Describe trip options without summing overlapping floats as river coverage."""
    distances = [s['miles'] for s in sections if not s.get('accessReview') and not s.get('distanceReview')]
    if not distances:
        return 'Distances under review'
    low, high = min(distances), max(distances)
    span = f'{low:g}' if low == high else f'{low:g}–{high:g}'
    scope = 'on available stretches' if len(distances) != len(sections) else 'per stretch'
    return f'{span} mi {scope}'


def find_river(slug):
    slug = (slug or "").replace(".html", "").strip("/")
    return next((r for r in load_rivers() if r["id"] == slug), None)


def _fmt_hours(hours):
    if hours >= 24:
        return f"{hours / 24:.1f} days"
    minutes = int(round(hours * 60))
    h, m = divmod(minutes, 60)
    if h == 0:
        return f"{m} min"
    if m == 0:
        return f"{h} hr"
    return f"{h} hr {m} min"


def _typical_hours(river, miles):
    if not supports_live_timing(river):
        return None
    speed = max(river["refSpeedMph"], 0.8)
    return miles / speed


def _notices_html(section):
    review = f'<div class="section-notice"><strong>Distance and endpoints under review</strong><p>{esc(section["distanceReview"])}</p></div>' if section.get('distanceReview') else ''
    if section.get('accessReview'):
        review += f'<div class="section-notice"><strong>Access and route under review</strong><p>{esc(section["accessReview"])}</p><p>No trip estimate is offered until the access issue is resolved.</p></div>'
    return review + ''.join(f'<div class="section-notice"><strong>{esc(n["title"])}</strong><p>{esc(n["text"])}</p>'
                   f'<a href="{esc(n["sourceUrl"])}" target="_blank" rel="noopener">{esc(n["sourceName"])}</a>'
                   f'<small>Source checked {esc(n["checkedOn"])}</small></div>' for n in section.get('notices', []))


def _guide_html(section):
    if section.get('accessReview') or section.get('distanceReview'):
        return ''
    parts = []
    for g in section.get('guideTimes', []):
        span = str(g['min']) if g['min'] == g['max'] else f"{g['min']}–{g['max']}"
        parts.append(f'<p class="guide-time"><strong>Published guide: {esc(span)} {esc(g["unit"])}</strong><br>'
                     f'{esc(g["conditions"])}<br><a href="{esc(g["sourceUrl"])}" target="_blank" rel="noopener">{esc(g["sourceName"])}</a></p>')
    return ''.join(parts)


def _state_meta(river):
    return STATES.get(river.get("state") or "MT", STATES["MT"])


def _distance_html(section):
    e = section.get('distanceEvidence')
    if not e:
        return ''
    distance = (f'Published trip length: {e["miles"]:g} mi' if e['method'] == 'published-trip-length'
                else f'River mile {e["putIn"]["riverMile"]:g} to {e["takeOut"]["riverMile"]:g}')
    return (f'<details class="distance-source"><summary>How this distance was checked</summary>'
            f'<p>{esc(e["note"])}</p><a href="{esc(e["sourceUrl"])}" target="_blank" rel="noopener">{esc(e["sourceName"])}</a>'
            f'<p>{distance} · checked {esc(e["checkedOn"])}</p></details>')


def _related(rivers, current, n=4):
    same_state = [
        r for r in rivers
        if r["id"] != current["id"] and r.get("state") == current.get("state")
    ]
    stem = current["id"].split("-")[0]
    same = [r for r in same_state if r["id"].split("-")[0] == stem]
    others = [r for r in same_state if r not in same]
    return (same + others)[:n]


def _lastmod():
    path = os.path.join(PUBLIC, "catalog.json")
    return time.strftime("%Y-%m-%d", time.gmtime(os.path.getmtime(path)))


def _head(title, description, path, extra="", json_ld=None, geo=None):
    url = SITE + path
    image = SITE + "/float-eta-share.png"
    geo = geo or STATES["MT"]
    blocks = []
    if json_ld:
        payload = json_ld if isinstance(json_ld, list) else [json_ld]
        for block in payload:
            blocks.append(
                '<script type="application/ld+json">'
                + json.dumps(block, ensure_ascii=False)
                + "</script>"
            )
    return f"""<!DOCTYPE html>
<html lang="en-US">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
  <meta name="author" content="Float ETA">
  <meta name="theme-color" content="#f5f3eb">
  <meta name="geo.region" content="{esc(geo['geo'])}">
  <meta name="geo.placename" content="{esc(geo['name'])}">
  <link rel="canonical" href="{esc(url)}">
  <link rel="alternate" hreflang="en-US" href="{esc(url)}">
  <link rel="alternate" hreflang="x-default" href="{esc(url)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Float ETA">
  <meta property="og:locale" content="en_US">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{esc(url)}">
  <meta property="og:image" content="{esc(image)}">
  <meta property="og:image:url" content="{esc(image)}">
  <meta property="og:image:secure_url" content="{esc(image)}">
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Float ETA — live river float times from USGS flow">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{esc(image)}">
  <meta name="twitter:image:alt" content="Float ETA — live river float times from USGS flow">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <link rel="manifest" href="/site.webmanifest">
  <link rel="sitemap" type="application/xml" href="/sitemap.xml">
  <link rel="stylesheet" href="/styles.css?v=20261023-1"><link rel="stylesheet" href="/middle.css?v=20261027-1">
  {extra}
  {"".join(blocks)}
</head>
"""


def _nav(active=""):
    def item(href, label, key):
        cls = ' class="is-active"' if active == key else ""
        return f'<a href="{href}"{cls}>{label}</a>'

    state_links = "\n          ".join(item(f"/{m['slug']}", m["name"], m["slug"]) for m in STATES.values())
    rivers_cls = ' class="is-active"' if active in STATE_BY_SLUG else ""
    return f"""  <a class="skip-link" href="#main">Skip to content</a>
  <header class="hero hero-legal">
    <nav class="nav" aria-label="Primary">
      <a class="brand" href="/"><svg class="brand-wave" viewBox="0 0 32 32" aria-hidden="true"><path d="M3 12c5-5 8 5 13 0s8 5 13 0M3 20c5-5 8 5 13 0s8 5 13 0" fill="none" stroke="currentColor" stroke-width="2.5"/></svg>Float <span>ETA</span></a>
      <div class="nav-links">
        {item("/", "Home", "home")}
        <details class="nav-drop">
          <summary{rivers_cls}>Rivers</summary>
          <div class="nav-drop-menu">
          {state_links}
          </div>
        </details>
        {item("/#calculator", "Float calculator", "calc")}
        {item("/about.html", "About", "about")}
      </div>
    </nav>
"""


def _footer():
    year = time.strftime("%Y")
    states = " ·\n        ".join(f'<a href="/{m["slug"]}">{m["name"]}</a>' for m in STATES.values())
    return f"""  <footer class="footer">
    <div class="footer-inner">
      <a class="brand" href="/"><svg class="brand-wave" viewBox="0 0 32 32" aria-hidden="true"><path d="M3 12c5-5 8 5 13 0s8 5 13 0M3 20c5-5 8 5 13 0s8 5 13 0" fill="none" stroke="currentColor" stroke-width="2.5"/></svg>Float <span>ETA</span></a>
      <p>Agency streamflow with approximate float-time guidance — daylight, water temp, and community obstruction reports included.</p>
      <p class="footer-links">
        <a href="/">Home</a> ·
        {states} ·
        <a href="/#calculator">Float calculator</a> ·
        <a href="/about.html">About</a> ·
        <a href="/privacy.html">Privacy Policy</a> ·
        <a href="/contact.html">Contact</a>
      </p>
      <p class="copyright">© {year} Float ETA · <a href="{SITE}">{SITE.replace("https://", "")}</a></p>
    </div>
  </footer>
</body>
</html>
"""


def _org_schema():
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Float ETA",
        "url": SITE + "/",
        "logo": SITE + "/icon-512.png",
        "description": f"Live river float-time estimates from USGS streamflow for {_state_names()}, with more states coming.",
        "areaServed": [{"@type": "State", "name": m["name"]} for m in STATES.values()],
    }


def sitemap_xml():
    lastmod = _lastmod()
    rivers = load_rivers()
    urls = [("/", "1.0", "daily"), ("/directory.html", "0.9", "weekly")]
    urls += [(f"/{m['slug']}", "0.9", "weekly") for m in STATES.values()]
    urls += [
        ("/about.html", "0.5", "monthly"),
        ("/privacy.html", "0.3", "yearly"),
        ("/contact.html", "0.3", "yearly"),
    ]
    for river in rivers:
        urls.append((f"/rivers/{river['id']}", "0.8", "weekly"))

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path, priority, freq in urls:
        parts.append("  <url>")
        parts.append(f"    <loc>{esc(SITE + path)}</loc>")
        parts.append(f"    <lastmod>{lastmod}</lastmod>")
        parts.append(f"    <changefreq>{freq}</changefreq>")
        parts.append(f"    <priority>{priority}</priority>")
        parts.append("  </url>")
    parts.append("</urlset>")
    return "\n".join(parts) + "\n"


def directory_html():
    rivers = load_rivers()
    items = []
    for river in rivers:
        state = _state_meta(river)
        items.append(
            f'<li><a href="/rivers/{esc(river["id"])}">{esc(river["name"])}</a>'
            f'<span>{esc(state["name"])} · {len(river["sections"])} {"stretch" if len(river["sections"]) == 1 else "stretches"}</span></li>'
        )
    options = "".join(
        f'<option value="{esc(meta["code"])}">{esc(meta["name"])}</option>'
        for meta in STATES.values()
    )
    desc = "Browse every Float ETA river by state, name, put-in, or take-out."
    return (
        _head("Explore rivers | Float ETA", desc, "/directory.html", json_ld=_org_schema())
        + _nav("rivers")
        + f"""
    <div class="hero-content"><h1>Find your next river.</h1><p class="hero-sub">Search by river, state, or access point.</p></div>
    <div class="hero-wave" aria-hidden="true"><svg viewBox="0 0 1440 90" preserveAspectRatio="none"><path d="M0,40 C240,90 480,0 720,35 C960,70 1200,10 1440,45 L1440,90 L0,90 Z" fill="var(--bg)"/></svg></div>
  </header>
  <main id="main" class="section river-dir">
    <p class="community-actions">Missing a route? <a href="/feedback.html?type=float-request">Request a float</a>.</p>
    <div class="directory-controls"><div class="control"><label for="directoryState">State</label><select id="directoryState"><option value="">All states</option>{options}</select></div><div class="control"><label for="directorySearch">River or access point</label><input id="directorySearch" type="text" placeholder="Try Madison or Palisades"></div></div>
    <ul id="directoryResults" class="home-river-grid">{''.join(items)}</ul>
    <div class="directory-meta"><p id="directoryStatus" role="status">Showing all {len(rivers)} rivers</p><button id="directoryMore" class="btn-primary" type="button" hidden>Show more rivers</button></div>
  </main>
  <script src="/directory.js?v=20261023-1"></script>
"""
        + _footer()
    )


def state_html(code):
    meta = STATES[code]
    rivers = [r for r in load_rivers() if r.get("state") == code]
    sections = sum(len(r["sections"]) for r in rivers)
    path = f"/{meta['slug']}"
    title = meta["dirTitle"]
    desc = meta["dirDesc"]
    cards = []
    for river in rivers:
        distance_label = _section_distance_label(river['sections'])
        diffs = sorted({s["difficulty"] for s in river["sections"]})
        cards.append(f"""
        <article class="river-dir-card">
          <h2><a href="/rivers/{esc(river['id'])}">{esc(river['name'])}</a></h2>
          <p>{esc(river['blurb'])}</p>
          <p class="river-dir-meta">{len(river['sections'])} stretch{'es' if len(river['sections']) != 1 else ''}
            · {esc(distance_label)} · {esc(', '.join(diffs))}</p>
          <a class="river-dir-link" href="/rivers/{esc(river['id'])}">River guide &amp; flow details →</a>
        </article>""")

    item_list = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": meta["h1"],
        "url": SITE + path,
        "description": desc,
        "isPartOf": {"@type": "WebSite", "name": "Float ETA", "url": SITE + "/"},
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(rivers),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i + 1,
                    "url": f"{SITE}/rivers/{r['id']}",
                    "name": r["name"],
                }
                for i, r in enumerate(rivers)
            ],
        },
    }
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": f"{meta['name']} rivers", "item": SITE + path},
        ],
    }

    others = ", ".join(
        f'<a href="/{m["slug"]}">{esc(m["name"])} rivers</a>'
        for c, m in STATES.items() if c != code
    )
    permit = ""
    if meta.get("permitNotice"):
        permit = (
            f'<p class="permit-notice">{esc(meta["permitNotice"])} '
            f'<a href="{esc(meta["permitUrl"])}" target="_blank" rel="noopener">Check current permit rules</a>.</p>'
        )

    return (
        _head(title, desc, path, json_ld=[_org_schema(), item_list, crumbs], geo=meta)
        + _nav(meta["slug"])
        + f"""
    <div class="hero-content">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / {esc(meta['name'])} rivers</nav>
      <h1>{esc(meta['h1'])}</h1>
      <p class="hero-sub">{len(rivers)} rivers and {sections} stretches with agency gauge information —
        {esc(meta['intro'])}</p>
    </div>
    <div class="hero-wave" aria-hidden="true">
      <svg viewBox="0 0 1440 90" preserveAspectRatio="none"><path d="M0,40 C240,90 480,0 720,35 C960,70 1200,10 1440,45 L1440,90 L0,90 Z" fill="var(--bg)"/></svg>
    </div>
  </header>
  <main id="main" class="section river-dir">
    <div class="section-head">
      <h2>Every Float ETA stretch in {esc(meta['name'])}</h2>
      <p>Browse put-in to take-out sections, access information, published trip guidance and agency flow. Live float-time estimates are available where a reference-flow model is established; other listings show their available guide information.
        Also explore: {others}.</p>
    </div>
    {permit}
    <div class="river-dir-grid">
      {''.join(cards)}
    </div>
  </main>
"""
        + _footer()
    )


def river_html(river):
    rivers = load_rivers()
    st = _state_meta(river)
    access_holds = sum(bool(s.get('accessReview')) for s in river['sections'])
    all_held = access_holds == len(river['sections'])
    distance_label = _section_distance_label(river['sections'])
    diffs = sorted({s["difficulty"] for s in river["sections"]})
    path = f"/rivers/{river['id']}"
    title = f"{river['name']} Float Time | {st['name']} | Float ETA"
    desc = (
        f"{river['blurb']} {len(river['sections'])} stretch"
        f"{'es' if len(river['sections']) != 1 else ''}, {distance_label}, "
        f"{', '.join(diffs)}. Access information, available gauge context and river-local daylight."
    )
    if len(desc) > 165:
        desc = desc[:162].rsplit(" ", 1)[0] + "…"

    rows = []
    access_cards = []
    faq_entities = []
    for sec in river["sections"]:
        hours = None if sec.get("distanceReview") or sec.get("accessReview") else _typical_hours(river, sec["miles"])
        time_cell = '~' + _fmt_hours(hours) if hours is not None else 'Live estimate not available'
        time_answer = (
            f"About {_fmt_hours(hours)} in a raft at a reference {int(river['refFlowCfs'])} cfs. The fishing option adds 25 minutes per river mile."
            if hours is not None else 'A live float-time estimate is not available for this stretch. Published guide times, where shown, are separate planning guidance and are not adjusted for current flow, craft or stops.'
        )
        label = f"{sec['putIn']} to {sec['takeOut']}"
        distance_cell = ('Distance under review' if sec.get('distanceReview') else
                         f"{'≈ ' if sec.get('distanceEvidence') else ''}{sec['miles']:g} mi{' · unverified' if sec.get('accessReview') else ''}")
        rows.append(f"""
        <tr>
          <td>{esc(sec['putIn'])} → {esc(sec['takeOut'])}</td>
          <td>{esc(distance_cell)}</td>
          <td>{'Route under review' if sec.get('accessReview') else esc(sec['difficulty'])}</td>
          <td>{esc(time_cell)}{_guide_html(sec)}</td>
          <td>{esc(sec['notes'])}</td>
        </tr>""")
        pending_reason = sec.get("mapPendingReason")
        access_links = (
            f'<span class="access-pending"><strong>Map unavailable:</strong> {esc(pending_reason)}</span>'
            if pending_reason else
            '<span class="access-pending">Exact access directions have not been audited yet.</span>'
        )
        if sec.get('mapPilot') and not sec.get('mapReleased'):
            access_links = '<span class="access-pending">This section’s access map is still under review.</span>'
        map_html = ""
        if sec.get("mapReleased") and sec.get("putInCoords") and sec.get("takeOutCoords") and sec.get("putInAccess") and sec.get("takeOutAccess"):
            points = (sec["putInCoords"], sec["takeOutCoords"])
            put_pos = f'{points[0]["lat"]},{points[0]["lon"]}'
            take_pos = f'{points[1]["lat"]},{points[1]["lon"]}'
            put_url = "https://www.google.com/maps/dir/?api=1&" + urlencode({"destination": put_pos})
            take_url = "https://www.google.com/maps/dir/?api=1&" + urlencode({"destination": take_pos})
            shuttle_url = "https://www.google.com/maps/dir/?api=1&" + urlencode({
                "origin": take_pos, "destination": put_pos, "travelmode": "driving",
            })
            bank = sec["takeOutAccess"].get("riverBank", "")
            bank_label = {"river-left": "river left", "river-right": "river right"}.get(bank, "")
            bank_html = f'<strong>Take-out: {bank_label}</strong> (facing downstream)<br>' if bank_label else ""
            access_links = (
                bank_html +
                f'<a href="{esc(put_url)}" target="_blank" rel="noopener">Put-in directions</a> · '
                f'<a href="{esc(take_url)}" target="_blank" rel="noopener">Take-out directions</a> · '
                f'<a href="{esc(shuttle_url)}" target="_blank" rel="noopener">Shuttle route</a><br>'
                f'<span class="access-verified">Sources checked {esc(sec["putInAccess"]["verifiedOn"])}: '
                f'<a href="{esc(sec["putInAccess"]["sourceUrl"])}" target="_blank" rel="noopener">put-in</a> · '
                f'<a href="{esc(sec["takeOutAccess"]["sourceUrl"])}" target="_blank" rel="noopener">take-out</a></span>'
            )
            if sec.get('mapPrecision') == 'approximate':
                access_links = '<strong>Approximate facility locations; exact landings are not confirmed.</strong><br>'
                for side, name in (('putInAccess', 'Put-in'), ('takeOutAccess', 'Take-out')):
                    access = sec[side]
                    access_links += f'<a href="{esc(access["sourceUrl"])}" target="_blank" rel="noopener">{name} access source</a>'
                    if access.get('status') == 'access-verified':
                        access_links += f': {esc(access["directions"])}'
                    access_links += '<br>'
            map_url = '/?' + urlencode({'river':river['id'], 'state':river['state'], 'section':sec['id'], 'map':'1'}) + '#calculator'
            map_html = (
                f'<a class="section-map-link" href="{esc(map_url)}"><span aria-hidden="true">⌖</span>'
                '<strong>Open this section’s access map</strong><span>Labelled put-in and take-out, satellite imagery and access sources.</span></a>'
            )
        access_cards.append(f"""
        <article class="access-guide">
          <div><h3>{esc(label)}</h3><p>{esc(sec['notes'])}</p>{_notices_html(sec)}{_distance_html(sec)}
          <p class="access-links">{access_links}</p>
          <a class="section-correction" href="/feedback.html?{esc(urlencode({'type':'correction','riverId':river['id'],'sectionId':sec['id']}))}">Suggest a correction for this section</a>
          <a class="section-correction" href="/feedback.html?{esc(urlencode({'type':'access-suggestion','riverId':river['id'],'sectionId':sec['id']}))}">Suggest an access location</a></div>
          {map_html}
        </article>""")
        faq_entities.append({
            "@type": "Question",
            "name": f"How long does it take to float {label} on the {river['name']}?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": time_answer + ' ' + sec['notes'],
            },
        })

    faq_entities.extend([
        {
            "@type": "Question",
            "name": f"What flow source is used for {river['name']}?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": (
                    flow_description(river) + " " + (river.get('gaugeContext', {}).get('note', '') + ' ' if river.get('gaugeContext') else '') + (
                        f"Speed is scaled from a reference {int(river['refFlowCfs'])} cfs drift of about {river['refSpeedMph']} mph."
                        if not all_held and supports_live_timing(river) else 'A calibrated live float-time estimate is not available.'
                    )
                ),
            },
        },
        {
            "@type": "Question",
            "name": f"Is the {river['name']} a good tube float?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": (
                    "Some listed sections have unresolved access. Do not plan those trips until the specific access issue is resolved." if access_holds else "Tubes lag the current (we use a 0.72× speed multiplier). "
                    + (
                        "This listing includes Class III or harder water — rafts and experienced paddlers, not tubes."
                        if any("III" in s["difficulty"] or "IV" in s["difficulty"] for s in river["sections"])
                        else "On Class I–II stretches tubes can work at moderate flows; skip high water and always wear a PFD."
                    )
                ),
            },
        },
    ])

    related = _related(rivers, river)
    related_html = "".join(
        f'<li><a href="/rivers/{esc(r["id"])}">{esc(r["name"])}</a> — {esc(r["blurb"])}</li>'
        for r in related
    )

    place = {
        "@context": "https://schema.org",
        "@type": ["TouristAttraction", "Place"],
        "name": f"{river['name']} river float",
        "description": river["blurb"],
        "url": SITE + path,
        "touristType": "River floating",
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": river["lat"],
            "longitude": river["lon"],
        },
        "address": {
            "@type": "PostalAddress",
            "addressRegion": st["code"],
            "addressCountry": "US",
        },
        "containedInPlace": {"@type": "State", "name": st["name"]},
    }
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq_entities}
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": f"{st['name']} rivers", "item": SITE + f"/{st['slug']}"},
            {"@type": "ListItem", "position": 3, "name": river["name"], "item": SITE + path},
        ],
    }

    faq_html = []
    for q in faq_entities:
        faq_html.append(f"""
        <details class="faq-item">
          <summary>{esc(q['name'])}</summary>
          <p>{esc(q['acceptedAnswer']['text'])}</p>
        </details>""")

    multi = (
        "<p>This is a multi-day wilderness float. Plan shuttles, permits, and camps — the calculator shows total hours on the water, not a same-day take-out.</p>"
        if river["multiDay"] or any(section.get("multiDay") for section in river["sections"])
        else ""
    )
    permit = ""
    if st.get("permitNotice"):
        permit = (
            f'<p class="permit-notice">{esc(st["permitNotice"])} '
            f'<a href="{esc(st["permitUrl"])}" target="_blank" rel="noopener">Check current permit rules</a>.</p>'
        )
    correction_url = "/feedback.html?" + urlencode({"riverId": river["id"], "type": "correction"})
    if all_held:
        timing_intro = '<p class="model-note">The listed routes need access review before they can be used for trip planning. Daylight and any available agency flow remain visible for context; trip estimates are withheld.</p>'
        timing_table_note = 'All listed routes are under access review.'
    elif not supports_live_timing(river):
        timing_intro = '<p>Live estimate unavailable. Reviewed access information, daylight and published guide times remain available. Guide times retain their original conditions and are not adjusted for today’s flow, craft, fishing stops or launch time.</p>'
        if river.get('timing', {}).get('note'):
            timing_intro += f'<p class="model-note">{esc(river["timing"]["note"])}</p>'
        timing_table_note = 'The table shows whether a live estimate is available and any published guide times.'
    else:
        timing_intro = f'<p>Float ETA estimates travel time from live discharge at <strong>{esc(flow_label(river))}</strong> ({esc(flow_name(river))}). At a reference <strong>{int(river["refFlowCfs"]):,} cfs</strong>, the model uses a raft speed of <strong>{river["refSpeedMph"]} mph</strong>. Craft and fishing stops change the estimate. Stopping to fish adds 25 minutes per river mile.</p>'
        timing_table_note = 'Times in the table are reference-flow raft estimates.'
        if 'timing' not in river:
            timing_intro += '<p class="model-note">This reference-speed model has not been validated against a published set of trip measurements. Use it as rough planning guidance and allow extra time.</p>'

    coverage_intro = (f'This listing has {len(river["sections"])} sections; {access_holds} have unresolved access or route details. Treat their mileages as unverified.'
                      if access_holds else f'The {esc(river["name"])} listing has {len(river["sections"])} access-to-access stretches: <strong>{esc(distance_label)}</strong> ({esc(", ".join(diffs))}).')
    if all_held:
        desc = f'{river["name"]} access and route review, available agency flow and daylight. Trip estimates are withheld until the listed access issues are resolved.'
    gauge_link = (f' Gauge page: <a href="{esc(flow_url(river))}" target="_blank" rel="noopener">{esc(flow_label(river))}</a>.' if flow_url(river) else '')
    gauge_context = river.get('gaugeContext')
    gauge_note = (f'<p class="model-note">{esc(gauge_context["note"])} '
                  f'<a href="{esc(gauge_context["sourceUrl"])}" target="_blank" rel="noopener">{esc(gauge_context["sourceName"])}</a> · '
                  f'Source checked {esc(gauge_context["checkedOn"])}.</p>') if gauge_context else ''
    return (
        _head(title, desc, path, json_ld=[_org_schema(), place, faq, crumbs], geo=st)
        + _nav(st["slug"])
        + f"""
    <div class="hero-content">
      <nav class="crumbs" aria-label="Breadcrumb">
        <a href="/">Home</a> / <a href="/{st['slug']}">{esc(st['name'])} rivers</a> / {esc(river['name'])}
      </nav>
      <h1>{esc(river['name'])} float time</h1>
      <p class="hero-sub">{esc(river['blurb'])}</p>
      <p class="coming-soon-pill">{esc(st['name'])} · {esc(flow_label(river))} · {len(river['sections'])} stretch{'es' if len(river['sections']) != 1 else ''}</p>
    </div>
    <div class="hero-wave" aria-hidden="true">
      <svg viewBox="0 0 1440 90" preserveAspectRatio="none"><path d="M0,40 C240,90 480,0 720,35 C960,70 1200,10 1440,45 L1440,90 L0,90 Z" fill="var(--bg)"/></svg>
    </div>
  </header>
  <main id="main" class="section river-page">
    {timing_intro}
    {multi}
    {permit}
    <p>{coverage_intro} {timing_table_note} Open the <a href="/?river={esc(river['id'])}#calculator">river dashboard</a>
      for today's CFS, daylight, and available weather and water-temperature readings.</p>

    <p class="river-cta">
      <a class="btn-primary" href="/?river={esc(river['id'])}#calculator">Open {esc(river['name'])} dashboard</a>
    </p>

    <h2>Float stretches on the {esc(river['name'])}</h2>
    <div class="table-wrap">
      <table class="stretch-table">
        <thead>
          <tr>
            <th>Put-in → take-out</th>
            <th>Miles</th>
            <th>Difficulty</th>
            <th>Float-time guidance</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </div>

    <h2>Access, maps, and shuttle planning</h2>
    <p>Open the access links before leaving service and confirm that roads, ramps, and parking are open. Map searches are starting points; signs and current agency notices control on the ground.</p>
    <div class="access-guide-list">{''.join(access_cards)}</div>

    <h2>Flow and trip planning</h2>
    <p>{esc(flow_description(river))}</p>
    {gauge_note}
    <p>Flow readings describe the gauge, and do not by themselves establish a trip duration.
      Always scout, wear a PFD, and check
      <a href="{esc(st['agencyUrl'])}" target="_blank" rel="noopener">{esc(st['agency'])}</a>
      for closures.{gauge_link}</p>

    <h2>Common questions</h2>
    <div class="faq-list">
      {''.join(faq_html)}
    </div>

    <h2>Nearby {esc(st['name'])} floats</h2>
    <ul class="related-rivers">
      {related_html}
    </ul>

    <aside class="site-steward">
      <h2>Who runs Float ETA?</h2>
      <p>Float ETA is an independent river-planning project. River details are assembled from public agency information and corrections from people who use these stretches. Estimates are reviewed as the catalog grows, but access and conditions can change faster than this site.</p>
      <p><a href="{esc(correction_url)}">Report a correction for {esc(river['name'])}</a> or read <a href="/about.html">how Float ETA works</a>.</p>
    </aside>
  </main>
"""
        + _footer()
    )


def not_found_html():
    title = "Page not found | Float ETA"
    desc = f"That page is not on Float ETA. Browse {_state_names()} river float times or open the live calculator."
    rivers = load_rivers()[:8]
    links = "".join(
        f'<li><a href="/rivers/{esc(r["id"])}">{esc(r["name"])}</a></li>' for r in rivers
    )
    return (
        _head(title, desc, "/")
        + _nav()
        + f"""
    <div class="hero-content">
      <h1>This page drifted off</h1>
      <p class="hero-sub">404 — that URL is not a Float ETA page. Try the calculator or a river directory.</p>
    </div>
    <div class="hero-wave" aria-hidden="true">
      <svg viewBox="0 0 1440 90" preserveAspectRatio="none"><path d="M0,40 C240,90 480,0 720,35 C960,70 1200,10 1440,45 L1440,90 L0,90 Z" fill="var(--bg)"/></svg>
    </div>
  </header>
  <main id="main" class="section">
    <p><a class="btn-primary" href="/#calculator">Open the float calculator</a>
      &nbsp; {" · ".join(f'<a href="/{m["slug"]}">{m["name"]}</a>' for m in STATES.values())}</p>
    <ul class="related-rivers">{links}</ul>
  </main>
"""
        + _footer()
    )
