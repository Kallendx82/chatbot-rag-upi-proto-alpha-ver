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


def _table_to_paragraphs(table_data: list[list[str | None]]) -> str:
    """Convert extracted table rows into readable natural-language paragraphs.

    Strategy: detect header rows, then for each data row build a sentence
    like "Kegiatan: Awal Perkuliahan, Semester Ganjil: 24 Agustus 2026,
    Semester Genap: 25 Januari 2027". This makes table content searchable
    and understandable by the LLM without needing the visual grid layout.
    """
    if not table_data or len(table_data) < 2:
        return ""

    # Clean cells
    rows = [
        [(cell or "").replace("\n", " ").strip() for cell in row]
        for row in table_data
    ]

    # Build merged headers from first 1-3 rows
    # E.g. row0: [NO., KEGIATAN, _, SEMESTER, _, _, _, _, _]
    #      row1: [_,   _,        _, GANJIL,   _, _, GENAP, _, _]
    # -> headers per column index
    n_cols = len(rows[0])
    col_headers: list[str] = [""] * n_cols
    data_start = 0

    for ri in range(min(3, len(rows))):
        row = rows[ri]
        non_empty = [c for c in row if c]
        if not non_empty:
            data_start = ri + 1
            continue
        # Header row if most cells are short/uppercase/empty
        looks_header = sum(1 for c in row if not c or c.isupper() or c.replace(".", "").replace("/", "").strip() == "") > len(row) * 0.5
        if looks_header:
            for ci, cell in enumerate(row):
                if cell:
                    if col_headers[ci]:
                        col_headers[ci] += " " + cell
                    else:
                        # Span: if next cells are empty, this header covers them
                        col_headers[ci] = cell
                        # Fill empty subsequent columns with same header
                        for ci2 in range(ci + 1, n_cols):
                            if not row[ci2] and not col_headers[ci2]:
                                col_headers[ci2] = cell
                            else:
                                break
            data_start = ri + 1
        else:
            break

    # Override spanned headers with sub-headers from row 1
    # (e.g. SEMESTER spanned -> GANJIL/GENAP override specific cols)
    for ci in range(n_cols):
        if not col_headers[ci]:
            col_headers[ci] = f"Kolom {ci+1}"

    paragraphs: list[str] = []
    current_section = ""

    for row in rows[data_start:]:
        non_empty = [(ci, c) for ci, c in enumerate(row) if c]
        if not non_empty:
            continue

        # Section header: only 1-2 non-empty cells, short, looks like a label
        values = [c for _, c in non_empty if not c.rstrip(".").isdigit()]
        if len(values) == 1 and len(values[0]) < 60:
            current_section = values[0].rstrip(".")
            continue

        # Build "Header: value" pairs, skip numbering
        parts: list[str] = []
        for ci, cell in non_empty:
            if cell.rstrip(".").isdigit():
                continue
            header = col_headers[ci] if ci < len(col_headers) else ""
            if header and header.upper() != cell.upper():
                parts.append(f"{header}: {cell}")
            else:
                parts.append(cell)

        if parts:
            line = _parts_to_sentence(parts, current_section)
            paragraphs.append(line)

    return "\n".join(paragraphs)


def _parts_to_sentence(parts: list[str], section: str) -> str:
    """Turn structured 'Header: value' pairs into a natural-language sentence."""
    kegiatan = ""
    details: list[str] = []

    for p in parts:
        if ": " in p:
            header, val = p.split(": ", 1)
            h = header.strip().upper()
            if h == "KEGIATAN" or h == "KEGIATAN REGISTRASI":
                kegiatan = val.strip()
            elif "SEMESTER" in h or "TAHUN" in h or "TANGGAL" in h:
                label = header.strip().title()
                details.append(f"{label} tanggal {val.strip()}")
            else:
                details.append(f"{header.strip()}: {val.strip()}")
        else:
            details.append(p)

    if kegiatan and details:
        sentence = f"{kegiatan} dijadwalkan pada {', '.join(details)}."
    elif kegiatan:
        sentence = f"{kegiatan}."
    else:
        sentence = ", ".join(details) + "."

    if section:
        sentence = f"Bagian {section}: {sentence}"
    return sentence


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


def extract_pdf(pdf_path: Path, sources_dir: Path | None = None, title_override: str | None = None) -> dict[str, Any]:
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
    table_count = 0

    for i, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        method = "text"
        if len(text) < MIN_CHARS_PER_PAGE:
            ocr_text = _ocr_page(page).strip()
            if ocr_text:
                text = ocr_text
                method = "ocr"
                ocr_count += 1

        # Extract tables and convert to readable paragraphs
        try:
            tabs = page.find_tables()
            if tabs.tables:
                table_paragraphs = []
                for table in tabs.tables:
                    para = _table_to_paragraphs(table.extract())
                    if para:
                        table_paragraphs.append(para)
                if table_paragraphs:
                    table_text = "\n\n".join(table_paragraphs)
                    # Replace the raw text with table paragraphs for pages
                    # dominated by tables (>50% of page area)
                    total_table_area = sum(
                        (t.bbox[2] - t.bbox[0]) * (t.bbox[3] - t.bbox[1])
                        for t in tabs.tables
                    )
                    page_area = page.rect.width * page.rect.height
                    if page_area > 0 and total_table_area / page_area > 0.2:
                        # Page is mostly table — use structured paragraphs only
                        text = table_text
                    else:
                        # Mixed page — append table paragraphs after text
                        text = f"{text}\n\n{table_text}"
                    method = "text+table"
                    table_count += 1
        except Exception:
            pass  # table extraction is best-effort

        pages.append({"page": i, "text": text, "method": method})

    doc.close()
    if ocr_count:
        print(f"  [*] {pdf_path.name}: {ocr_count}/{len(pages)} page(s) needed OCR")
    if table_count:
        print(f"  [*] {pdf_path.name}: {table_count}/{len(pages)} page(s) had tables converted to paragraphs")

    source = str(pdf_path.resolve())
    if sources_dir is not None:
        sources_dir.mkdir(parents=True, exist_ok=True)
        dest = sources_dir / f"{doc_id}.pdf"
        shutil.copy2(pdf_path, dest)
        # Store as relative path from the backend root for portability
        try:
            backend_root = sources_dir.resolve().parent.parent.parent
            source = str(dest.resolve().relative_to(backend_root))
        except ValueError:
            source = str(dest.resolve())

    return {
        "doc_id": doc_id,
        "source": source,
        "title": title_override or pdf_path.stem,
        "pages": pages,
    }


def run(pdf_dir: Path, out_dir: Path, sources_dir: Path | None = None, title_override: str | None = None) -> list[Path]:
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
            record = extract_pdf(pdf_path, sources_dir=sources_dir, title_override=title_override)
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
