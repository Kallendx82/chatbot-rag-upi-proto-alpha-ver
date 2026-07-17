"""Step 1 - Extraction: PDF -> raw per-page text, with OCR fallback.

Uses PyMuPDF (fitz) to pull the text layer directly. Pages that come back
with almost no text (scanned images, no OCR layer) are rendered to an image
and passed through Tesseract OCR instead.

Usage (standalone):
    python extract.py --pdf-dir path/to/new_pdfs --out data_raw/

Output: one JSON file per PDF in --out, named "<doc_id>.json":
    {
      "doc_id": "…",
      "source": "absolute/path/to/file.pdf",
      "title": "file",
      "pages": [{"page": 1, "text": "…", "method": "text"}, ...]
    }

If --sources-dir is given, the original PDF is copied there as
"<doc_id>.pdf" and "source" points at that copy instead of the original
location - so the chatbot's PDF viewer keeps working even if the folder you
ingested from later gets moved, renamed, or deleted.

Requires: pymupdf, pytesseract (+ the Tesseract binary on PATH), Pillow.
OCR is optional - if pytesseract/Tesseract is not installed, scanned pages
are skipped with a warning instead of crashing the whole run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

MIN_CHARS_PER_PAGE = 20  # below this, treat the page as "no text layer" -> OCR
OCR_LANG = "ind+eng"  # Indonesian + English; requires both traineddata files


def make_doc_id(source_path: Path) -> str:
    """Stable 16-hex-char id derived from the absolute file path.

    Matches the convention already used in chunks_meta.json (see existing
    records: 16 lowercase hex chars). Re-ingesting the same file path always
    yields the same doc_id, which is what embed.py uses to detect "this file
    was already ingested, replace its chunks" instead of duplicating them.
    """
    return hashlib.sha1(str(source_path.resolve()).encode("utf-8")).hexdigest()[:16]


def _ocr_page(page, dpi: int = 200) -> str:
    """Render a PDF page to an image and OCR it. Returns "" if OCR unavailable."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        print("  [WARN] pytesseract/Pillow not installed - skipping OCR for this page.")
        return ""

    pix = page.get_pixmap(dpi=dpi)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    try:
        return pytesseract.image_to_string(img, lang=OCR_LANG)
    except Exception as exc:  # Tesseract binary missing, bad lang pack, etc.
        print(f"  [WARN] OCR failed ({exc}). Is the Tesseract binary installed "
              f"and on PATH, with the '{OCR_LANG}' language packs?")
        return ""


def extract_pdf(pdf_path: Path, sources_dir: Path | None = None) -> dict[str, Any]:
    """Extract every page of one PDF, OCR-ing pages with no usable text layer.

    doc_id is always derived from the ORIGINAL path (so re-ingesting the same
    source file is recognised as an update, not a duplicate) even when
    sources_dir makes a permanent copy and "source" ends up pointing there.
    """
    import fitz  # PyMuPDF

    doc_id = make_doc_id(pdf_path)

    doc = fitz.open(str(pdf_path))
    pages: list[dict[str, Any]] = []
    ocr_count = 0

    for i, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        method = "text"
        if len(text) < MIN_CHARS_PER_PAGE:
            ocr_text = _ocr_page(page).strip()
            if ocr_text:
                text = ocr_text
                method = "ocr"
                ocr_count += 1
        pages.append({"page": i, "text": text, "method": method})

    doc.close()
    if ocr_count:
        print(f"  [*] {pdf_path.name}: {ocr_count}/{len(pages)} page(s) needed OCR")

    source = str(pdf_path.resolve())
    if sources_dir is not None:
        sources_dir.mkdir(parents=True, exist_ok=True)
        dest = sources_dir / f"{doc_id}.pdf"
        shutil.copy2(pdf_path, dest)
        source = str(dest.resolve())

    return {
        "doc_id": doc_id,
        "source": source,
        "title": pdf_path.stem,
        "pages": pages,
    }


def run(pdf_dir: Path, out_dir: Path, sources_dir: Path | None = None) -> list[Path]:
    """Extract every PDF under pdf_dir (recursive), one JSON per file in out_dir.

    When sources_dir is given, each original PDF is also copied there (named
    "<doc_id>.pdf") so the chatbot keeps serving it even if pdf_dir is later
    moved or deleted - see extract_pdf().
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = sorted(pdf_dir.rglob("*.pdf"))
    if not pdf_files:
        print(f"[!] No PDF files found under {pdf_dir}")
        return []

    written: list[Path] = []
    for pdf_path in pdf_files:
        print(f"[*] Extracting {pdf_path.relative_to(pdf_dir)} ...")
        try:
            record = extract_pdf(pdf_path, sources_dir=sources_dir)
        except Exception as exc:
            print(f"  [ERROR] Failed to extract {pdf_path}: {exc}")
            continue
        out_path = out_dir / f"{record['doc_id']}.json"
        out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(out_path)

    if sources_dir is not None:
        print(f"[OK] Extracted {len(written)}/{len(pdf_files)} PDF(s) -> {out_dir} "
              f"(originals copied to {sources_dir})")
    else:
        print(f"[OK] Extracted {len(written)}/{len(pdf_files)} PDF(s) -> {out_dir}")
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract text from new PDFs (with OCR fallback).")
    parser.add_argument("--pdf-dir", required=True, type=Path, help="Folder containing new PDFs (searched recursively)")
    parser.add_argument("--out", required=True, type=Path, help="Output folder for raw extraction JSON")
    parser.add_argument("--sources-dir", type=Path, default=None,
                         help="If given, copy each original PDF here as <doc_id>.pdf")
    args = parser.parse_args()

    if not args.pdf_dir.is_dir():
        print(f"[ERROR] --pdf-dir does not exist: {args.pdf_dir}")
        return 1

    run(args.pdf_dir, args.out, sources_dir=args.sources_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
