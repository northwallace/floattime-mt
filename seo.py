"""
FloatETA SEO pages — sitemap, Montana directory, and per-river landings.

River copy is read from public/rivers.js so the calculator and Google
see the same catalog. No extra dependencies.
"""

import json
import os
import re
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(ROOT, "public")
SITE = os.environ.get("SITE_URL", "https://floateta.com").rstrip("/")
ADSENSE = "ca-pub-1358970586107841"


def esc(text):
    return (
        str(text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _split_objects(blob):
    objs, i, n = [], 0, len(blob)
    while i < n:
        if blob[i] == "{":
            depth = 0
            start = i
            for j in range(i, n):
                if blob[j] == "{":
                    depth += 1
                elif blob[j] == "}":
                    depth -= 1
                    if depth == 0:
                        objs.append(blob[start : j + 1])
                        i = j + 1
                        break
            else:
                break
        else:
            i += 1
    return objs


def _str_field(blob, key):
    m = re.search(rf'{re.escape(key)}:\s*"((?:\\.|[^"\\])*)"', blob)
    return m.group(1).replace('\\"', '"').replace("\\n", "\n") if m else ""


def _num_field(blob, key):
    m = re.search(rf"{re.escape(key)}:\s*(-?[\d.]+)", blob)
    return float(m.group(1)) if m else 0.0


def _bool_field(blob, key):
    return bool(re.search(rf"{re.escape(key)}:\s*true", blob))


def load_rivers():
    text = open(os.path.join(PUBLIC, "rivers.js"), encoding="utf-8").read()
    start = text.find("const RIVERS = [")
    end = text.find("\nconst CRAFT")
    if start < 0 or end < 0:
        return []
    rivers = []
    for obj in _split_objects(text[start:end]):
        head, _, rest = obj.partition("sections:")
        sections = []
        for sec in _split_objects(rest):
            sections.append({
                "id": _str_field(sec, "id"),
                "putIn": _str_field(sec, "putIn"),
                "takeOut": _str_field(sec, "takeOut"),
                "miles": _num_field(sec, "miles"),
                "difficulty": _str_field(sec, "difficulty"),
                "notes": _str_field(sec, "notes"),
            })
        rivers.append({
            "id": _str_field(head, "id"),
            "name": _str_field(head, "name"),
            "gauge": _str_field(head, "gauge"),
            "gaugeName": _str_field(head, "gaugeName"),
            "lat": _num_field(head, "lat"),
            "lon": _num_field(head, "lon"),
            "refFlowCfs": _num_field(head, "refFlowCfs"),
            "refSpeedMph": _num_field(head, "refSpeedMph"),
            "blurb": _str_field(head, "blurb"),
            "multiDay": _bool_field(head, "multiDay"),
            "sections": sections,
        })
    return [r for r in rivers if r["id"]]


def find_river(slug):
    slug = (slug or "").replace(".html", "").strip("/")
    return next((r for r in load_rivers() if r["id"] == slug), None)


def _fmt_hours(hours):
    if hours >= 24:
        return f"{hours / 24:.1f} days"
    h = int(hours)
    m = int(round((hours - h) * 60))
    if h == 0:
        return f"{m} min"
    if m == 0:
        return f"{h} hr"
    return f"{h} hr {m} min"


def _typical_hours(river, miles):
    speed = max(river["refSpeedMph"], 0.8)
    return miles / speed


def _related(rivers, current, n=4):
    stem = current["id"].split("-")[0]
    same = [r for r in rivers if r["id"] != current["id"] and r["id"].split("-")[0] == stem]
    others = [r for r in rivers if r["id"] != current["id"] and r not in same]
    return (same + others)[:n]


def _lastmod():
    path = os.path.join(PUBLIC, "rivers.js")
    return time.strftime("%Y-%m-%d", time.gmtime(os.path.getmtime(path)))


def _head(title, description, path, extra="", json_ld=None):
    url = SITE + path
    image = SITE + "/og.svg"
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
  <meta name="author" content="FloatETA">
  <meta name="theme-color" content="#0e1a14">
  <meta name="geo.region" content="US-MT">
  <meta name="geo.placename" content="Montana">
  <link rel="canonical" href="{esc(url)}">
  <link rel="alternate" hreflang="en-US" href="{esc(url)}">
  <link rel="alternate" hreflang="x-default" href="{esc(url)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="FloatETA">
  <meta property="og:locale" content="en_US">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{esc(url)}">
  <meta property="og:image" content="{esc(image)}">
  <meta property="og:image:alt" content="FloatETA — Montana river float times from live USGS flow">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{esc(image)}">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="manifest" href="/site.webmanifest">
  <link rel="sitemap" type="application/xml" href="/sitemap.xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/styles.css">
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE}" crossorigin="anonymous"></script>
  {extra}
  {"".join(blocks)}
</head>
"""


def _nav(active=""):
    def item(href, label, key):
        cls = ' class="is-active"' if active == key else ""
        return f'<a href="{href}"{cls}>{label}</a>'

    return f"""  <a class="skip-link" href="#main">Skip to content</a>
  <header class="hero hero-legal">
    <nav class="nav" aria-label="Primary">
      <a class="brand" href="/">🛶 Float<span>ETA</span></a>
      <div class="nav-links">
        {item("/", "Home", "home")}
        {item("/montana", "Montana rivers", "montana")}
        {item("/#calculator", "Float calculator", "calc")}
        {item("/contact.html", "Contact", "contact")}
      </div>
    </nav>
"""


def _footer():
    year = time.strftime("%Y")
    return f"""  <footer class="footer">
    <div class="footer-inner">
      <a class="brand" href="/">🛶 Float<span>ETA</span></a>
      <p>Live USGS streamflow turned into real Montana float times — daylight, water temp, and community obstruction reports included.</p>
      <p class="footer-links">
        <a href="/">Home</a> ·
        <a href="/montana">Montana rivers</a> ·
        <a href="/#calculator">Float calculator</a> ·
        <a href="/privacy.html">Privacy Policy</a> ·
        <a href="/contact.html">Contact</a>
      </p>
      <p class="copyright">© {year} FloatETA · <a href="{SITE}">{SITE.replace("https://", "")}</a></p>
    </div>
  </footer>
</body>
</html>
"""


def _org_schema():
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "FloatETA",
        "url": SITE + "/",
        "logo": SITE + "/favicon.svg",
        "description": "Live river float-time estimates from USGS streamflow for Montana, with more states coming.",
        "areaServed": {"@type": "State", "name": "Montana"},
        "sameAs": [SITE + "/"],
    }


def sitemap_xml():
    lastmod = _lastmod()
    rivers = load_rivers()
    urls = [
        ("/", "1.0", "daily"),
        ("/montana", "0.9", "weekly"),
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


def montana_html():
    rivers = load_rivers()
    sections = sum(len(r["sections"]) for r in rivers)
    title = "Montana Rivers to Float | 24 Live Gauges & 54 Stretches | FloatETA"
    desc = (
        "Directory of Montana river floats with live USGS flow: Madison, Yellowstone, "
        "Gallatin, Big Hole, Blackfoot, Clark Fork, Bitterroot, and more. See miles, "
        "difficulty, and typical raft time for every stretch."
    )
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
        "name": "Montana rivers to float",
        "url": SITE + "/montana",
        "description": desc,
        "isPartOf": {"@type": "WebSite", "name": "FloatETA", "url": SITE + "/"},
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
            {"@type": "ListItem", "position": 2, "name": "Montana rivers", "item": SITE + "/montana"},
        ],
    }

    return (
        _head(title, desc, "/montana", json_ld=[_org_schema(), item_list, crumbs])
        + _nav("montana")
        + f"""
    <div class="hero-content">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / Montana rivers</nav>
      <h1>Montana rivers to float</h1>
      <p class="hero-sub">{len(rivers)} rivers and {sections} stretches with live USGS gauges —
        pick a river for typical raft time, access points, and today's calculator.</p>
    </div>
    <div class="hero-wave" aria-hidden="true">
      <svg viewBox="0 0 1440 90" preserveAspectRatio="none"><path d="M0,40 C240,90 480,0 720,35 C960,70 1200,10 1440,45 L1440,90 L0,90 Z" fill="var(--bg)"/></svg>
    </div>
  </header>
  <main id="main" class="section river-dir">
    <div class="section-head">
      <h2>Every FloatETA stretch in Montana</h2>
      <p>These are real put-in to take-out runs, not a generic state list. Times on each river page are typical raft times at a reference flow; the <a href="/#calculator">live calculator</a> scales them to today's CFS.</p>
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
    miles = sum(s["miles"] for s in river["sections"])
    diffs = sorted({s["difficulty"] for s in river["sections"]})
    path = f"/rivers/{river['id']}"
    title = f"{river['name']} Float Time | Live CFS & Take-Out ETA | FloatETA"
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
                    f"tubes run slower. Stopping to fish adds about 35 minutes per mile. "
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
                    f"FloatETA uses USGS gauge {river['gauge']} ({river['gaugeName']}) "
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
            "addressRegion": "MT",
            "addressCountry": "US",
        },
        "containedInPlace": {"@type": "State", "name": "Montana"},
    }
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq_entities}
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Montana rivers", "item": SITE + "/montana"},
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
        _head(title, desc, path, json_ld=[_org_schema(), place, faq, crumbs])
        + _nav()
        + f"""
    <div class="hero-content">
      <nav class="crumbs" aria-label="Breadcrumb">
        <a href="/">Home</a> / <a href="/montana">Montana rivers</a> / {esc(river['name'])}
      </nav>
      <h1>{esc(river['name'])} float time</h1>
      <p class="hero-sub">{esc(river['blurb'])}</p>
      <p class="coming-soon-pill">Montana · USGS {esc(river['gauge'])} · {len(river['sections'])} stretch{'es' if len(river['sections']) != 1 else ''}</p>
    </div>
    <div class="hero-wave" aria-hidden="true">
      <svg viewBox="0 0 1440 90" preserveAspectRatio="none"><path d="M0,40 C240,90 480,0 720,35 C960,70 1200,10 1440,45 L1440,90 L0,90 Z" fill="var(--bg)"/></svg>
    </div>
  </header>
  <main id="main" class="section river-page">
    <p>FloatETA estimates how long this float <em>actually</em> takes from live discharge
      at <strong>USGS {esc(river['gauge'])}</strong> ({esc(river['gaugeName'])}), not a
      guidebook average. At a typical <strong>{int(river['refFlowCfs']):,} cfs</strong>,
      a raft drifts about <strong>{river['refSpeedMph']} mph</strong> here. Higher flow
      speeds you up; skinny water slows you down. Kayaks run faster than the current,
      tubes slower. Optional fishing adds 35 minutes per mile.</p>
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
      <a href="https://fwp.mt.gov/activities/boating" target="_blank" rel="noopener">Montana FWP boating</a>
      for closures. Gauge page:
      <a href="https://waterdata.usgs.gov/monitoring-location/{esc(river['gauge'])}/" target="_blank" rel="noopener">USGS {esc(river['gauge'])}</a>.</p>

    <h2>Common questions</h2>
    <div class="faq-list">
      {''.join(faq_html)}
    </div>

    <h2>Nearby Montana floats</h2>
    <ul class="related-rivers">
      {related_html}
    </ul>
  </main>
"""
        + _footer()
    )


def not_found_html():
    title = "Page not found | FloatETA"
    desc = "That page is not on FloatETA. Browse Montana river float times or open the live calculator."
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
      <p class="hero-sub">404 — that URL is not a FloatETA page. Try the calculator or a Montana river.</p>
    </div>
    <div class="hero-wave" aria-hidden="true">
      <svg viewBox="0 0 1440 90" preserveAspectRatio="none"><path d="M0,40 C240,90 480,0 720,35 C960,70 1200,10 1440,45 L1440,90 L0,90 Z" fill="var(--bg)"/></svg>
    </div>
  </header>
  <main id="main" class="section">
    <p><a class="btn-primary" href="/#calculator">Open the float calculator</a>
      &nbsp; <a href="/montana">All Montana rivers</a></p>
    <ul class="related-rivers">{links}</ul>
  </main>
"""
        + _footer()
    )
