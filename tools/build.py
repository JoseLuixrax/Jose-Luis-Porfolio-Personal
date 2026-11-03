#!/usr/bin/env python3
"""
Generador estático del portfolio (español e inglés).

Lee content/projects.toml (español) y content/projects.en.toml (inglés) y, para cada idioma:
  1. genera una página por proyecto: proyectos/<slug>.html y en/projects/<slug>.html
  2. inserta las tarjetas de proyecto y el sprite de iconos en la portada (index.html y
     en/index.html, entre los marcadores <!-- X:START --> y <!-- X:END -->)
Después regenera sitemap.xml con las páginas de los dos idiomas.

En projects.en.toml cada proyecto se enlaza con el español por su slug. Los campos que no
aparecen en inglés (categoría, filtros, etiquetas, código...) se heredan del español.

Uso:
    python3 tools/build.py

Sin dependencias externas: Python 3.11+ (tomllib). En Python 3.10 o anterior:
    pip install tomli
"""
from __future__ import annotations

import html
import posixpath
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from icons import ICONS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"

STATUS_CLASS = {
    "En producción": "",
    "Herramienta interna": "",
    "En implantación": "status--wip",
    "Open source": "status--oss",
    "In production": "",
    "Internal tool": "",
    "Rollout in progress": "status--wip",
}

FONTS = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600"
    "&family=JetBrains+Mono:wght@400;500&display=swap"
)

THEME_BOOT = (
    "<script>(function(){var t;try{t=localStorage.getItem('theme')}catch(e){}"
    "if(!t){t=window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}"
    "document.documentElement.setAttribute('data-theme',t)})();</script>"
)

# Campos que cada proyecto debe tener traducidos en projects.en.toml (si existen en español).
TRANSLATED = (
    "title", "kicker", "status", "period", "role", "context", "summary", "tagline",
    "problem", "solution", "learnings", "results", "kpis", "flow", "features", "stack",
    "challenges", "links",
)

# --------------------------------------------------------------------------- idiomas
# root: carpeta del idioma dentro del sitio · projects_dir: carpeta de las páginas de proyecto.
LANGS = {
    "es": {
        "root": "",
        "projects_dir": "proyectos",
        "locale": "es_ES",
        "content": "projects.toml",
        "ui": {
            "switch": ("ES", "Ver en español"),
            "anchors": {"about": "sobre-mi", "projects": "proyectos", "stack": "stack",
                        "experience": "experiencia", "contact": "contacto"},
            "nav": {"about": "Sobre mí", "projects": "Proyectos", "stack": "Stack",
                    "experience": "Experiencia", "contact": "Contacto"},
            "nav_label": "Principal",
            "skip": "Saltar al contenido",
            "theme": "Cambiar tema claro/oscuro",
            "menu": "Abrir menú",
            "cta": "Contactar",
            "view_project": "Ver proyecto",
            "sections": {
                "problem": ("problema", "El problema"),
                "solution": ("solucion", "La solución"),
                "flow": ("arquitectura", "Arquitectura y flujo"),
                "features": ("funcionalidades", "Funcionalidades clave"),
                "stack": ("stack", "Stack y por qué"),
                "challenges": ("retos", "Retos técnicos"),
                "results": ("resultados", "Resultados"),
                "snippet": ("codigo", "Código"),
                "learnings": ("aprendizajes", "Lo que aprendí"),
            },
            "facts": ("Rol", "Contexto", "Periodo", "Estado"),
            "toc": "En esta página",
            "copy": "Copiar",
            "private": "Proyecto interno: el código fuente es privado. "
                       "Este fragmento está simplificado, sin credenciales ni datos de negocio.",
            "cta_title": "¿Te interesa este perfil?",
            "cta_text": "Si este proyecto se parece a los retos de tu equipo, estaré encantado de contarte "
                        "cómo lo abordaría en vuestro contexto.",
            "cta_button": "Escríbeme",
            "mail_subject": "Contacto desde tu portfolio",
            "pager": "Otros proyectos",
            "prev": "Anterior",
            "next": "Siguiente",
        },
    },
    "en": {
        "root": "en/",
        "projects_dir": "projects",
        "locale": "en_US",
        "content": "projects.en.toml",
        "ui": {
            "switch": ("EN", "Read in English"),
            "anchors": {"about": "about", "projects": "projects", "stack": "stack",
                        "experience": "experience", "contact": "contact"},
            "nav": {"about": "About", "projects": "Projects", "stack": "Stack",
                    "experience": "Experience", "contact": "Contact"},
            "nav_label": "Main",
            "skip": "Skip to content",
            "theme": "Toggle light/dark theme",
            "menu": "Open menu",
            "cta": "Get in touch",
            "view_project": "View project",
            "sections": {
                "problem": ("problem", "The problem"),
                "solution": ("solution", "The solution"),
                "flow": ("architecture", "Architecture and flow"),
                "features": ("features", "Key features"),
                "stack": ("stack", "Stack and why"),
                "challenges": ("challenges", "Technical challenges"),
                "results": ("results", "Results"),
                "snippet": ("code", "Code"),
                "learnings": ("learnings", "What I learned"),
            },
            "facts": ("Role", "Context", "Period", "Status"),
            "toc": "On this page",
            "copy": "Copy",
            "private": "Internal project: the source code is private. "
                       "This snippet is simplified, with no credentials or business data.",
            "cta_title": "Interested in this profile?",
            "cta_text": "If this project looks like the kind of problem your team deals with, I'd be glad "
                        "to tell you how I would approach it in your context.",
            "cta_button": "Email me",
            "mail_subject": "Contact from your portfolio",
            "pager": "More projects",
            "prev": "Previous",
            "next": "Next",
        },
    },
}
DEFAULT_LANG = "es"


