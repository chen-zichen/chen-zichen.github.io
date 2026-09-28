#!/usr/bin/env python3
"""Re-render site/publications/index.html and site/llms-full.txt from pubs.json.

In index.html this rewrites only:
  - the <main> list and the stamp line (#st-n)             -> markup/classes identical to the hand-written page
  - <!-- seo:start --> ... <!-- seo:end --> after <title>  -> description / canonical / robots / icons / Open Graph
  - <!-- ld:start -->  ... <!-- ld:end -->  before </head> -> JSON-LD (CollectionPage, BreadcrumbList, ItemList of ScholarlyArticle)
Everything else (styles, header, footer, scripts) is left byte-for-byte alone. Re-running is idempotent.
The visible page never changes because of the SEO blocks: they are <meta>/<link>/<script type="application/ld+json"> only."""
import json, re
from html import escape
from itertools import groupby
from pathlib import Path
from urllib.parse import urlparse

SITE = Path(__file__).resolve().parents[2] / "site"
D = SITE / "publications"
pubs = json.loads((D / "pubs.json").read_text())
page = (D / "index.html").read_text()

ME = "Zichen Chen"

# ---------------------------------------------------------------- site facts (shared with the homepage; keep in sync)
ORIGIN = "https://chen-zichen.github.io"
HOME = ORIGIN + "/"
URL = ORIGIN + "/publications/"
PERSON_ID = HOME + "#person"
WEBSITE_ID = HOME + "#website"
OG_IMAGE = ORIGIN + "/assets/img/og.jpg"   # 1200x630 JPEG (~150 KB; small enough for WhatsApp previews), built with the homepage
OG_IMAGE_TYPE = "image/jpeg"
THEME = "#DDD7CB"
SCHOLAR = "https://scholar.google.com/citations?user=X4goIzYAAAAJ"
PROFILES = [
    ("Google Scholar", SCHOLAR),
    ("X", "https://x.com/my_cat_can_code"),
    ("LinkedIn", "https://www.linkedin.com/in/chenzichen"),
    ("GitHub", "https://github.com/chen-zichen"),
]
# same @id as the homepage graph's Bake AI node, so the two pages describe one organisation
BAKE_AI = {"@type": "Organization", "@id": HOME + "#bake-ai", "name": "Bake AI", "url": "https://bakeai.inc"}
TITLE = "Publications — Zichen Chen"

# ---------------------------------------------------------------- visible list (unchanged)
def nb(s):  # names never break inside
    return escape(s, quote=False).replace(" ", "&nbsp;")

def author(name, eq):
    s = nb(name) + ('<span class="m">*</span>' if name in eq else "")
    return f"<b>{s}</b>" if name == ME else s

def link(href, text):
    return f'<a href="{escape(href)}" target="_blank" rel="noopener">{text}</a>'

def entry(p):
    L = ['        <li class="e">']
    t = escape(p["title"], quote=False)
    L.append(f'          <p class="t">{link(p["url"], t) if p.get("url") else t}</p>')
    L.append('          <p class="a">' + ", ".join(author(a, p["equal_contrib"]) for a in p["authors"]) + "</p>")
    v = '<span class="sep">·</span>'.join(escape(x.strip(), quote=False) for x in p["venue_display"].split(" · "))
    for k in ("page", "code"):
        if p.get(k):
            v += f'<span class="lk">[{link(p[k], k)}]</span>'
    L.append(f'          <p class="v">{v}</p>')
    if p.get("notes"):
        L.append('          <p class="note">' + "".join(f"<span>{escape(n, quote=False)}</span>" for n in p["notes"]) + "</p>")
    L.append("        </li>")
    return "\n".join(L)

years = [(y, list(g)) for y, g in groupby(pubs, key=lambda p: p["group_year"])]
secs = []
for y, g in years:
    body = "\n".join(entry(p) for p in g)
    secs.append(
        f'    <section class="yr" aria-labelledby="y{y}">\n'
        f'      <h2 class="y" id="y{y}"><span>{y}</span></h2>\n'
        f"      <ol>\n{body}\n      </ol>\n"
        f"    </section>"
    )
