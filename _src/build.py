#!/usr/bin/env python3
"""Build the static site: one page per language, so search engines index each language on its own URL.

    python3 _src/build.py

Inputs (all in _src/):
  layout.html            shared <head>, header, footer
  pages/home.html        home page body           -> /, /zh/, /fr/, /pt/
  pages/hire.html        machinery-hire page body -> /machinery-hire/, /zh/machinery-hire/, ...
  partials/*.html        pieces used by several pages ({{include:name}})
  content.json           copy in zh + en  ({key: {zh, en, note?}})
  i18n/fr.json, pt.json  copy in fr / pt  ({key: text})
Outputs: the HTML pages above, 404.html, sitemap.xml, robots.txt.

Placeholders:
  {{t:key}} text · {{raw:key}} text that may contain <br> · {{attr:key}} attribute-escaped text
  {{pic:name|sizes|focal[|decor]}} <picture> (WebP srcset + JPEG fallback; alt = cap.<name>)
  {{fleet:name|key|focal|tag,tag}} hire card · {{thumb:name|key}} small fleet link
  {{gallery:name|classes,...}} · {{include:partial}} · {{selected:value}} · {{current:page}}
  plus page variables such as {{home}}, {{hirepage}}, {{canonical}}, {{jsonld}}, {{i18n}}.
"""
import datetime
import html
import json
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_src"
SITE = "https://www.sycamoreagritech.com"
LANGS = ["en", "zh", "fr", "pt"]
LANG_TAG = {"en": "en", "zh": "zh-Hans", "fr": "fr", "pt": "pt"}
OG_LOCALE = {"en": "en_GB", "zh": "zh_CN", "fr": "fr_FR", "pt": "pt_PT"}
LANG_NAME = {"en": "English", "zh": "中文", "fr": "Français", "pt": "Português"}
LANG_SHORT = {"en": "EN", "zh": "中文", "fr": "FR", "pt": "PT"}
PREFIX = {"en": "", "zh": "zh/", "fr": "fr/", "pt": "pt/"}
PAGES = [
    {"id": "home", "tpl": "pages/home.html", "slug": "", "title": "meta.title", "desc": "meta.desc", "select": None},
    {"id": "hire", "tpl": "pages/hire.html", "slug": "machinery-hire/", "title": "hp.title", "desc": "hp.desc", "select": "hire",
     "h1": "hp.h1", "faq": "faq", "faqCount": 5},
    {"id": "trade", "tpl": "pages/trade.html", "slug": "agricultural-products/", "title": "tp.title", "desc": "tp.desc", "select": "trade",
     "h1": "tp.h1", "faq": "tfaq", "faqCount": 6},
]

# ---------- copy ----------
content = json.loads((SRC / "content.json").read_text("utf-8"))
T = {k: {"zh": v["zh"], "en": v["en"]} for k, v in content.items()}
warnings = []
for lang in ("fr", "pt"):
    path = SRC / "i18n" / f"{lang}.json"
    data = json.loads(path.read_text("utf-8")) if path.exists() else {}
    for k in T:
        if not data.get(k):
            warnings.append(f"{lang}: missing '{k}' (using English)")
        T[k][lang] = data.get(k) or T[k]["en"]
    warnings += [f"{lang}: unknown key '{k}'" for k in data if k not in T]


PHONES = ["+265 999 947 228", "+265 999 441 333"]


def text(key, lang):
    if key not in T:
        sys.exit(f"Unknown content key: {key}")
    v = T[key][lang]
    for ph in PHONES:  # keep phone numbers on one line
        v = v.replace(ph, ph.replace(" ", "\u00a0"))
    return v


def esc(s):
    return html.escape(s, quote=False)


def attr(s):
    return html.escape(s, quote=True)


def url(lang, page):
    return f"{SITE}/{PREFIX[lang]}{page['slug']}"


def path(lang, page):
    return f"/{PREFIX[lang]}{page['slug']}"


# ---------- images ----------
_size = {}


def size(name, variant):
    key = (name, variant)
    if key not in _size:
        with Image.open(ROOT / "assets" / "img" / f"{name}-{variant}.webp") as im:
            _size[key] = im.size
    return _size[key]


def picture(name, sizes, focal, lang, decor=False):
    w, h = size(name, "lg")
    sw = size(name, "sm")[0]
    alt = "" if decor else attr(text(f"cap.{name}", lang))
    style = f' style="object-position: {focal}"' if focal else ""
    return (
        f'<picture><source type="image/webp" sizes="{sizes}" '
        f'srcset="/assets/img/{name}-sm.webp {sw}w, /assets/img/{name}-lg.webp {w}w">'
        f'<img src="/assets/img/{name}-lg.jpg" width="{w}" height="{h}" alt="{alt}" loading="lazy" decoding="async"{style}></picture>'
    )


