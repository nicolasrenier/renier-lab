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
  news.html                generated — see below
  news.json                source of truth for the news list
  contact.html             address and joining information
  404.html                 not-found page
  css/style.css            all styling
  js/main.js               nav, scroll animations, lightbox, publication filter
  images/                  hero/, science/, thumbs/science/, thumbs/news/,
                           lab/, team/, logos/ (funder logos)
  _headers                 Cloudflare Pages caching and security headers
  _redirects               redirects from the old Squarespace URLs
  robots.txt, sitemap.xml
tools/
  build_publications.py    regenerates the publication list from JSON
  build_news.py            regenerates the news lists from JSON
```

## Editing

**Text and people** — edit the HTML directly. Each page is plain, readable markup;
the nav and footer are repeated on every page, so a nav change means touching all of them.

**Publications** — never edit `publications.html` between the `PUBLICATIONS:START` and
`PUBLICATIONS:END` markers by hand; it is generated. Add the entry to
`site/publications.json` and run:

```bash
python3 tools/build_publications.py
```

Each entry needs `title`, `authors`, `journal`, `year` and `type`; `volume`, `pages`, `doi`
and `pmid` are optional. Titles link to the DOI when present, otherwise to PubMed. The script
also keeps the publication count in the page hero honest.

`type` decides the section, and has to be set by hand — it cannot be derived from the author
list, because co-corresponding authorship is not visible there:

| `type` | Section |
|---|---|
| `primary` | **From the Lab** — research from the lab |
| `note` | **From the Lab**, *Notes and Reviews* subsection — reviews and commentary from the lab |
| `previous` | **Previous Work** — first-author work predating the lab |
| `collaboration` | **Collaborations** — everything else |

Sections appear in that order. **Collaborations** is grouped under year headings; the lab's
own three sections are one continuous list, newest first, with the year in the citation —
with only a few papers each, a heading per year leaves them stranded. The `grouped` flag in
the script's `SECTIONS` table controls this per section.

The script refuses to build if an entry has a missing or unknown `type`, so a new paper
cannot slip in unclassified. The filter box hides a section heading when nothing in it
matches.

**Gallery images** — the science grid uses 800px-wide copies in
`site/images/thumbs/science/` for the tiles and the full-resolution file in
`site/images/science/` for the lightbox. When adding a science image, add both. Lab
photographs are already web-sized and used directly.

**News** — never edit the news lists in `news.html` or `index.html` by hand; the regions
between the `NEWS:START`/`NEWS:END` and `BRIEF:START`/`BRIEF:END` markers are generated.
Add the entry to `site/news.json` and run:

```bash
python3 tools/build_news.py
```

The file holds two kinds of entry, in one list:

```json
{"kind": "update", "date": "2026-04",
 "title": "Developmental vascular atlas published in Cell",
 "body":  "Our comprehensive 3D atlas ...",
 "image": "images/thumbs/news/cell-atlas-2026.jpg",
 "alt":   "Vascular labelling in a postnatal mouse brain",
 "frame": "person"}

{"kind": "brief", "date": "2026-10", "tag": "talk",
 "text": "Invited talk at the FENS Forum, Vienna."}
```

`update` is a full item with a heading, body and optional thumbnail. `brief` is a one-liner
for talks, press mentions, short pieces and events; its `tag` is `talk`, `press`, `note` or
`event`, each with its own colour. `frame` is `person` (circular, for photographs of people),
`logo` (fitted on white) or omitted (cropped square).

`date` is `"YYYY-MM"` or `"YYYY"` — both the sort key and the source of the displayed label.
Entries are sorted newest first; a bare year sorts below the months of the same year, and
same-date entries keep the order they have in the file, so reorder those by moving them.
Add `"display"` to override a label.

The news page gets everything; the home page gets the latest three updates and four brief
items (`HOME_UPDATES` / `HOME_BRIEFS` in the script). `title`, `body` and `text` are written
out as raw HTML so links work — which also means a stray `<` will break the page. `alt` is
plain text and is escaped for you. Accented characters go in as themselves; the files are
UTF-8.

**News thumbnails** — each news item carries an 88px thumbnail from
`site/images/thumbs/news/`, cut to 240x240. Science crops fill the tile; funder logos
from `site/images/logos/` are fitted on a white ground instead (add `news-thumb--logo`
to the wrapper), and photographs of people use `news-thumb--person` for the circular
frame. Team photographs are already 400x400 and are referenced directly.

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
