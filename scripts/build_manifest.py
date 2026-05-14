#!/usr/bin/env python3
"""Regenerate data/manifest.json from files in data/articles/.

Filename convention: <CODE>_【<SERIES_NAME>】<TITLE>.md
  CODE = <SERIES_LETTER><NUMBER>, e.g. A01, D15, I06

Existing series metadata (color, icon) is preserved. Files that don't match
the convention are skipped and reported on stderr.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = ROOT / "data" / "articles"
MANIFEST_PATH = ROOT / "data" / "manifest.json"

FILENAME_RE = re.compile(r"^([A-Z])(\d+)_【([A-Z])([^】]+)】(.+)\.md$")

DEFAULT_COLOR = "#888"
DEFAULT_ICON = "📄"


def parse_filename(name: str):
    m = FILENAME_RE.match(name)
    if not m:
        return None
    code_letter, num, brace_letter, sname, title = m.groups()
    if code_letter != brace_letter:
        return None
    return {
        "code": f"{code_letter}{num}",
        "s": code_letter,
        "sname": sname,
        "title": title,
        "file": name,
    }


def sort_key(article: dict) -> tuple[str, int]:
    num = int(re.match(r"[A-Z](\d+)", article["code"]).group(1))
    return (article["s"], num)


def main() -> int:
    if not ARTICLES_DIR.is_dir():
        print(f"error: {ARTICLES_DIR} does not exist", file=sys.stderr)
        return 2

    existing: dict = {}
    if MANIFEST_PATH.exists():
        existing = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    series_meta = {s["id"]: s for s in existing.get("series", [])}

    articles: list[dict] = []
    skipped: list[tuple[str, str]] = []
    for path in sorted(ARTICLES_DIR.iterdir()):
        if not path.is_file():
            continue
        if not path.name.endswith(".md"):
            skipped.append((path.name, "missing .md extension"))
            continue
        parsed = parse_filename(path.name)
        if parsed is None:
            skipped.append((path.name, "filename does not match <CODE>_【<SERIES>】<TITLE>.md"))
            continue
        articles.append(parsed)

    articles.sort(key=sort_key)

    used_letters = {a["s"] for a in articles}
    for letter in sorted(used_letters):
        if letter not in series_meta:
            sname = next(a["sname"] for a in articles if a["s"] == letter)
            series_meta[letter] = {
                "id": letter,
                "name": sname,
                "color": DEFAULT_COLOR,
                "icon": DEFAULT_ICON,
            }

    series_list = [series_meta[letter] for letter in sorted(series_meta) if letter in used_letters]

    out = {
        "version": existing.get("version", "8.0"),
        "updated": date.today().isoformat(),
        "total": len(articles),
        "series": series_list,
        "articles": articles,
    }

    MANIFEST_PATH.write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {MANIFEST_PATH.relative_to(ROOT)}: {len(articles)} articles across {len(series_list)} series.")
    if skipped:
        print("Skipped files (did not match convention):", file=sys.stderr)
        for name, reason in skipped:
            print(f"  - {name}: {reason}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