def load(name: str) -> dict:
    return tomllib.loads((CONTENT / name).read_text(encoding="utf-8"))


def merge_project(es: dict, en: dict) -> dict:
    """Proyecto en inglés: lo que no está traducido se hereda del español."""
    merged = {**es, **en}
    if "snippet" in es:
        merged["snippet"] = {**es["snippet"], **en.get("snippet", {})}
    return merged


def load_content() -> tuple[dict, dict[str, dict]]:
    es = load(LANGS["es"]["content"])
    en = load(LANGS["en"]["content"])
    en_by_slug = {p["slug"]: p for p in en["projects"]}
    content = {
        "es": {"categories": {c["id"]: c["label"] for c in es["categories"]}, "projects": es["projects"]},
        "en": {
            "categories": {c["id"]: c["label"] for c in en["categories"]},
            "projects": [merge_project(p, en_by_slug.get(p["slug"], {})) for p in es["projects"]],
        },
    }
    validate(es, en_by_slug, content)
    return es["site"], content


def validate(es: dict, en_by_slug: dict[str, dict], content: dict) -> None:
    slugs = [p["slug"] for p in es["projects"]]
    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        raise ValueError(f"Slugs duplicados: {dupes}")
    categories = content["es"]["categories"]
    if set(content["en"]["categories"]) != set(categories):
        raise ValueError("Las categorías de projects.en.toml no coinciden con las de projects.toml")
    for p in es["projects"]:
        if p["category"] not in categories:
            raise ValueError(f"{p['slug']}: categoría desconocida '{p['category']}'")
        unknown = set(p["filters"]) - set(categories)
        if unknown:
            raise ValueError(f"{p['slug']}: filtros desconocidos {unknown}")
        en = en_by_slug.get(p["slug"])
        if en is None:
            raise ValueError(f"{p['slug']}: falta la traducción en projects.en.toml")
        missing = [k for k in TRANSLATED if k in p and k not in en]
        if p.get("snippet", {}).get("note") and not en.get("snippet", {}).get("note"):
            missing.append("snippet.note")
        if missing:
            raise ValueError(f"{p['slug']}: faltan campos traducidos en projects.en.toml: {missing}")
    extra = set(en_by_slug) - set(slugs)
    if extra:
        raise ValueError(f"projects.en.toml tiene proyectos que no existen en español: {extra}")


SITE, CONTENT_BY_LANG = load_content()


