#!/usr/bin/env python3
"""Regenerate the news lists in site/news.html and site/index.html from site/news.json.

news.json is the source of truth. Add or edit entries there, then run:

    python3 tools/build_news.py

Two kinds of entry:

  {"kind": "update", "date": "2026-04",
   "title": "Developmental vascular atlas published in Cell",
   "body":  "Our comprehensive 3D atlas ...",
   "image": "images/thumbs/news/cell-atlas-2026.jpg",   # optional
   "alt":   "Vascular labelling in a postnatal mouse brain",
   "frame": "person"}                                    # person | logo | omit

  {"kind": "brief", "date": "2026-10", "tag": "talk",
   "text": "Invited talk at the FENS Forum, Vienna."}

`date` is "YYYY-MM" or "YYYY"; it is both the sort key and the source of the
displayed label ("Apr 2026" / "2026"). Add "display" to override the label.
Entries are sorted newest first; within one date, file order is kept, so
reorder same-date entries by moving them in the JSON.

`title`, `body` and `text` are written through as raw HTML, so links and
entities work — and so a stray "<" will break the page. Everything else is
escaped.

Brief tags: talk, press, note, event.
"""
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
JSON_PATH = SITE / "news.json"

HOME_UPDATES = 3      # how many of each the home page shows
HOME_BRIEFS = 4

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
TAGS = {"talk": "Talk", "press": "Press", "note": "Note", "event": "Event"}


def sort_key(entry):
    """Newest first. A bare year sorts below the months of that same year,
    which is how the hand-written list already read."""
    y, _, m = entry["date"].partition("-")
    return (-int(y), -int(m or 0))


def label(entry):
    if entry.get("display"):
        return entry["display"]
    y, _, m = entry["date"].partition("-")
    return f"{MONTHS[int(m) - 1]} {y}" if m else y


def render_update(e, indent, fade):
    p = " " * indent
    cls = "news-item fade-in" if fade else "news-item"
    out = [f'{p}<div class="{cls}">',
           f'{p}  <span class="news-date">{html.escape(label(e))}</span>']
    if e.get("image"):
        frame = {"person": " news-thumb--person", "logo": " news-thumb--logo"}.get(e.get("frame"), "")
        out.append(f'{p}  <div class="news-thumb{frame}"><img src="{html.escape(e["image"], quote=True)}" '
                   f'alt="{html.escape(e.get("alt", ""), quote=True)}" loading="lazy" decoding="async"></div>')
    out += [f'{p}  <div class="news-content">',
            f'{p}    <h3>{e["title"]}</h3>',
            f'{p}    <p>{e["body"]}</p>',
            f'{p}  </div>',
            f'{p}</div>']
    return "\n".join(out)


def render_brief(e, indent):
    p = " " * indent
    tag = e.get("tag", "note")
    if tag not in TAGS:
        sys.exit(f'Unknown brief tag {tag!r} on {e["date"]}. Known tags: {", ".join(TAGS)}.')
    return "\n".join([
        f'{p}<li class="brief-item">',
        f'{p}  <div class="brief-meta"><span class="brief-tag brief-tag--{tag}">{TAGS[tag]}</span>'
        f'<span class="brief-date">{html.escape(label(e))}</span></div>',
        f'{p}  <p>{e["text"]}</p>',
        f'{p}</li>',
    ])


def replace_region(page_text, name, body, path):
    """Swap whatever sits between <!-- NAME:START ... --> and <!-- NAME:END -->."""
    start_tag, end_tag = f"<!-- {name}:START", f"<!-- {name}:END -->"
    if start_tag not in page_text or end_tag not in page_text:
        sys.exit(f"Markers {start_tag}...  and {end_tag} not found in {path}.")
    head, rest = page_text.split(start_tag, 1)
    close = rest.index("-->") + 3
    marker, tail = start_tag + rest[:close], rest[close:].split(end_tag, 1)[1]
    indent = " " * (len(head) - head.rfind("\n") - 1)
    return f"{head}{marker}\n{body}\n{indent}{end_tag}{tail}"


def main():
    entries = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    for e in entries:
        if not re.fullmatch(r"\d{4}(-\d{2})?", e.get("date", "")):
            sys.exit(f'Bad date {e.get("date")!r} — expected "YYYY-MM" or "YYYY".')
    entries.sort(key=sort_key)          # stable: same-date entries keep file order

    updates = [e for e in entries if e["kind"] == "update"]
    briefs = [e for e in entries if e["kind"] == "brief"]
    unknown = {e["kind"] for e in entries} - {"update", "brief"}
    if unknown:
        sys.exit(f'Unknown kind(s): {", ".join(sorted(unknown))}. Use "update" or "brief".')

    for path, ups, brs, indent, fade in [
        (SITE / "news.html", updates, briefs, 10, True),
        (SITE / "index.html", updates[:HOME_UPDATES], briefs[:HOME_BRIEFS], 10, False),
    ]:
        page = path.read_text(encoding="utf-8")
        page = replace_region(page, "NEWS",
                              "\n\n".join(render_update(e, indent, fade) for e in ups), path)
        page = replace_region(page, "BRIEF",
                              "\n".join(render_brief(e, indent + 2) for e in brs), path)
        path.write_text(page, encoding="utf-8")
        print(f"Wrote {len(ups)} updates and {len(brs)} brief items to {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
