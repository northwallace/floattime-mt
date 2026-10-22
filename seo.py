"""
Float ETA SEO pages — sitemap, state directories, and per-river landings.

River copy is read from public/catalog.json so the calculator and Google
see the same catalog. No extra dependencies.
"""

import json
import os
import re
import time

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
    return {s["id"]: {
        **s, "code": s["id"], "geo": "US-" + s["id"],
        "dirTitle": f'{s["name"]} Rivers to Float | Live USGS Gauges | Float ETA',
        "dirDesc": f'Explore {s["name"]} river floats, stretches, and USGS gauges.',
        "h1": f'{s["name"]} rivers to float',
        "intro": f'Find your next stretch in {s["name"]}. Check access and local conditions before launching.'
    } for s in catalog()["states"]}


STATES = _state_records()
STATE_BY_SLUG = {meta["slug"]: code for code, meta in STATES.items()}


def _state_names():
    names = [m["name"] for m in STATES.values()]
    return ", ".join(names[:-1]) + ", and " + names[-1] if len(names) > 2 else " and ".join(names)


def esc(text):
    import html
    return html.escape(str(text or ""), quote=True)


def load_rivers():
    return catalog()["rivers"]


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
    speed = max(river["refSpeedMph"], 0.8)
    return miles / speed


def _state_meta(river):
    return STATES.get(river.get("state") or "MT", STATES["MT"])


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
    image = SITE + "/og.png"
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
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Float ETA — live river float times from USGS flow">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{esc(image)}">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <link rel="manifest" href="/site.webmanifest">
  <link rel="sitemap" type="application/xml" href="/sitemap.xml">
  <link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/middle.css">
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
      <p>Live USGS streamflow turned into real float times — daylight, water temp, and community obstruction reports included.</p>
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


