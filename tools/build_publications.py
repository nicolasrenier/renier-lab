#!/usr/bin/env python3
"""Regenerate the publication list in site/publications.html from site/publications.json.

publications.json is the source of truth. Add or edit entries there, then run:

    python3 tools/build_publications.py

Each entry: title, authors, type, journal, year, volume, pages, doi, pmid.
Only `title`, `authors`, `journal`, `year` and `type` are required.

`type` decides which section the paper lands in, and cannot be worked out from the
author list (co-corresponding authorship is not visible there), so it is set by hand:

    primary        research from the lab            -> "From the Lab"
    preprint       a preprint from the lab          -> "From the Lab",
                                                       "Preprints" subsection
    note           reviews and commentary from the  -> "From the Lab", "Notes and
                   lab                                 Reviews", below Preprints
    previous       first-author work predating the  -> "Previous Work"
                   lab
    collaboration  everything else                  -> "Collaborations"

The vocabulary is also written down in the "_memo" block at the top of the JSON,
which the script ignores.

Sections keep that order. Collaborations are grouped under year headings; the
lab's own sections are one flat list, newest first, with the year in the citation.
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

# section key -> (heading, subsection heading or None, group by year?)
# The lab's own sections read as one continuous list: with only a handful of
# papers each, a year heading per entry leaves them stranded. Collaborations are
# numerous enough that the year headings help you find your way.
SECTIONS = [
    ("primary", "From the Lab", None, False),
    ("preprint", None, "Preprints", False),       # nested inside the section above
    ("note", None, "Notes and Reviews", False),   # nested too, below Preprints
    ("previous", "Previous Work", None, False),
    ("collaboration", "Collaborations", None, True),
]
TYPES = {key for key, *_ in SECTIONS}


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


def pub_items(pubs, indent):
    """The <div class="pub-item"> blocks, in the order given."""
    p = " " * indent
    out = []
    for pub in pubs:
        title = html.escape(pub["title"])
        url = link_for(pub)
        titled = (
            f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">{title}</a>'
            if url else title
        )
        out += [f'{p}<div class="pub-item">',
                f'{p}  <p class="pub-title">{titled}</p>',
                f'{p}  <p class="pub-authors">{html.escape(pub["authors"])}</p>',
                f'{p}  <p class="pub-journal">{html.escape(citation(pub))}</p>',
                f'{p}</div>']
    return "\n".join(out)


def flat_list(pubs, indent):
    """One continuous list, newest first, no year headings."""
    p = " " * indent
    pubs = sorted(pubs, key=lambda x: -int(x["year"]))   # stable within a year
    return "\n".join([f'{p}<div class="pub-list fade-in">',
                       pub_items(pubs, indent + 2),
                       f'{p}</div>'])


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
        out.append(pub_items(by_year[year], indent + 4))
        out.append(f'{p}  </div>')
        out.append(f'{p}</div>')
    return "\n".join(out)


def render(pubs):
    unknown = {str(p.get("type")) for p in pubs} - TYPES
    if unknown:
        sys.exit("Unknown or missing type(s): " + ", ".join(sorted(unknown))
                 + ". Use one of: " + ", ".join(sorted(TYPES)) + ".")

    out = []
    for key, heading, sub, grouped in SECTIONS:
        group = [p for p in pubs if p["type"] == key]
        if not group:
            continue
        render_list = year_groups if grouped else flat_list
        if sub:                                   # nested in the open section
            out.append('        <div class="pub-subsection">')
            out.append(f'          <h3 class="pub-subsection-title">{html.escape(sub)}</h3>')
            out.append(render_list(group, 10))
            out.append('        </div>')
            continue
        if out:
            out.append('      </div>')            # close the previous section
        out.append('      <div class="pub-section">')
        out.append(f'        <h2 class="pub-section-title">{html.escape(heading)}</h2>')
        out.append(render_list(group, 8))
    out.append('      </div>')
    return "\n".join(out)


def load(path, key):
    """The JSON files carry a "_memo" block for whoever edits them; skip it."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data[key]


def main():
    pubs = load(JSON_PATH, "publications")
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