main_inner = "\n\n" + "\n\n".join(secs) + "\n\n  "

m = re.search(r'(<main aria-label="Publications, newest first">)(.*?)(</main>)', page, re.S)
assert m
page = page[: m.start(2)] + main_inner + page[m.end(2):]

STAMP_LINE = 'doing research<br class="mb"> for fun'   # the stamp's middle line; br.mb breaks only on phones
page, k = re.subn(r'(<span id="st-n">).*?(</span>)', lambda m: m.group(1) + STAMP_LINE + m.group(2), page, flags=re.S)
assert k == 1
n = len(pubs)

# ---------------------------------------------------------------- derived facts (so the metadata never goes stale)
def venues(p):
    return [v.strip() for v in p["venue_display"].split(" · ")]

def is_preprint(v):
    return v.lower() == "arxiv preprint"

def arxiv_url(aid):
    return f"https://arxiv.org/abs/{aid}"

def clean_note(s):  # "innovation award." -> "innovation award"
    return s.strip().rstrip(".")

def date_published(p):
    """pubs.json dates are exact (date_precision "day") when they come from arXiv or a proceedings page; curated
    ones marked date_precision "year" in build_pubs.py only place the entry in the list, so publish just the year."""
    return p["date"][:4] if p.get("date_precision") == "year" else p["date"]

# Topics named in the description are kept only while some title in pubs.json still supports them.
TOPICS = [
    ("AI agents", r"\bagent"),
    ("auto research", r"auto research|autonomous research"),
    ("benchmarks", r"benchmark|evaluat"),
    ("trustworthy AI", r"\brisk|oversight|reliable|explain"),
]
titles = " ".join(p["title"] for p in pubs).lower()
topics = [t for t, rx in TOPICS if re.search(rx, titles)]

# Headline venues, in this order, kept only while pubs.json has a paper there.
VENUES = ["ICLR", "NeurIPS", "ACL", "COLM", "EMNLP", "NAACL", "IJCAI", "AAAI"]
all_venues = [v for p in pubs for v in venues(p)]
top_venues = [v for v in VENUES if any(re.match(rf"{re.escape(v)}\b", x) for x in all_venues)][:4]   # 4 keeps the description ~160 chars

def series(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]

DESCRIPTION = (
    f"{n} publications by Zichen Chen, co-founder and CEO of Bake AI, on {series(topics)}"
    f" — at {', '.join(top_venues)} and more."
)

# ---------------------------------------------------------------- <head>: meta block
def meta(attr, key, val):
    return f'<meta {attr}="{key}" content="{escape(val)}">'

# same alt text as the homepage's og:image:alt (one image, one description)
OG_ALT = ("Zichen Chen — co-founder & CEO, Bake AI · auto research."
          " Two prints of an empty armchair on a grassy hill under a blue sky, on greige paper.")
SEO = "\n".join([
    "<!-- seo:start (generated by tools/pubs/render_pubs.py; edit there) -->",
    meta("name", "description", DESCRIPTION),
    meta("name", "author", ME),
    meta("name", "robots", "index, follow, max-snippet:-1, max-image-preview:large"),
    f'<link rel="canonical" href="{URL}">',
    '<link rel="alternate" type="text/markdown" href="/llms-full.txt" title="Zichen Chen — Publications (Markdown)">',
    meta("name", "theme-color", THEME),
    '<link rel="icon" href="/favicon.ico" sizes="32x32">',
    '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
    '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
    '<link rel="manifest" href="/site.webmanifest">',
    meta("property", "og:type", "website"),
    meta("property", "og:site_name", ME),
    meta("property", "og:locale", "en_US"),
    meta("property", "og:title", TITLE),
    meta("property", "og:description", DESCRIPTION),
    meta("property", "og:url", URL),
    meta("property", "og:image", OG_IMAGE),
    meta("property", "og:image:type", OG_IMAGE_TYPE),
    meta("property", "og:image:width", "1200"),
    meta("property", "og:image:height", "630"),
    meta("property", "og:image:alt", OG_ALT),
    meta("name", "twitter:card", "summary_large_image"),
    meta("name", "twitter:site", "@my_cat_can_code"),
    meta("name", "twitter:creator", "@my_cat_can_code"),
    "<!-- seo:end -->",
])