# --------------------------------------------------------------------------- utilidades
def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def inline(text: str) -> str:
    """Escapa HTML y aplica un markdown mínimo: **negrita**, *cursiva* y `código`."""
    out = esc(text)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"\*([^*\s][^*]*?)\*", r"<em>\1</em>", out)
    return out


def paragraphs(text: str) -> str:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
    return "\n".join(f"<p>{inline(' '.join(b.split()))}</p>" for b in blocks)


def icon(name: str, extra: str = "") -> str:
    if name not in ICONS:
        raise KeyError(f"Icono desconocido: {name}")
    cls = f"icon {extra}".strip()
    return f'<svg class="{cls}" aria-hidden="true"><use href="#i-{name}"></use></svg>'


def sprite() -> str:
    symbols = "".join(
        f'<symbol id="i-{name}" viewBox="0 0 24 24">{paths}</symbol>' for name, paths in ICONS.items()
    )
    return f'<svg xmlns="http://www.w3.org/2000/svg" style="display:none">{symbols}</svg>'


def status(p: dict) -> str:
    cls = f"status {STATUS_CLASS.get(p['status'], '')}".strip()
    return f'<span class="{cls}">{esc(p["status"])}</span>'


def tech_line(tags: list[str]) -> str:
    return " · ".join(esc(t) for t in tags)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


# --------------------------------------------------------------------------- rutas
def page_path(lang: str, slug: str | None = None) -> str:
    """Ruta de una página dentro del sitio: index.html, en/index.html, proyectos/x.html..."""
    cfg = LANGS[lang]
    if slug is None:
        return f"{cfg['root']}index.html"
    return f"{cfg['root']}{cfg['projects_dir']}/{slug}.html"


def page_url(lang: str, slug: str | None = None) -> str:
    path = page_path(lang, slug)
    if path.endswith("index.html"):
        path = path[: -len("index.html")]
    return SITE["base_url"] + path


def rel(target: str, current: str) -> str:
    """Enlace relativo desde la página `current` a `target` (ambas rutas desde la raíz del sitio)."""
    return posixpath.relpath(target, posixpath.dirname(current) or ".")


def other_lang(lang: str) -> str:
    return next(code for code in LANGS if code != lang)


def alternates(slug: str | None = None) -> str:
    links = [
        f'  <link rel="alternate" hreflang="{code}" href="{page_url(code, slug)}">' for code in LANGS
    ]
    links.append(f'  <link rel="alternate" hreflang="x-default" href="{page_url(DEFAULT_LANG, slug)}">')
    return "\n".join(links)


def replace_block(source: str, marker: str, content: str, name: str) -> str:
    pattern = re.compile(rf"(<!-- {marker}:START -->)(.*?)(<!-- {marker}:END -->)", re.S)
    if not pattern.search(source):
        raise ValueError(f"No se encuentra el marcador {marker} en {name}")
    return pattern.sub(lambda m: f"{m.group(1)}\n{content}\n{m.group(3)}", source)


# --------------------------------------------------------------------------- portada
def project_card(lang: str, p: dict) -> str:
    href = rel(page_path(lang, p["slug"]), page_path(lang))
    more = LANGS[lang]["ui"]["view_project"]
    return f"""          <a class="pcard" href="{href}" data-filters="{' '.join(p['filters'])}">
            <p class="label">{esc(p['kicker'])}</p>
            <h3 class="pcard__title">{esc(p['title'])}</h3>
            <p class="pcard__summary">{esc(p['summary'])}</p>
            <p class="tech-line">{tech_line(p['tags'][:5])}</p>
            <div class="pcard__foot">{status(p)}<span class="pcard__more">{more} {icon('arrow-right')}</span></div>
          </a>"""


def build_index(lang: str) -> None:
    name = page_path(lang)
    path = ROOT / name
    source = path.read_text(encoding="utf-8")
    source = replace_block(source, "ICONS", sprite(), name)
    cards = "\n".join(project_card(lang, p) for p in CONTENT_BY_LANG[lang]["projects"])
    source = replace_block(source, "PROJECTS", cards, name)
    write(path, source)


