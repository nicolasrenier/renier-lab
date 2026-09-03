#!/usr/bin/env python3
"""Regenerate the publication list in site/publications.html from site/publications.json.

publications.json is the source of truth. Add or edit entries there, then run:

    python3 tools/build_publications.py

Each entry: title, authors, type, journal, year, volume, pages, doi, pmid.
Only `title`, `authors`, `journal`, `year` and `type` are required.

`type` decides which section the paper lands in, and cannot be worked out from the
author list (co-corresponding authorship is not visible there), so it is set by hand:

    primary        research from the lab            -> "From the Lab"
    note           reviews and commentary from the  -> "From the Lab",
                   lab                                 "Notes and Reviews" subsection
    previous       first-author work predating the  -> "Previous Work"
                   lab
    collaboration  everything else                  -> "Collaborations"

Sections keep that order; within each, papers are grouped by year, newest first.
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

# section key -> (heading, subsection heading or None)
SECTIONS = [
    ("primary", "From the Lab", None),
    ("note", None, "Notes and Reviews"),      # nested inside the section above
    ("previous", "Previous Work", None),
    ("collaboration", "Collaborations", None),
]
TYPES = {key for key, _, _ in SECTIONS}


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


def year_groups(pubs, indent):
    """Year-grouped <div>s, newest year first."""
    by_year = defaultdict(list)
    for pub in pubs:
        by_year[str(pub["year"])].append(pub)

    p = " " * indent
    out = []
    for year in sorted(by_year, key=int, reverse=True):
        out.append(f'{p}<div class="pub-year-group fade-in">')
        out.append(f'{p}  <h4 class="pub-year">{html.escape(year)}</h4>')
        out.append(f'{p}  <div class="pub-list">')
        for pub in by_year[year]:
            title = html.escape(pub["title"])
            url = link_for(pub)
            titled = (
                f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">{title}</a>'
                if url else title
            )
            out.append(f'{p}    <div class="pub-item">')
            out.append(f'{p}      <p class="pub-title">{titled}</p>')
            out.append(f'{p}      <p class="pub-authors">{html.escape(pub["authors"])}</p>')
            out.append(f'{p}      <p class="pub-journal">{html.escape(citation(pub))}</p>')
            out.append(f'{p}    </div>')
        out.append(f'{p}  </div>')
        out.append(f'{p}</div>')
    return "\n".join(out)


def render(pubs):
    unknown = {str(p.get("type")) for p in pubs} - TYPES
    if unknown:
        sys.exit("Unknown or missing type(s): " + ", ".join(sorted(unknown))
                 + ". Use one of: " + ", ".join(sorted(TYPES)) + ".")

    out = []
    for key, heading, sub in SECTIONS:
        group = [p for p in pubs if p["type"] == key]
        if not group:
            continue
        if sub:                                   # nested in the open section
            out.append('        <div class="pub-subsection">')
            out.append(f'          <h3 class="pub-subsection-title">{html.escape(sub)}</h3>')
            out.append(year_groups(group, 10))
            out.append('        </div>')
            out.append('      </div>')            # closes the section it belongs to
            continue
        if out and not out[-1].startswith('      </div>'):
            out.append('      </div>')            # close the previous section
        out.append('      <div class="pub-section">')
        out.append(f'        <h2 class="pub-section-title">{html.escape(heading)}</h2>')
        out.append(year_groups(group, 8))
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
