"""Step 2 - Cleaning: normalise raw extracted text before chunking.

Pure text transforms, no I/O of its own - `run_pipeline.py` calls
`clean_page_text()` on each page produced by extract.py. Kept as a separate
module so a developer can also run it standalone on already-extracted JSON:

    python clean.py --in data_raw/ --out data_clean/
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Common boilerplate lines that show up on every page of UPI documents and add
# no information (running headers/footers, page-number-only lines).
_BOILERPLATE_PATTERNS = [
    re.compile(r"^\s*halaman\s+\d+(\s*(dari|of)\s*\d+)?\s*$", re.IGNORECASE),
    re.compile(r"^\s*page\s+\d+(\s*of\s*\d+)?\s*$", re.IGNORECASE),
    re.compile(r"^\s*\d+\s*$"),  # a line that is only a page number
]

_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_MULTI_BLANK_LINE_RE = re.compile(r"\n{3,}")
_HYPHEN_LINEBREAK_RE = re.compile(r"(\w)-\n(\w)")  # "informa-\ntion" -> "informa" + "tion"
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def clean_page_text(text: str) -> str:
    """Normalise one page of extracted text. Idempotent - safe to re-run."""
    if not text:
        return ""

    text = _CONTROL_CHARS_RE.sub("", text)
    text = _HYPHEN_LINEBREAK_RE.sub(r"\1\2", text)

    lines = []
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            lines.append("")
            continue
        if any(p.match(line) for p in _BOILERPLATE_PATTERNS):
            continue
        line = _MULTI_SPACE_RE.sub(" ", line)
        lines.append(line)

    cleaned = "\n".join(lines)
    cleaned = _MULTI_BLANK_LINE_RE.sub("\n\n", cleaned)
    return cleaned.strip()


def clean_record(record: dict) -> dict:
    """Clean every page of one extract.py output record, in place-ish (returns new dict)."""
    cleaned_pages = [
        {**p, "text": clean_page_text(p["text"])}
        for p in record.get("pages", [])
    ]
    return {**record, "pages": cleaned_pages}


def run(in_dir: Path, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(in_dir.glob("*.json"))
    if not files:
        print(f"[!] No extracted JSON files found in {in_dir}")
        return 0

    count = 0
    for f in files:
        record = json.loads(f.read_text(encoding="utf-8"))
        cleaned = clean_record(record)
        (out_dir / f.name).write_text(
            json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        count += 1

    print(f"[OK] Cleaned {count} document(s) -> {out_dir}")
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean raw extracted PDF text.")
    parser.add_argument("--in", dest="in_dir", required=True, type=Path)
    parser.add_argument("--out", dest="out_dir", required=True, type=Path)
    args = parser.parse_args()

    if not args.in_dir.is_dir():
        print(f"[ERROR] --in does not exist: {args.in_dir}")
        return 1

    run(args.in_dir, args.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
