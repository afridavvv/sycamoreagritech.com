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
SITE = "https://sycamoreagritech.com"
LANGS = ["en", "zh", "fr", "pt"]
LANG_TAG = {"en": "en", "zh": "zh-Hans", "fr": "fr", "pt": "pt"}
OG_LOCALE = {"en": "en_GB", "zh": "zh_CN", "fr": "fr_FR", "pt": "pt_PT"}
LANG_NAME = {"en": "English", "zh": "中文", "fr": "Français", "pt": "Português"}
LANG_SHORT = {"en": "EN", "zh": "中文", "fr": "FR", "pt": "PT"}
PREFIX = {"en": "", "zh": "zh/", "fr": "fr/", "pt": "pt/"}
PAGES = [
    {"id": "home", "tpl": "pages/home.html", "slug": "", "title": "meta.title", "desc": "meta.desc", "select": None},
    {"id": "hire", "tpl": "pages/hire.html", "slug": "machinery-hire/", "title": "hp.title", "desc": "hp.desc", "select": "hire"},
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


def text(key, lang):
    if key not in T:
        sys.exit(f"Unknown content key: {key}")
    return T[key][lang]


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
        "url": f"{SITE}/",
        "logo": f"{SITE}/assets/apple-touch-icon.png",
        "image": [f"{SITE}/assets/img/hero-pivot-wheat-lg.jpg", f"{SITE}/assets/og-image.jpg"],
        "description": text("meta.desc", lang),
        "telephone": "+265 999 947 228",
        "email": "info@sycamoreagritech.com",
        "address": {"@type": "PostalAddress", "streetAddress": "Chitipi", "addressLocality": "Lilongwe", "addressCountry": "MW"},
        "areaServed": {"@type": "Country", "name": "Malawi"},
        "knowsLanguage": ["en", "zh", "fr", "pt"],
        "contactPoint": [
            {"@type": "ContactPoint", "contactType": "customer service", "telephone": "+265 999 947 228", "email": "info@sycamoreagritech.com", "areaServed": "MW", "availableLanguage": ["English", "Chinese", "French", "Portuguese"]},
            {"@type": "ContactPoint", "contactType": "sales", "telephone": "+265 999 441 333", "email": "sales@sycamoreagritech.com", "areaServed": "MW"},
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
        graph.append({"@type": "FAQPage", "@id": url(lang, page) + "#faq", "mainEntity": [
            {"@type": "Question", "name": text(f"faq.q{i}", lang), "acceptedAnswer": {"@type": "Answer", "text": text(f"faq.a{i}", lang)}}
            for i in range(1, 6)]})
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": text("hp.crumbHome", lang), "item": url(lang, PAGES[0])},
            {"@type": "ListItem", "position": 2, "name": text("nav.hire", lang), "item": url(lang, page)}]})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("</", "<\\/")


def i18n(lang, page):
    data = {
        "lang": lang,
        "mail": {k.split(".", 1)[1]: T[k][lang] for k in T if k.startswith("mail.")},
        "suggest": {l: {"text": T["ui.langSuggest"][l], "go": T["ui.langGo"][l], "url": path(l, page)} for l in LANGS if l != lang},
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


# ---------- rendering ----------
def render(tpl, lang, page):
    for _ in range(5):  # resolve includes (they may include other partials)
        tpl = re.sub(r"\{\{include:([\w-]+)\}\}", lambda m: (SRC / "partials" / f"{m.group(1)}.html").read_text("utf-8").rstrip("\n"), tpl)

    hirepage = path(lang, PAGES[1])
    variables = {
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
        "alllangs": "中文 · English · Français · Português",
        "jsonld": jsonld(lang, page), "i18n": i18n(lang, page),
    }

    def macro(m):
        kind, arg = m.group(1), m.group(2)
        if kind is None:  # plain variable
            name = m.group(3)
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

# 404 (English, noindex)
notfound = render(layout.replace("{{body}}", (SRC / "pages" / "404.html").read_text("utf-8").rstrip("\n")), "en", PAGES[0])
notfound = notfound.replace('<meta name="viewport"', '<meta name="robots" content="noindex">\n<meta name="viewport"', 1)
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