# ---------- structured data ----------
def org(lang):
    return {
        "@type": "LocalBusiness",
        "@id": f"{SITE}/#business",
        "name": "Sycamore Agritech Limited",
        "alternateName": "盛楷农业科技有限公司",
        "legalName": "Sycamore Agritech Limited",
        "url": f"{SITE}/",
        "logo": f"{SITE}/assets/apple-touch-icon.png",
        "image": [f"{SITE}/assets/img/hero-pivot-wheat-lg.jpg", f"{SITE}/assets/og-image.jpg"],
        "description": text("meta.desc", lang),
        "telephone": "+265 999 947 228",
        "email": "reception@sycamoreagritech.com",
        "address": {"@type": "PostalAddress", "streetAddress": "Chitipi", "addressLocality": "Lilongwe", "addressCountry": "MW"},
        "areaServed": {"@type": "Country", "name": "Malawi"},
        "knowsLanguage": ["en", "zh", "fr", "pt"],
        "contactPoint": [
            {"@type": "ContactPoint", "contactType": "customer service", "telephone": "+265 999 947 228", "email": "reception@sycamoreagritech.com", "areaServed": "MW", "availableLanguage": ["English", "Chinese", "French", "Portuguese"]},
            {"@type": "ContactPoint", "contactType": "sales", "telephone": "+265 999 441 333", "email": "reception@sycamoreagritech.com", "areaServed": "MW"},
        ],
    }


def jsonld(lang, page):
    graph = [org(lang), {
        "@type": "WebPage", "@id": url(lang, page) + "#webpage", "url": url(lang, page),
        "name": text(page["title"], lang), "description": text(page["desc"], lang),
        "inLanguage": LANG_TAG[lang], "isPartOf": {"@id": f"{SITE}/#website"},
        "about": {"@id": f"{SITE}/#business"},
    }, {"@type": "WebSite", "@id": f"{SITE}/#website", "url": f"{SITE}/", "name": "Sycamore Agritech Limited",
        "inLanguage": [LANG_TAG[l] for l in LANGS], "publisher": {"@id": f"{SITE}/#business"}}]
    if page["id"] == "hire":
        machines = ["lovol", "tk", "plough", "sub", "planter", "sprayer", "combine", "reel", "exc"]
        graph.append({
            "@type": "Service", "@id": url(lang, page) + "#service",
            "name": text("hp.h1", lang), "serviceType": text("nav.hire", lang),
            "description": text("hp.desc", lang), "provider": {"@id": f"{SITE}/#business"},
            "areaServed": {"@type": "Country", "name": "Malawi"}, "url": url(lang, page),
            "hasOfferCatalog": {"@type": "OfferCatalog", "name": text("hire.fleetTitle", lang), "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": f'{text(f"fleet.{m}.name", lang)} ({text(f"fleet.{m}.model", lang)})', "description": text(f"fleet.{m}.text", lang)}}
                for m in machines]},
        })
    if page["id"] == "trade":
        products = [prod["id"] for cat in TRADE["categories"] for prod in cat["products"]]
        graph.append({
            "@type": "Service", "@id": url(lang, page) + "#service",
            "name": text("tp.h1", lang), "serviceType": text("biz.trade.title", lang),
            "description": text("tp.desc", lang), "provider": {"@id": f"{SITE}/#business"},
            "areaServed": "Worldwide", "url": url(lang, page),
            "hasOfferCatalog": {"@type": "OfferCatalog", "name": text("tp.catH2", lang), "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": text(f"prod.{pid}.name", lang), "description": text(f"prod.{pid}.text", lang),
                                                   "areaServed": "Worldwide"}}
                for pid in products]},
        })
    if page.get("faq"):
        graph.append({"@type": "FAQPage", "@id": url(lang, page) + "#faq", "mainEntity": [
            {"@type": "Question", "name": text(f"{page['faq']}.q{i}", lang), "acceptedAnswer": {"@type": "Answer", "text": text(f"{page['faq']}.a{i}", lang)}}
            for i in range(1, page["faqCount"] + 1)]})
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": text("hp.crumbHome", lang), "item": url(lang, PAGES[0])},
            {"@type": "ListItem", "position": 2, "name": text("nav." + page["id"], lang), "item": url(lang, page)}]})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("</", "<\\/")


def i18n(lang, page):
    data = {
        "lang": lang,
        "mail": {k.split(".", 1)[1]: T[k][lang] for k in T if k.startswith("mail.")},
        "suggest": {l: {"text": T["ui.langSuggest"][l], "go": T["ui.langGo"][l], "url": path(l, page)} for l in LANGS if l != lang},
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


# ---------- trade page data ----------
MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
    "pt": ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
}
TRADE_PATH = SRC / "trade-data.json"
TRADE = json.loads(TRADE_PATH.read_text("utf-8")) if TRADE_PATH.exists() else {"categories": [], "calendar": []}


