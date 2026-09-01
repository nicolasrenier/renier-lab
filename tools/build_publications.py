#!/usr/bin/env python3
"""Regenerate the publication list in site/publications.html from site/publications.json.

publications.json is the source of truth. Add or edit entries there, then run:

    python3 tools/build_publications.py

Each entry: title, authors, journal, year, volume, pages, doi, pmid.
Only `title`, `authors`, `journal` and `year` are required.
"""
import html
import json
import pathlib
import re
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
JSON_PATH = SITE / "publications.json"
HTML_PATH = SITE / "publications.html"

START = "<!-- PUBLICATIONS:START"
END = "<!-- PUBLICATIONS:END -->"


def citation(pub):
    """'Nat Commun 17, 1295 (2026)' — omitting whatever is missing."""
    bits = [pub["journal"]]
    if pub.get("volume"):
        bits.append(pub["volume"])
    line = " ".join(bits)
    if pub.get("pages"):
        line += f", {pub['pages']}"
    return f"{line} ({pub['year']})"


def link_for(pub):
    if pub.get("doi"):
        return f"https://doi.org/{pub['doi']}"
    if pub.get("pmid"):
        return f"https://pubmed.ncbi.nlm.nih.gov/{pub['pmid']}/"
    return None


def render(pubs):
    by_year = defaultdict(list)
    for pub in pubs:
        by_year[str(pub["year"])].append(pub)

    out = []
    for year in sorted(by_year, key=int, reverse=True):
        out.append('      <div class="pub-year-group fade-in">')
        out.append(f'        <h3 class="pub-year">{html.escape(year)}</h3>')
        out.append('        <div class="pub-list">')
        for pub in by_year[year]:
            title = html.escape(pub["title"])
            url = link_for(pub)
            titled = (
                f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">{title}</a>'
                if url else title
            )
            out.append('          <div class="pub-item">')
            out.append(f'            <p class="pub-title">{titled}</p>')
            out.append(f'            <p class="pub-authors">{html.escape(pub["authors"])}</p>')
            out.append(f'            <p class="pub-journal">{html.escape(citation(pub))}</p>')
            out.append('          </div>')
        out.append('        </div>')
        out.append('      </div>')
    return "\n".join(out)


def main():
    pubs = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    page = HTML_PATH.read_text(encoding="utf-8")

    if START not in page or END not in page:
        sys.exit(f"Markers not found in {HTML_PATH}. Expected {START}...  and {END}.")

    head, rest = page.split(START, 1)
    marker_close = rest.index("-->") + 3
    marker = START + rest[:marker_close]
    tail = rest[marker_close:].split(END, 1)[1]

    page = f"{head}{marker}\n{render(pubs)}\n      {END}{tail}"

    # Keep the hero blurb's count honest.
    page = re.sub(r"\b\d+ publications in leading journals",
                  f"{len(pubs)} publications in leading journals", page)

    HTML_PATH.write_text(page, encoding="utf-8")
    print(f"Wrote {len(pubs)} publications to {HTML_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