if "<!-- seo:start" in page:
    page, k = re.subn(r"<!-- seo:start.*?<!-- seo:end -->", lambda _: SEO, page, flags=re.S)
    assert k == 1
else:  # first run: the SEO block replaces the old hand-written description
    page, k = re.subn(r'<meta name="description"[^>]*>\n', "", page)
    assert k <= 1
    page, k = re.subn(r"(<title>[^<]*</title>\n)", lambda m: m.group(1) + SEO + "\n", page)
    assert k == 1

# ---------------------------------------------------------------- <head>: JSON-LD
def person(name):
    if name == ME:
        return {"@type": "Person", "@id": PERSON_ID, "name": name}
    if name.endswith(" Team"):   # "Epi Team": a group credit, not a person
        return {"@type": "Organization", "name": name}
    return {"@type": "Person", "name": name}

def article(p):
    a = {
        "@type": "ScholarlyArticle",
        "name": p["title"],
        "headline": p["title"],
        "author": [person(x) for x in p["authors"]],
        "datePublished": date_published(p),
        "url": p["url"],
    }
    aid = p.get("arxiv_id")
    if aid:
        if arxiv_url(aid) != p["url"]:
            a["sameAs"] = arxiv_url(aid)
        a["identifier"] = {"@type": "PropertyValue", "propertyID": "arXiv", "value": aid}
    # venue(s): schema.org's `publication` takes a PublicationEvent; one per venue shown on the page
    ev = [{"@type": "PublicationEvent", "name": v} for v in venues(p)]
    a["publication"] = ev[0] if len(ev) == 1 else ev
    if all(is_preprint(v) for v in venues(p)):
        a["creativeWorkStatus"] = "Preprint"
    if urlparse(p["url"]).netloc.endswith("bakeai.inc"):
        a["publisher"] = BAKE_AI
    rel = []
    if p.get("page"):
        rel.append({"@type": "WebPage", "name": "Project page", "url": p["page"]})
    if p.get("code"):
        rel.append({"@type": "SoftwareSourceCode", "name": "Code", "url": p["code"], "codeRepository": p["code"]})
    if rel:
        a["subjectOf"] = rel[0] if len(rel) == 1 else rel
    awards = [clean_note(x) for x in p.get("notes", []) if "award" in x.lower()]
    if awards:
        a["award"] = awards[0][:1].upper() + awards[0][1:] if len(awards) == 1 else awards
    return a

LD = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "CollectionPage",
            "@id": URL + "#webpage",
            "url": URL,
            "name": TITLE,
            "description": DESCRIPTION,
            "inLanguage": "en",
            "isPartOf": {"@type": "WebSite", "@id": WEBSITE_ID, "url": HOME},
            "about": {"@id": PERSON_ID},
            "author": {"@id": PERSON_ID},
            "breadcrumb": {"@id": URL + "#breadcrumb"},
            "mainEntity": {"@id": URL + "#list"},
        },
        {
            "@type": "Person",
            "@id": PERSON_ID,
            "name": ME,
            "url": HOME,
            "jobTitle": "Co-founder and CEO",
            "worksFor": BAKE_AI,
            "sameAs": [u for _, u in PROFILES],
        },
        {
            "@type": "BreadcrumbList",
            "@id": URL + "#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": ME, "item": HOME},
                {"@type": "ListItem", "position": 2, "name": "Publications", "item": URL},
            ],
        },
        {
            "@type": "ItemList",
            "@id": URL + "#list",
            "name": "Publications by Zichen Chen",
            "itemListOrder": "https://schema.org/ItemListOrderDescending",
            "numberOfItems": n,
            "itemListElement": [
                {"@type": "ListItem", "position": i, "item": article(p)} for i, p in enumerate(pubs, 1)
            ],
        },
    ],
}