def month_range(lang, start, end):
    """'May–Aug' / '5–8月' for 1-based months (end may wrap past December)."""
    if lang == "zh":
        return f"{start}月" if start == end else f"{start}–{end}月"
    m = MONTHS[lang]
    return m[start - 1] if start == end else f"{m[start - 1]}–{m[end - 1]}"


def bars(cls, start, end, row):
    """Grid bars for a month range in a given lane; a range that wraps past December is split in two."""
    if end >= start:
        return [f'<i class="sc-bar {cls}" style="grid-column: {start} / {end + 1}; grid-row: {row}"></i>']
    return [f'<i class="sc-bar {cls}" style="grid-column: {start} / 13; grid-row: {row}"></i>',
            f'<i class="sc-bar {cls}" style="grid-column: 1 / {end + 1}; grid-row: {row}"></i>']


def catalogue(lang):
    out = []
    for cat in TRADE["categories"]:
        items = []
        for prod in cat["products"]:
            avail = month_range(lang, *prod["supply"]) if prod.get("supply") else esc(text("tp.cal.yearRound", lang))
            pid = prod["id"]
            name, desc = esc(text(f"prod.{pid}.name", lang)), esc(text(f"prod.{pid}.text", lang))
            items.append(f'<li><strong>{name}</strong><span>{desc}</span><span class="avail">{avail}</span></li>')
        title = esc(text(f"cat.{cat['id']}", lang))
        out.append(f'        <div class="cat"><div class="cat-head">{cat["icon"]}<h3>{title}</h3></div><ul>{"".join(items)}</ul></div>')
    return "\n".join(out)


def tradecal(lang):
    rows = []
    for row in TRADE["calendar"]:
        b = bars("wheat harvest", *row["harvest"], 1) + (bars("maize", *row["supply"], 2) if row.get("supply") else [])
        label = esc(text(f"prod.{row['id']}.name", lang))
        colon, semi = {"fr": ("\u00a0: ", "\u00a0; "), "zh": ("：", "；")}.get(lang, (": ", "; "))
        spoken = f'{text("tp.cal.harvest", lang)}{colon}{month_range(lang, *row["harvest"])}'
        if row.get("supply"):
            spoken += f'{semi}{text("tp.cal.supply", lang)}{colon}{month_range(lang, *row["supply"])}'
        rows.append(f'          <span class="sc-label">{label}</span>\n          <div class="sc-track"><span class="sr-only">{esc(spoken)}</span>{"".join(b)}</div>')
    return "\n".join(rows)


