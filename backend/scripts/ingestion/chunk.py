"""Step 3 - Chunking: cleaned per-page text -> schema-aligned chunk records.

Chunks are produced per PDF page (so the "page" field always matches the
physical page the PDF viewer will jump to), using a recursive paragraph ->
sentence splitter so no chunk exceeds MAX_CHARS. The first heading-looking
line on a page becomes that page's "section" label.

Output chunk shape matches what app/rag/vectorstore.py expects to load
(see chunks_meta.json):
    {
      "doc_id", "source", "url", "title", "category", "source_type",
      "page", "section", "text", "chunk_length", "chunk_index",
      "chunk_id", "keywords"
    }

Usage (standalone):
    python chunk.py --in data_clean/ --out data_chunks/ --category "BiroSDM"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

MAX_CHARS = 900       # soft ceiling per chunk
MIN_CHARS = 80        # merge trailing fragments smaller than this into the previous chunk
OVERLAP_SENTENCES = 1  # carry the last sentence of a chunk into the next, for context continuity

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_HEADING_RE = re.compile(
    r"^(BAB\s+[IVXLCDM]+|[0-9]+(\.[0-9]+)*\s+[A-Z]|[A-Z][A-Z\s]{4,60})$"
)

_STOPWORDS = {
    # Indonesian
    "yang", "dan", "di", "ke", "dari", "untuk", "pada", "dengan", "adalah",
    "ini", "itu", "atau", "sebagai", "dalam", "akan", "oleh", "juga", "dapat",
    "tidak", "para", "serta", "telah", "secara", "maka", "sudah", "harus",
    "bagi", "seperti", "jika", "karena", "agar", "saat", "setiap",
    # English
    "the", "and", "for", "with", "that", "this", "from", "are", "was",
    "were", "have", "has", "will", "shall", "can", "not", "all", "any",
}
_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z\-]{3,}")


def _is_heading(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 80 or line.endswith((".", ",", ";")):
        return False
    return bool(_HEADING_RE.match(line))


def _find_section(page_text: str) -> str | None:
    for line in page_text.split("\n"):
        if _is_heading(line):
            return line.strip()
    return None


def _split_sentences(paragraph: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(paragraph) if s.strip()]


def split_into_chunks(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Recursively pack paragraphs (falling back to sentences) into <= max_chars windows."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    units: list[str] = []
    for p in paragraphs:
        units.extend([p] if len(p) <= max_chars else _split_sentences(p))

    chunks: list[str] = []
    current = ""
    for unit in units:
        candidate = f"{current} {unit}".strip() if current else unit
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        # a single unit longer than max_chars (rare) is kept whole rather than
        # cut mid-word - downstream embedding truncates, but no data is lost.
        current = unit

    if current:
        chunks.append(current)

    # Merge a too-small trailing fragment into the previous chunk instead of
    # shipping a near-empty chunk (common on the last paragraph of a page).
    if len(chunks) >= 2 and len(chunks[-1]) < MIN_CHARS:
        chunks[-2] = f"{chunks[-2]} {chunks[-1]}".strip()
        chunks.pop()

    # Light overlap: prefix each chunk (after the first) with the previous
    # chunk's last sentence, so retrieval near a chunk boundary still has
    # context on both sides.
    if OVERLAP_SENTENCES and len(chunks) > 1:
        for i in range(1, len(chunks)):
            prev_sentences = _split_sentences(chunks[i - 1])
            if prev_sentences:
                overlap = " ".join(prev_sentences[-OVERLAP_SENTENCES:])
                if not chunks[i].startswith(overlap):
                    chunks[i] = f"{overlap} {chunks[i]}".strip()

    return chunks


def extract_keywords(text: str, top_n: int = 8) -> list[str]:
    """Best-effort keyword extraction: frequency over stopword-filtered words.

    Deliberately dependency-free (no NLP library) - good enough for the
    existing UI, which only displays these as hint chips, not for ranking.
    """
    freq: dict[str, int] = {}
    for word in _WORD_RE.findall(text.lower()):
        if word in _STOPWORDS:
            continue
        freq[word] = freq.get(word, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:top_n]]


def chunk_document(record: dict[str, Any], category: str, source_type: str = "pdf") -> list[dict[str, Any]]:
    """Turn one cleaned extract.py record into a flat list of chunk dicts."""
    doc_id = record["doc_id"]
    chunks: list[dict[str, Any]] = []
    chunk_index = 0

    for page in record.get("pages", []):
        page_text = page.get("text", "")
        if not page_text.strip():
            continue
        section = _find_section(page_text)
        for piece in split_into_chunks(page_text):
            chunks.append({
                "doc_id": doc_id,
                "source": record["source"],
                "url": record.get("url"),
                "title": record.get("title", doc_id),
                "category": category,
                "source_type": source_type,
                "page": page["page"],
                "section": section,
                "text": piece,
                "chunk_length": len(piece),
                "chunk_index": chunk_index,
                "chunk_id": f"{doc_id}::{chunk_index}",
                "keywords": extract_keywords(piece),
            })
            chunk_index += 1

    return chunks


def run(in_dir: Path, out_dir: Path, category: str) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(in_dir.glob("*.json"))
    if not files:
        print(f"[!] No cleaned JSON files found in {in_dir}")
        return 0

    total_chunks = 0
    for f in files:
        record = json.loads(f.read_text(encoding="utf-8"))
        chunks = chunk_document(record, category=category)
        (out_dir / f.name).write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        total_chunks += len(chunks)
        print(f"  [*] {record.get('title', f.stem)}: {len(chunks)} chunk(s)")

    print(f"[OK] Chunked {len(files)} document(s) into {total_chunks} chunk(s) -> {out_dir}")
    return total_chunks


def main() -> int:
    parser = argparse.ArgumentParser(description="Chunk cleaned PDF text into schema-aligned records.")
    parser.add_argument("--in", dest="in_dir", required=True, type=Path)
    parser.add_argument("--out", dest="out_dir", required=True, type=Path)
    parser.add_argument("--category", required=True, help="Category label stored on every chunk (e.g. 'BiroSDM')")
    args = parser.parse_args()

    if not args.in_dir.is_dir():
        print(f"[ERROR] --in does not exist: {args.in_dir}")
        return 1

    run(args.in_dir, args.out_dir, args.category)
    return 0


if __name__ == "__main__":
    sys.exit(main())