# --------------------------------------------------------------------------- páginas de proyecto
def head(lang: str, p: dict) -> str:
    current = page_path(lang, p["slug"])
    url = page_url(lang, p["slug"])
    title = f"{p['title']} · {SITE['name']}"
    desc = p["summary"]
    og = f"{SITE['base_url']}assets/img/og-cover.png"
    locale = LANGS[lang]["locale"]
    locale_alt = LANGS[other_lang(lang)]["locale"]
    assets = rel("assets", current)
    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}">
  <meta name="author" content="{esc(SITE['name'])}">
  <link rel="canonical" href="{url}">
{alternates(p['slug'])}
  <meta property="og:type" content="article">
  <meta property="og:locale" content="{locale}">
  <meta property="og:locale:alternate" content="{locale_alt}">
  <meta property="og:site_name" content="{esc(SITE['name'])}">
  <meta property="og:title" content="{esc(p['title'])}">
  <meta property="og:description" content="{esc(desc)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{og}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="{assets}/img/favicon-32.png" type="image/png" sizes="32x32">
  <link rel="icon" href="{assets}/img/favicon-192.png" type="image/png" sizes="192x192">
  <link rel="apple-touch-icon" href="{assets}/img/apple-touch-icon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="{FONTS}">
  <link rel="stylesheet" href="{assets}/css/styles.css">
  {THEME_BOOT}