# ---------- rendering ----------
def render(tpl, lang, page):
    for _ in range(5):  # resolve includes (they may include other partials)
        tpl = re.sub(r"\{\{include:([\w-]+)\}\}", lambda m: (SRC / "partials" / f"{m.group(1)}.html").read_text("utf-8").rstrip("\n"), tpl)

    hirepage = path(lang, PAGES[1])
    tradepage = path(lang, PAGES[2])
    variables = {
        "tradepage": tradepage,
        "lang": lang, "lang_tag": LANG_TAG[lang], "og_locale": OG_LOCALE[lang], "lang_short": LANG_SHORT[lang],
        "page_title": esc(text(page["title"], lang)), "page_desc": attr(text(page["desc"], lang)),
        "canonical": url(lang, page), "home": path(lang, PAGES[0]), "hirepage": hirepage,
        "hreflang": "\n".join(
            [f'<link rel="alternate" hreflang="{LANG_TAG[l]}" href="{url(l, page)}">' for l in LANGS]
            + [f'<link rel="alternate" hreflang="x-default" href="{url("en", page)}">']),
        "langmenu": "\n        ".join(
            f'<li><a href="{path(l, page)}" hreflang="{LANG_TAG[l]}" lang="{LANG_TAG[l]}"'
            + (' aria-current="true"' if l == lang else "") + f">{LANG_NAME[l]}</a></li>" for l in ["zh", "en", "fr", "pt"]),
        "footerlangs": " ".join(
            f'<a href="{path(l, page)}" hreflang="{LANG_TAG[l]}" lang="{LANG_TAG[l]}">{LANG_NAME[l]}</a>' for l in ["zh", "en", "fr", "pt"]),
        "alllangs": " · ".join(f'<span lang="{LANG_TAG[l]}">{LANG_NAME[l]}</span>' for l in ["zh", "en", "fr", "pt"]),
        "jsonld": jsonld(lang, page), "i18n": i18n(lang, page),
    }

    def macro(m):
        kind, arg = m.group(1), m.group(2)
        if kind is None:  # plain variable
            name = m.group(3)
            if name == "catalogue":
                return catalogue(lang)
            if name == "tradecal":
                return tradecal(lang)
            if name not in variables:
                sys.exit(f"Unknown variable {{{{{name}}}}}")
            return variables[name]
        if kind == "t":
            return esc(text(arg, lang))
        if kind == "raw":
            return text(arg, lang) if "<br>" in text(arg, lang) and lang == "zh" else esc(text(arg, lang).replace("<br>", " "))
        if kind == "attr":
            return attr(text(arg, lang))
        if kind == "selected":
            return " selected" if page["select"] == arg else ""
        if kind == "current":
            return ' aria-current="page"' if page["id"] == arg else ""
        if kind == "pic":
            p = arg.split("|")
            return picture(p[0], p[1], p[2], lang, decor=len(p) > 3 and p[3] == "decor")
        if kind == "fleet":
            name, key, focal, tags = arg.split("|")
            tag_html = "".join(f"<li>{esc(text('tag.' + t, lang))}</li>" for t in tags.split(",") if t)
            return (
                f'<article class="equip">{picture(name, "(max-width: 600px) 100vw, (max-width: 760px) 50vw, 370px", focal, lang)}'
                f'<div class="equip-body"><p class="equip-model">{esc(text(f"fleet.{key}.model", lang))}</p>'
                f'<h3>{esc(text(f"fleet.{key}.name", lang))}</h3><p>{esc(text(f"fleet.{key}.text", lang))}</p>'
                f'<ul class="tags">{tag_html}</ul>'
                f'<a class="crop-link" href="#contact" data-product="hire">{esc(text("hire.cta1", lang))} →</a></div></article>'
            )
        if kind == "thumb":
            name, key = arg.split("|")
            return (f'<a class="fleet-thumb" href="{hirepage}#fleet">{picture(name, "240px", "", lang, decor=True)}'
                    f'<span><small>{esc(text(f"fleet.{key}.model", lang))}</small>{esc(text(f"fleet.{key}.name", lang))}</span></a>')
        if kind == "catalogue":
            return catalogue(lang)
        if kind == "tradecal":
            return tradecal(lang)
        if kind == "gallery":
            out = []
            for item in arg.split(","):
                name, _, classes = item.partition("|")
                sizes = "(max-width: 600px) 100vw, (max-width: 1000px) 66vw, 600px" if "g-wide" in classes else "(max-width: 600px) 50vw, (max-width: 1000px) 33vw, 300px"
                cls = " ".join(["g-item", *classes.split()])
                out.append(f'<button class="{cls}" type="button" data-full="/assets/img/{name}-lg.webp">'
                           f'{picture(name, sizes, "", lang, decor=True)}<span class="g-cap">{esc(text("cap." + name, lang))}</span></button>')
            return "\n        ".join(out)
        sys.exit(f"Unknown placeholder {m.group(0)}")

    return re.sub(r"\{\{(?:(\w+):([^}]*)|(\w+))\}\}", macro, tpl)


layout = (SRC / "layout.html").read_text("utf-8")
written = []
for page in PAGES:
    body = (SRC / page["tpl"]).read_text("utf-8")
    for lang in LANGS:
        out = render(layout.replace("{{body}}", body.rstrip("\n")), lang, page)
        dest = ROOT / PREFIX[lang] / page["slug"] / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(out, "utf-8")
        written.append(dest.relative_to(ROOT))
        # The company name must always be written in full
        for m in re.finditer(r"Sycamore Agritech(?![\s\u00a0]+Limited)", out):
            warnings.append(f"{dest.relative_to(ROOT)}: short company name near: …{out[max(0, m.start() - 40):m.end() + 20]!r}…")

# 404 (English, noindex)
notfound = render(layout.replace("{{body}}", (SRC / "pages" / "404.html").read_text("utf-8").rstrip("\n")), "en", PAGES[0])
notfound = notfound.replace('<meta name="viewport"', '<meta name="robots" content="noindex">\n<meta name="viewport"', 1)
notfound = re.sub(r'<link rel="(?:canonical|alternate)"[^>]*>\n?', "", notfound)
notfound = re.sub(r"<title>[^<]*</title>", "<title>Page not found | Sycamore Agritech Limited</title>", notfound, 1)
(ROOT / "404.html").write_text(notfound, "utf-8")

# sitemap + robots
today = datetime.date.today().isoformat()
entries = []
for page in PAGES:
    for lang in LANGS:
        alts = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{LANG_TAG[l]}" href="{url(l, page)}"/>' for l in LANGS)
        alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{url("en", page)}"/>'
        entries.append(f"  <url>\n    <loc>{url(lang, page)}</loc>\n    <lastmod>{today}</lastmod>{alts}\n  </url>")
(ROOT / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    + "\n".join(entries) + "\n</urlset>\n", "utf-8")
(ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", "utf-8")

print("written:", ", ".join(str(p) for p in written), "+ 404.html, sitemap.xml, robots.txt")
for w in warnings:
    print("WARN", w)
