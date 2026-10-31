#!/usr/bin/env python3
"""
Generador estático del portfolio.

Lee content/projects.toml y:
  1. genera una página por proyecto en proyectos/<slug>.html
  2. inserta las tarjetas de proyecto y el sprite de iconos en index.html
     (entre los marcadores <!-- X:START --> y <!-- X:END -->)
  3. regenera sitemap.xml

Uso:
    python3 tools/build.py

Sin dependencias externas: Python 3.11+ (tomllib). En Python 3.10 o anterior:
    pip install tomli
"""
from __future__ import annotations

import html
import re
import sys
from datetime import date
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from icons import ICONS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = tomllib.loads((ROOT / "content" / "projects.toml").read_text(encoding="utf-8"))
SITE = DATA["site"]
CATEGORIES = {c["id"]: c["label"] for c in DATA["categories"]}
PROJECTS = DATA["projects"]

STATUS_CLASS = {
    "En producción": "",
    "Herramienta interna": "",
    "En implantación": "status--wip",
    "Open source": "status--oss",
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


# --------------------------------------------------------------------------- utilidades
def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def inline(text: str) -> str:
    """Escapa HTML y aplica un markdown mínimo: **negrita** y `código`."""
    out = esc(text)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
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


def replace_block(source: str, marker: str, content: str) -> str:
    pattern = re.compile(rf"(<!-- {marker}:START -->)(.*?)(<!-- {marker}:END -->)", re.S)
    if not pattern.search(source):
        raise ValueError(f"No se encuentra el marcador {marker} en index.html")
    return pattern.sub(lambda m: f"{m.group(1)}\n{content}\n{m.group(3)}", source)


# --------------------------------------------------------------------------- portada
def project_card(p: dict) -> str:
    return f"""          <a class="pcard" href="proyectos/{p['slug']}.html" data-filters="{' '.join(p['filters'])}">
            <p class="label">{esc(p['kicker'])}</p>
            <h3 class="pcard__title">{esc(p['title'])}</h3>
            <p class="pcard__summary">{esc(p['summary'])}</p>
            <p class="tech-line">{tech_line(p['tags'][:5])}</p>
            <div class="pcard__foot">{status(p)}<span class="pcard__more">Ver proyecto {icon('arrow-right')}</span></div>
          </a>"""


def build_index() -> None:
    path = ROOT / "index.html"
    source = path.read_text(encoding="utf-8")
    source = replace_block(source, "ICONS", sprite())
    source = replace_block(source, "PROJECTS", "\n".join(project_card(p) for p in PROJECTS))
    path.write_text(source, encoding="utf-8")


# --------------------------------------------------------------------------- páginas de proyecto
def head(p: dict) -> str:
    url = f"{SITE['base_url']}proyectos/{p['slug']}.html"
    title = f"{p['title']} · {SITE['name']}"
    desc = p["summary"]
    og = f"{SITE['base_url']}assets/img/og-cover.png"
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}">
  <meta name="author" content="{esc(SITE['name'])}">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="article">
  <meta property="og:locale" content="es_ES">
  <meta property="og:site_name" content="{esc(SITE['name'])}">
  <meta property="og:title" content="{esc(p['title'])}">
  <meta property="og:description" content="{esc(desc)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{og}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="../assets/img/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="{FONTS}">
  <link rel="stylesheet" href="../assets/css/styles.css">
  {THEME_BOOT}
</head>"""


def nav() -> str:
    links = [
        ("Sobre mí", "../index.html#sobre-mi"),
        ("Proyectos", "../index.html#proyectos"),
        ("Stack", "../index.html#stack"),
        ("Experiencia", "../index.html#experiencia"),
        ("Contacto", "../index.html#contacto"),
    ]
    items = "".join(f'<li><a href="{href}">{label}</a></li>' for label, href in links)
    return f"""  <a class="skip-link" href="#contenido">Saltar al contenido</a>
  <header class="nav">
    <div class="container nav__inner">
      <a class="brand" href="../index.html">{esc(SITE['name'])}</a>
      <nav aria-label="Principal"><ul class="nav__links" id="menu">{items}</ul></nav>
      <div class="nav__actions">
        <button class="icon-btn theme-toggle" type="button" data-theme-toggle aria-label="Cambiar tema claro/oscuro">{icon('moon', 'i-moon')}{icon('sun', 'i-sun')}</button>
        <a class="btn btn--primary btn--sm nav__cta" href="../index.html#contacto">Contactar</a>
        <button class="icon-btn nav__toggle" type="button" aria-label="Abrir menú" aria-controls="menu" aria-expanded="false">{icon('menu', 'i-open')}{icon('x', 'i-close')}</button>
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


def snippet_html(p: dict) -> str:
    s = p["snippet"]
    code = esc(s["code"].strip("\n"))
    note = ""
    if p.get("confidential"):
        note = (
            f'<p class="note">{icon("lock")}<span>Proyecto interno: el código fuente es privado. '
            "Este fragmento está simplificado, sin credenciales ni datos de negocio.</span></p>"
        )
    elif s.get("note"):
        note = f'<p class="note">{icon("code")}<span>{inline(s["note"])}</span></p>'
    return f"""<div class="code">
            <div class="code__bar"><span>{esc(s['title'])}</span><button class="code__copy" type="button">{icon('copy')}<span>Copiar</span></button></div>
            <pre><code class="language-{esc(s['lang'])}">{code}</code></pre>
          </div>
          {note}"""