</head>"""


def lang_switch(lang: str, current: str, slug: str | None = None) -> str:
    target = other_lang(lang)
    code, label = LANGS[target]["ui"]["switch"]
    href = rel(page_path(target, slug), current)
    return (
        f'<a class="icon-btn lang-switch" href="{href}" hreflang="{target}" lang="{target}" '
        f'aria-label="{esc(label)}" title="{esc(label)}">{code}</a>'
    )


def nav(lang: str, slug: str) -> str:
    ui = LANGS[lang]["ui"]
    current = page_path(lang, slug)
    home = rel(page_path(lang), current)
    items = "".join(
        f'<li><a href="{home}#{ui["anchors"][key]}">{esc(label)}</a></li>' for key, label in ui["nav"].items()
    )
    return f"""  <a class="skip-link" href="#contenido">{esc(ui['skip'])}</a>
  <header class="nav">
    <div class="container nav__inner">
      <a class="brand" href="{home}">{esc(SITE['name'])}</a>
      <nav aria-label="{esc(ui['nav_label'])}"><ul class="nav__links" id="menu">{items}</ul></nav>
      <div class="nav__actions">
        {lang_switch(lang, current, slug)}
        <button class="icon-btn theme-toggle" type="button" data-theme-toggle aria-label="{esc(ui['theme'])}">{icon('moon', 'i-moon')}{icon('sun', 'i-sun')}</button>
        <a class="btn btn--primary btn--sm nav__cta" href="{home}#{ui['anchors']['contact']}">{esc(ui['cta'])}</a>
        <button class="icon-btn nav__toggle" type="button" aria-label="{esc(ui['menu'])}" aria-controls="menu" aria-expanded="false">{icon('menu', 'i-open')}{icon('x', 'i-close')}</button>
      </div>
    </div>
  </header>"""


def footer() -> str:
    return f"""  <footer class="footer">
    <div class="container footer__inner">
      <span>© <span data-year>{date.today().year}</span> {esc(SITE['name'])}</span>
      <div class="footer__links">
        <a href="mailto:{SITE['email']}">Email</a>
        <a href="{SITE['linkedin']}" target="_blank" rel="noopener">LinkedIn</a>
        <a href="{SITE['github']}" target="_blank" rel="noopener">GitHub</a>
      </div>
    </div>
  </footer>"""


def flow_html(steps: list[dict]) -> str:
    parts = []
    for i, s in enumerate(steps):
        if i:
            parts.append(f'<li class="flow__arrow" aria-hidden="true">{icon("arrow-right")}</li>')
        parts.append(f'<li class="flow__step"><b>{esc(s["title"])}</b><span>{inline(s["text"])}</span></li>')
    return f'<ol class="flow">{"".join(parts)}</ol>'


def features_html(items: list[dict]) -> str:
    cards = "".join(
        f'<div class="feature"><h3>{esc(f["title"])}</h3><p>{inline(f["text"])}</p></div>' for f in items
    )
    return f'<div class="features">{cards}</div>'


def stack_html(items: list[dict]) -> str:
    rows = "".join(
        f'<div class="tech__row"><span class="tech__name">{esc(t["name"])}</span>'
        f'<span class="tech__why">{inline(t["why"])}</span></div>'
        for t in items
    )
    return f'<div class="tech">{rows}</div>'


def challenges_html(items: list[dict]) -> str:
    lis = "".join(
        f'<li class="challenge"><div><h3>{esc(c["title"])}</h3><p>{inline(c["text"])}</p></div></li>' for c in items
    )
    return f'<ol class="challenges">{lis}</ol>'


def results_html(items: list[str]) -> str:
    lis = "".join(f'<li>{icon("check")}<span>{inline(r)}</span></li>' for r in items)
    return f'<ul class="checks">{lis}</ul>'


def snippet_html(lang: str, p: dict) -> str:
    ui = LANGS[lang]["ui"]
    s = p["snippet"]
    code = esc(s["code"].strip("\n"))
    note = ""
    if p.get("confidential"):
        note = f'<p class="note">{icon("lock")}<span>{esc(ui["private"])}</span></p>'
    elif s.get("note"):
        note = f'<p class="note">{icon("code")}<span>{inline(s["note"])}</span></p>'
    return f"""<div class="code">
            <div class="code__bar"><span>{esc(s['title'])}</span><button class="code__copy" type="button">{icon('copy')}<span>{esc(ui['copy'])}</span></button></div>
            <pre><code class="language-{esc(s['lang'])}">{code}</code></pre>
          </div>
          {note}"""


def project_page(lang: str, i: int, p: dict) -> str:
    ui = LANGS[lang]["ui"]
    projects = CONTENT_BY_LANG[lang]["projects"]
    categories = CONTENT_BY_LANG[lang]["categories"]
    current = page_path(lang, p["slug"])
    home = rel(page_path(lang), current)
    assets = rel("assets", current)

    def section(key: str, content: str) -> tuple[str, str, str]:
        sid, title = ui["sections"][key]
        return sid, title, content

    sections: list[tuple[str, str, str]] = [
        section("problem", f'<div class="prose">{paragraphs(p["problem"])}</div>'),
        section("solution", f'<div class="prose">{paragraphs(p["solution"])}</div>'),
    ]
    if p.get("flow"):
        sections.append(section("flow", flow_html(p["flow"])))
    if p.get("features"):
        sections.append(section("features", features_html(p["features"])))
    if p.get("stack"):
        sections.append(section("stack", stack_html(p["stack"])))
    if p.get("challenges"):
        sections.append(section("challenges", challenges_html(p["challenges"])))
    if p.get("results"):
        sections.append(section("results", results_html(p["results"])))
    if p.get("snippet"):
        sections.append(section("snippet", snippet_html(lang, p)))
    if p.get("learnings"):
        sections.append(section("learnings", f'<div class="prose">{paragraphs(p["learnings"])}</div>'))

    toc = "".join(f'<li><a href="#{sid}">{esc(title)}</a></li>' for sid, title, _ in sections)
    body = "\n".join(
        f"""        <section class="p-section" id="{sid}">
          <h2><span class="num">{n:02d}</span>{esc(title)}</h2>
          {content}
        </section>"""
        for n, (sid, title, content) in enumerate(sections, 1)
    )

    facts = "".join(
        f'<div class="fact"><dt class="label">{esc(label)}</dt><dd>{value}</dd></div>'
        for label, value in zip(ui["facts"], (esc(p["role"]), esc(p["context"]), esc(p["period"]), status(p)))
    )
    kpis = "".join(
        f'<div class="kpi"><div class="kpi__value">{esc(k["value"])}</div><div class="kpi__label">{esc(k["label"])}</div></div>'
        for k in p.get("kpis", [])
    )
    links = ""
    if p.get("links"):
        btns = "".join(
            f'<a class="btn btn--ghost btn--sm" href="{esc(l["url"])}" target="_blank" rel="noopener">'
            f'{icon(l.get("icon", "external"))}{esc(l["label"])}</a>'
            for l in p["links"]
        )
        links = f'<div class="p-hero__links">{btns}</div>'

    prev_p = projects[i - 1] if i > 0 else None
    next_p = projects[i + 1] if i < len(projects) - 1 else None
    pager = ""
    if prev_p:
        pager += (
            f'<a class="prev" href="{prev_p["slug"]}.html"><small>{icon("arrow-left")} {esc(ui["prev"])}</small>'
            f'<strong>{esc(prev_p["title"])}</strong></a>'
        )
    if next_p:
        pager += (
            f'<a class="next" href="{next_p["slug"]}.html"><small>{esc(ui["next"])} {icon("arrow-right")}</small>'
            f'<strong>{esc(next_p["title"])}</strong></a>'
        )

    scripts = f'  <script src="{assets}/js/main.js" defer></script>'
    if p.get("snippet"):
        scripts = f'  <script src="{assets}/js/prism.min.js" defer></script>\n' + scripts

    subject = quote(ui["mail_subject"])
    return f"""{head(lang, p)}
