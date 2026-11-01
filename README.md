# José Luis Pérez Lara · Portfolio

**Responsable Técnico E-commerce · Backend & Automation Engineer** · Córdoba, España · Remoto o reubicación

🌐 **Portfolio:** https://joseluixrax.github.io/Jose-Luis-Porfolio-Personal/
💼 **LinkedIn:** [in/jose-luis-perez-lara](https://www.linkedin.com/in/jose-luis-perez-lara/)
✉️ **Email:** [joseluisperez232003@gmail.com](mailto:joseluisperez232003@gmail.com)

---

## Sobre mí

Responsable técnico de la operación digital de **VapoSelección**, un e-commerce multicanal con tienda PrestaShop, venta en **4 marketplaces de Amazon** (ES · FR · DE · IT) y 3 tiendas físicas. Especializado en **backend, integración de APIs y automatización** de procesos críticos con Python, PHP y n8n, infraestructura propia con Docker e **IA aplicada** a procesos reales.

Formación: **Máster FP en Inteligencia Artificial y Big Data** y **CFGS en Desarrollo de Aplicaciones Web** (I.E.S. Gran Capitán).

## Proyectos

Cada proyecto tiene su propia página con el problema, la solución, la arquitectura, el stack, los retos técnicos y un fragmento de código.

| Proyecto | Área | Stack principal |
|---|---|---|
| [Sistema de gestión FBA para Amazon](https://joseluixrax.github.io/Jose-Luis-Porfolio-Personal/proyectos/sistema-fba-amazon.html) | E-commerce · Automatización | Python, Amazon SP-API, n8n, Pandas |
| [Migración de PrestaShop a contenedores](https://joseluixrax.github.io/Jose-Luis-Porfolio-Personal/proyectos/migracion-prestashop-docker.html) | Infraestructura | Docker Compose, Nginx, PHP 7.4, MariaDB |
| [Dashboard de ventas, márgenes y rotación](https://joseluixrax.github.io/Jose-Luis-Porfolio-Personal/proyectos/dashboard-ventas-almacen.html) | Datos & BI | PHP, SQL avanzado, Odoo API, n8n |
| [Traductor de catálogo con IA](https://joseluixrax.github.io/Jose-Luis-Porfolio-Personal/proyectos/traductor-catalogo-ia.html) | IA aplicada | Python, LLM API, PrestaShop |
| [Asistente de IA conectado al negocio (MCP)](https://joseluixrax.github.io/Jose-Luis-Porfolio-Personal/proyectos/asistente-ia-mcp.html) | IA aplicada | MCP, n8n, SP-API, Odoo |
| [Plataforma de automatización n8n + FastAPI](https://joseluixrax.github.io/Jose-Luis-Porfolio-Personal/proyectos/plataforma-automatizacion-n8n.html) | Automatización | n8n, FastAPI, Pandas, Nginx |
| [Reestructuración de la tienda PrestaShop](https://joseluixrax.github.io/Jose-Luis-Porfolio-Personal/proyectos/reestructuracion-prestashop.html) | E-commerce | PHP, PrestaShop 1.7, Smarty, SQL |
| [Segmentación de catálogo y pricing](https://joseluixrax.github.io/Jose-Luis-Porfolio-Personal/proyectos/segmentacion-catalogo-pricing.html) | Datos | Python, Pandas, openpyxl |
| [Implantación de Odoo ERP](https://joseluixrax.github.io/Jose-Luis-Porfolio-Personal/proyectos/implantacion-odoo-erp.html) | E-commerce · ERP | Odoo, PrestaShop, TPV, Verifactu |
| [AdvanceBoy: emulador de GBA para Android](https://joseluixrax.github.io/Jose-Luis-Porfolio-Personal/proyectos/advanceboy-emulador-gba.html) | Personal | Kotlin, C/JNI, mGBA, OpenGL ES |
| [Discord Voice AI](https://joseluixrax.github.io/Jose-Luis-Porfolio-Personal/proyectos/discord-voice-ai.html) | Personal · IA | Python, discord.py, Whisper, LLM |
| [Pokémon Draft Tournament](https://joseluixrax.github.io/Jose-Luis-Porfolio-Personal/proyectos/pokemon-draft-tournament.html) | Personal | JavaScript, PokeAPI |

## Stack

`Python` `PHP` `Node.js` `SQL` `Bash` · `MySQL/MariaDB` `PostgreSQL` `MongoDB` · `Docker` `Nginx` `Linux` `GitHub Actions` · `n8n` `Amazon SP-API` `Odoo` `MCP` · `Pandas` `NumPy` `Machine Learning` `LLMs` · `PrestaShop` `JavaScript` `React` `Next.js`

---

## Cómo está hecho este portfolio

Sitio estático sin frameworks ni dependencias en el navegador (HTML, CSS y JavaScript), publicado con **GitHub Pages**. Las páginas de proyecto se generan desde un único fichero de contenido con un script de Python sin dependencias externas.

```
├── index.html                 Portada (las tarjetas de proyecto se insertan al generar)
├── proyectos/                 Páginas de cada proyecto (generadas, no editar a mano)
├── content/projects.toml      ← Contenido de todos los proyectos: se edita aquí
├── tools/build.py             Generador: TOML → HTML + sitemap.xml
├── tools/icons.py             Iconos SVG del sitio
└── assets/                    CSS, JS, imágenes y Prism (resaltado de código)
```

### Añadir o editar un proyecto

1. Edita `content/projects.toml` (cada proyecto es un bloque `[[projects]]`).
2. Genera el sitio:
   ```bash
   python3 tools/build.py      # Python 3.11+ (en 3.10: pip install tomli)
   ```
3. Revisa en local:
   ```bash
   python3 -m http.server 8000   # http://localhost:8000
   ```
4. Haz commit y push: GitHub Pages publica los cambios automáticamente.

### Publicación

En el repositorio: **Settings → Pages → Build and deployment → Deploy from a branch → `main` / `(root)`**.
