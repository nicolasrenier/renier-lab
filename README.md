# renier-lab.com

Static website for the **Renier Lab — Laboratory of Structural Plasticity**, Paris Brain
Institute (ICM), Inserm / CNRS / Sorbonne Université.

No build step, no framework, no dependencies. `site/` is the deployed directory exactly
as it appears in the browser.

## Layout

```
site/                      what gets deployed
  index.html               home
  research.html            research themes and imaging approach
  team.html                current members and alumni
  publications.html        generated — see below
  publications.json        source of truth for the publication list
  resources.html           iDISCO+, ClearMap, LAMBADA
  gallery.html             science images and lab photographs
  news.html                lab updates
  contact.html             address and joining information
  404.html                 not-found page
  css/style.css            all styling
  js/main.js               nav, scroll animations, lightbox, publication filter
  images/                  hero/, science/, thumbs/science/, lab/, team/
  _headers                 Cloudflare Pages caching and security headers
  _redirects               redirects from the old Squarespace URLs
  robots.txt, sitemap.xml
tools/
  build_publications.py    regenerates the publication list from JSON
```

## Editing

**Text, people, news** — edit the HTML directly. Each page is plain, readable markup;
the nav and footer are repeated on every page, so a nav change means touching all of them.

**Publications** — never edit `publications.html` between the `PUBLICATIONS:START` and
`PUBLICATIONS:END` markers by hand; it is generated. Add the entry to
`site/publications.json` and run:

```bash
python3 tools/build_publications.py
```

Each entry needs `title`, `authors`, `journal` and `year`; `volume`, `pages`, `doi` and
`pmid` are optional. Titles link to the DOI when present, otherwise to PubMed. The script
also keeps the publication count in the page hero honest.

**Gallery images** — the science grid uses 800px-wide copies in
`site/images/thumbs/science/` for the tiles and the full-resolution file in
`site/images/science/` for the lightbox. When adding a science image, add both. Lab
photographs are already web-sized and used directly.

## Preview locally

```bash
cd site && python3 -m http.server 8000
```

Then open <http://localhost:8000>. Note that `_headers` and `_redirects` are Cloudflare
features and do nothing in this local server.

## Deployment

Cloudflare Workers, connected to this repository through Workers Builds. Pushing to `main`
deploys; other branches get their own preview URL.

`wrangler.jsonc` declares the whole thing: no server code, no build step — Cloudflare serves
`site/` as static assets, returns `site/404.html` for unknown paths, and resolves both
`/research` and `/research.html`. `site/_headers` and `site/_redirects` are read by Workers
and are not themselves served.

To deploy by hand from a checkout:

```bash
npx wrangler deploy
```