<body>
{sprite()}
{nav(lang, p['slug'])}
  <main id="contenido">
    <header class="p-hero">
      <div class="container">
        <a class="back" href="{home}#{ui['anchors']['projects']}">{icon('arrow-left')} {esc(ui['nav']['projects'])}</a>
        <p class="label">{esc(categories[p['category']])} · {esc(p['kicker'])}</p>
        <h1>{esc(p['title'])}</h1>
        <p class="p-hero__tagline">{esc(p['tagline'])}</p>
        {links}
        <dl class="facts">{facts}</dl>
        <div class="kpis">{kpis}</div>
        <div class="p-stack"><span class="label">Stack</span><span class="tech-line">{tech_line(p['tags'])}</span></div>
      </div>
    </header>

    <div class="container">
      <div class="p-layout">
        <aside class="toc" aria-label="{esc(ui['toc'])}">
          <p class="label">{esc(ui['toc'])}</p>
          <ol>{toc}</ol>
        </aside>
        <article class="p-content">
{body}
        </article>
      </div>

      <section class="p-cta" aria-labelledby="cta-title">
        <h2 id="cta-title">{esc(ui['cta_title'])}</h2>
        <p>{esc(ui['cta_text'])}</p>
        <div class="contact__actions">
          <a class="btn btn--primary" href="mailto:{SITE['email']}?subject={subject}">{icon('mail')}{esc(ui['cta_button'])}</a>
          <a class="btn btn--ghost" href="{SITE['linkedin']}" target="_blank" rel="noopener">{icon('linkedin')}LinkedIn</a>
        </div>
      </section>

      <nav class="pager" aria-label="{esc(ui['pager'])}">{pager}</nav>
    </div>
  </main>
{footer()}
{scripts}
</body>
</html>
"""


# --------------------------------------------------------------------------- sitemap
def build_sitemap() -> None:
    today = date.today().isoformat()
    urls = []
    for lang in LANGS:
        urls.append(page_url(lang))
        urls += [page_url(lang, p["slug"]) for p in CONTENT_BY_LANG[lang]["projects"]]
    entries = "\n".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    write(
        ROOT / "sitemap.xml",
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n</urlset>\n",
    )


# --------------------------------------------------------------------------- main
def build_lang(lang: str) -> None:
    cfg = LANGS[lang]
    projects = CONTENT_BY_LANG[lang]["projects"]
    out_dir = ROOT / cfg["root"] / cfg["projects_dir"]
    expected = set()
    for i, p in enumerate(projects):
        target = ROOT / page_path(lang, p["slug"])
        write(target, project_page(lang, i, p))
        expected.add(target.name)
    for stale in out_dir.glob("*.html"):
        if stale.name not in expected:
            stale.unlink()
            print(f"  eliminado {stale.relative_to(ROOT)} (ya no está en {cfg['content']})")
    build_index(lang)
    print(f"OK · {lang}: {len(projects)} proyectos en {cfg['root']}{cfg['projects_dir']}/ · {page_path(lang)} actualizado")


def main() -> None:
    for lang in LANGS:
        build_lang(lang)
    build_sitemap()
    print("OK · sitemap.xml actualizado")


if __name__ == "__main__":
    main()