def ld_json(obj):
    """Compact JSON, one @graph node (and one list item) per line: small, but still readable in a diff."""
    c = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    lines = []
    for node in obj["@graph"]:
        items = node.get("itemListElement") if node.get("@type") == "ItemList" else None
        if items is None:
            lines.append(c(node))
        else:
            head = c({k: v for k, v in node.items() if k != "itemListElement"})[:-1]
            lines.append(head + ',"itemListElement":[\n' + ",\n".join(c(x) for x in items) + "\n]}")
    s = '{"@context":' + c(obj["@context"]) + ',"@graph":[\n' + ",\n".join(lines) + "\n]}"
    # "<", ">" and "&" only ever occur inside JSON strings; \u-escaping them keeps "</script>" and "<!--" inert
    return s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

LD_BLOCK = (
    "<!-- ld:start (generated by tools/pubs/render_pubs.py from pubs.json; edit there) -->\n"
    '<script type="application/ld+json">\n' + ld_json(LD) + "\n</script>\n"
    "<!-- ld:end -->"
)
if "<!-- ld:start" in page:
    page, k = re.subn(r"<!-- ld:start.*?<!-- ld:end -->", lambda _: LD_BLOCK, page, flags=re.S)
else:
    page, k = re.subn(r"(</head>)", lambda m: LD_BLOCK + "\n" + m.group(1), page)
assert k == 1

(D / "index.html").write_text(page)

# ---------------------------------------------------------------- llms-full.txt (Markdown for LLMs / AI search)
def md(s):  # escape Markdown emphasis/link syntax in plain text
    return re.sub(r"([\\`*_\[\]])", r"\\\1", s)

def md_author(name, eq):
    s = md(name) + ("\\*" if name in eq else "")
    return f"**{s}**" if name == ME else s

L = [
    "# Zichen Chen — Publications",
    "",
    "> Zichen Chen is co-founder and CEO of Bake AI (https://bakeai.inc), working full-time on auto research,"
    " including AutoLab (https://autolab.moe), the Visual Aesthetic Benchmark (https://vab.bakelab.ai) and"
    " Épi (https://bakeai.inc/research/articles/epi/). Zichen Chen holds a Ph.D. in Computer Science from the"
    " University of California, Santa Barbara (with Prof. Misha Sra) and an M.S. (Research) in Computer Science"
    " from Nanyang Technological University, Singapore. Previously, Zichen Chen worked under Prof. Alex \"Sandy\""
    " Pentland's guidance at Stanford (Stanford HAI / Digital Economy Lab) and spent time at Google Research.",
    "",
    "Website: " + HOME + "  ",
    "Profiles: " + " · ".join(f"[{k}]({u})" for k, u in PROFILES),
    "",
    f"This is the full list of {n} publications from {URL}, grouped by year, newest first"
    f" (also on [Google Scholar]({SCHOLAR})). Zichen Chen's name is in bold; \\* marks equal contribution.",
]
for y, g in years:
    L += ["", f"## {y}"]
    for p in g:
        L += ["", f"### [{md(p['title'])}]({p['url']})", ""]
        L.append("- Authors: " + ", ".join(md_author(a, p["equal_contrib"]) for a in p["authors"]))
        L.append("- Venue: " + md(p["venue_display"]))
        links = []
        aid = p.get("arxiv_id")
        if aid:
            links.append(f"[arXiv:{aid}]({arxiv_url(aid)})")
        for k in ("page", "code"):
            if p.get(k):
                links.append(f"[{k}]({p[k]})")
        if links:
            L.append("- Links: " + " · ".join(links))
        if p.get("notes"):
            L.append("- Notes: " + "; ".join(md(clean_note(x)) for x in p["notes"]))
(SITE / "llms-full.txt").write_text("\n".join(L) + "\n")

print("rendered", n, "entries in", len(secs), "years; stamp:", STAMP_LINE)
print("description:", len(DESCRIPTION), "chars:", DESCRIPTION)