def project_page(i: int, p: dict) -> str:
    sections: list[tuple[str, str, str]] = [
        ("problema", "El problema", f'<div class="prose">{paragraphs(p["problem"])}</div>'),
        ("solucion", "La solución", f'<div class="prose">{paragraphs(p["solution"])}</div>'),
    ]
    if p.get("flow"):
        sections.append(("arquitectura", "Arquitectura y flujo", flow_html(p["flow"])))
    if p.get("features"):
        sections.append(("funcionalidades", "Funcionalidades clave", features_html(p["features"])))
    if p.get("stack"):
        sections.append(("stack", "Stack y por qué", stack_html(p["stack"])))
    if p.get("challenges"):
        sections.append(("retos", "Retos técnicos", challenges_html(p["challenges"])))
    if p.get("results"):
        sections.append(("resultados", "Resultados", results_html(p["results"])))
    if p.get("snippet"):
        sections.append(("codigo", "Código", snippet_html(p)))
    if p.get("learnings"):
        sections.append(("aprendizajes", "Lo que aprendí", f'<div class="prose">{paragraphs(p["learnings"])}</div>'))

    toc = "".join(f'<li><a href="#{sid}">{esc(title)}</a></li>' for sid, title, _ in sections)
    body = "\n".join(
        f"""        <section class="p-section" id="{sid}">
          <h2><span class="num">{n:02d}</span>{esc(title)}</h2>
          {content}
        </section>"""
        for n, (sid, title, content) in enumerate(sections, 1)
    )

    facts = "".join(
        f'<div class="fact"><dt class="label">{label}</dt><dd>{value}</dd></div>'
        for label, value in (
            ("Rol", esc(p["role"])),
            ("Contexto", esc(p["context"])),
            ("Periodo", esc(p["period"])),
            ("Estado", status(p)),
        )
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

    prev_p = PROJECTS[i - 1] if i > 0 else None
    next_p = PROJECTS[i + 1] if i < len(PROJECTS) - 1 else None
    pager = ""
    if prev_p:
        pager += (
            f'<a class="prev" href="{prev_p["slug"]}.html"><small>{icon("arrow-left")} Anterior</small>'
            f'<strong>{esc(prev_p["title"])}</strong></a>'
        )
    if next_p:
        pager += (
            f'<a class="next" href="{next_p["slug"]}.html"><small>Siguiente {icon("arrow-right")}</small>'
            f'<strong>{esc(next_p["title"])}</strong></a>'
        )

    scripts = '  <script src="../assets/js/main.js" defer></script>'
    if p.get("snippet"):
        scripts = '  <script src="../assets/js/prism.min.js" defer></script>\n' + scripts

    return f"""{head(p)}
<body>
{sprite()}
{nav()}
  <main id="contenido">
    <header class="p-hero">
      <div class="container">
        <a class="back" href="../index.html#proyectos">{icon('arrow-left')} Proyectos</a>
        <p class="label">{esc(CATEGORIES[p['category']])} · {esc(p['kicker'])}</p>
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
        <aside class="toc" aria-label="En esta página">
          <p class="label">En esta página</p>
          <ol>{toc}</ol>
        </aside>
        <article class="p-content">
{body}
        </article>
      </div>

      <section class="p-cta" aria-labelledby="cta-title">
        <h2 id="cta-title">¿Te interesa este perfil?</h2>
        <p>Si este proyecto se parece a los retos de tu equipo, estaré encantado de contarte cómo lo abordaría en vuestro contexto.</p>
        <div class="contact__actions">
          <a class="btn btn--primary" href="mailto:{SITE['email']}?subject=Contacto%20desde%20tu%20portfolio">{icon('mail')}Escríbeme</a>
          <a class="btn btn--ghost" href="{SITE['linkedin']}" target="_blank" rel="noopener">{icon('linkedin')}LinkedIn</a>
        </div>
      </section>

      <nav class="pager" aria-label="Otros proyectos">{pager}</nav>
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
    urls = [SITE["base_url"]] + [f"{SITE['base_url']}proyectos/{p['slug']}.html" for p in PROJECTS]
    entries = "\n".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n</urlset>\n",
        encoding="utf-8",
    )


# --------------------------------------------------------------------------- main
def validate() -> None:
    slugs = [p["slug"] for p in PROJECTS]
    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        raise ValueError(f"Slugs duplicados: {dupes}")
    for p in PROJECTS:
        if p["category"] not in CATEGORIES:
            raise ValueError(f"{p['slug']}: categoría desconocida '{p['category']}'")
        unknown = set(p["filters"]) - set(CATEGORIES)
        if unknown:
            raise ValueError(f"{p['slug']}: filtros desconocidos {unknown}")


def main() -> None:
    validate()
    out_dir = ROOT / "proyectos"
    out_dir.mkdir(exist_ok=True)
    expected = set()
    for i, p in enumerate(PROJECTS):
        target = out_dir / f"{p['slug']}.html"
        target.write_text(project_page(i, p), encoding="utf-8")
        expected.add(target.name)
    for stale in out_dir.glob("*.html"):
        if stale.name not in expected:
            stale.unlink()
            print(f"  eliminado {stale.relative_to(ROOT)} (ya no está en projects.toml)")
    build_index()
    build_sitemap()
    print(f"OK · {len(PROJECTS)} proyectos generados en proyectos/ · index.html y sitemap.xml actualizados")


if __name__ == "__main__":
    main()