def state_html(code):
    meta = STATES[code]
    rivers = [r for r in load_rivers() if r.get("state") == code]
    sections = sum(len(r["sections"]) for r in rivers)
    path = f"/{meta['slug']}"
    title = meta["dirTitle"]
    desc = meta["dirDesc"]
    cards = []
    for river in rivers:
        miles = sum(s["miles"] for s in river["sections"])
        diffs = sorted({s["difficulty"] for s in river["sections"]})
        cards.append(f"""
        <article class="river-dir-card">
          <h2><a href="/rivers/{esc(river['id'])}">{esc(river['name'])}</a></h2>
          <p>{esc(river['blurb'])}</p>
          <p class="river-dir-meta">{len(river['sections'])} stretch{'es' if len(river['sections']) != 1 else ''}
            · {miles:g} river miles · {esc(', '.join(diffs))}</p>
          <a class="river-dir-link" href="/rivers/{esc(river['id'])}">Float times &amp; live CFS →</a>
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

    return (
        _head(title, desc, path, json_ld=[_org_schema(), item_list, crumbs], geo=meta)
        + _nav(meta["slug"])
        + f"""
    <div class="hero-content">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / {esc(meta['name'])} rivers</nav>
      <h1>{esc(meta['h1'])}</h1>
      <p class="hero-sub">{len(rivers)} rivers and {sections} stretches with live USGS gauges —
        {esc(meta['intro'])}</p>
    </div>
    <div class="hero-wave" aria-hidden="true">
      <svg viewBox="0 0 1440 90" preserveAspectRatio="none"><path d="M0,40 C240,90 480,0 720,35 C960,70 1200,10 1440,45 L1440,90 L0,90 Z" fill="var(--bg)"/></svg>
    </div>
  </header>
  <main id="main" class="section river-dir">
    <div class="section-head">
      <h2>Every Float ETA stretch in {esc(meta['name'])}</h2>
      <p>These are real put-in to take-out runs, not a generic state list. Times on each river page are typical raft times at a reference flow; the <a href="/#calculator">live calculator</a> scales them to today's CFS.
        Also live: {others}.</p>
    </div>
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
    miles = sum(s["miles"] for s in river["sections"])
    diffs = sorted({s["difficulty"] for s in river["sections"]})
    path = f"/rivers/{river['id']}"
    title = f"{river['name']} Float Time | {st['name']} | Float ETA"
    desc = (
        f"{river['blurb']} {len(river['sections'])} stretch"
        f"{'es' if len(river['sections']) != 1 else ''}, {miles:g} miles, "
        f"{', '.join(diffs)}. Live USGS {river['gauge']} flow and sunset take-out times."
    )
    if len(desc) > 165:
        desc = desc[:162].rsplit(" ", 1)[0] + "…"

    rows = []
    faq_entities = []
    for sec in river["sections"]:
        hours = _typical_hours(river, sec["miles"])
        label = f"{sec['putIn']} to {sec['takeOut']}"
        rows.append(f"""
        <tr>
          <td>{esc(sec['putIn'])} → {esc(sec['takeOut'])}</td>
          <td>{sec['miles']:g} mi</td>
          <td>{esc(sec['difficulty'])}</td>
          <td>~{_fmt_hours(hours)}</td>
          <td>{esc(sec['notes'])}</td>
        </tr>""")
        faq_entities.append({
            "@type": "Question",
            "name": f"How long does it take to float {label} on the {river['name']}?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": (
                    f"About {_fmt_hours(hours)} in a raft at a typical "
                    f"{int(river['refFlowCfs'])} cfs. Kayaks run a bit faster; "
                    f"tubes run slower. Add your own stop or fishing time in the planner. "
                    f"{sec['notes']}"
                ),
            },
        })

    faq_entities.extend([
        {
            "@type": "Question",
            "name": f"What USGS gauge is used for {river['name']} float times?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": (
                    f"Float ETA uses USGS gauge {river['gauge']} ({river['gaugeName']}) "
                    f"for live discharge. Speed is scaled from a reference "
                    f"{int(river['refFlowCfs'])} cfs drift of about {river['refSpeedMph']} mph."
                ),
            },
        },
        {
            "@type": "Question",
            "name": f"Is the {river['name']} a good tube float?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": (
                    "Tubes lag the current (we use a 0.72× speed multiplier). "
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
        "isAccessibleForFree": True,
        "publicAccess": True,
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
        if river["multiDay"]
        else ""
    )

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
      <p class="coming-soon-pill">{esc(st['name'])} · USGS {esc(river['gauge'])} · {len(river['sections'])} stretch{'es' if len(river['sections']) != 1 else ''}</p>
    </div>
    <div class="hero-wave" aria-hidden="true">
      <svg viewBox="0 0 1440 90" preserveAspectRatio="none"><path d="M0,40 C240,90 480,0 720,35 C960,70 1200,10 1440,45 L1440,90 L0,90 Z" fill="var(--bg)"/></svg>
    </div>
  </header>
  <main id="main" class="section river-page">
    <p>Float ETA estimates how long this float <em>actually</em> takes from live discharge
      at <strong>USGS {esc(river['gauge'])}</strong> ({esc(river['gaugeName'])}), not a
      guidebook average. At a typical <strong>{int(river['refFlowCfs']):,} cfs</strong>,
      a raft drifts about <strong>{river['refSpeedMph']} mph</strong> here. Higher flow
      speeds you up; skinny water slows you down. Kayaks run faster than the current,
      tubes slower. Add your own total time for stops and fishing.</p>
    {multi}
    <p>The {esc(river['name'])} listing covers <strong>{miles:g} river miles</strong> across
      {len(river['sections'])} access-to-access stretch{'es' if len(river['sections']) != 1 else ''}
      ({esc(', '.join(diffs))}). Times in the table are typical raft hours at that
      reference flow. Open the <a href="/?river={esc(river['id'])}#calculator">live calculator</a>
      for today's CFS, sunset take-out, water temperature, and rain/UV at the put-in.</p>

    <p class="river-cta">
      <a class="btn-primary" href="/?river={esc(river['id'])}#calculator">See today's {esc(river['name'])} float time</a>
    </p>

    <h2>Float stretches on the {esc(river['name'])}</h2>
    <div class="table-wrap">
      <table class="stretch-table">
        <thead>
          <tr>
            <th>Put-in → take-out</th>
            <th>Miles</th>
            <th>Difficulty</th>
            <th>Typical raft time</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </div>

    <h2>How we time this river</h2>
    <p>Speed scales with discharge using hydraulic geometry
      <span class="math">v ∝ Q<sup>0.34</sup></span>, calibrated to this gauge.
      That is why a 1,000 cfs afternoon is a different day than 3,000 cfs runoff.
      Always scout, wear a PFD, and check
      <a href="{esc(st['agencyUrl'])}" target="_blank" rel="noopener">{esc(st['agency'])}</a>
      for closures. Gauge page:
      <a href="https://waterdata.usgs.gov/monitoring-location/{esc(river['gauge'])}/" target="_blank" rel="noopener">USGS {esc(river['gauge'])}</a>.</p>

    <h2>Common questions</h2>
    <div class="faq-list">
      {''.join(faq_html)}
    </div>

    <h2>Nearby {esc(st['name'])} floats</h2>
    <ul class="related-rivers">
      {related_html}
    </ul>
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
