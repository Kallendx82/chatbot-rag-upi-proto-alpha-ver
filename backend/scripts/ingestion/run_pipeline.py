"""End-to-end ingestion: extract -> clean -> chunk -> embed, in one command.

    python run_pipeline.py --pdf-dir "D:\\new_pdfs\\BiroSDM" --category "BiroSDM"

Intermediate artefacts (raw/cleaned/chunked JSON) are written to a work
folder (default: scripts/ingestion/_work/<run timestamp>/) so you can
inspect what was extracted/chunked before it gets merged into the live
index - useful the first few times you run this, or when debugging a
document that OCR'd badly.

Add --keep-work to keep that folder afterwards (default: deleted on success).
"""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chunk as chunk_step        # noqa: E402
import clean as clean_step        # noqa: E402
import embed as embed_step        # noqa: E402
import extract as extract_step    # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Full PDF ingestion pipeline (extract -> clean -> chunk -> embed).")
    parser.add_argument("--pdf-dir", required=True, type=Path, help="Folder of new PDFs (searched recursively)")
    parser.add_argument("--category", required=True, help="Category label to store on every chunk (e.g. 'BiroSDM', 'FIP')")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "app" / "data",
        help="Folder holding faiss.index / chunks_meta.json / index_info.json (default: backend/app/data)",
    )
    parser.add_argument("--work-dir", type=Path, default=None, help="Where to write intermediate JSON (default: auto-generated under _work/)")
    parser.add_argument("--keep-work", action="store_true", help="Don't delete the intermediate JSON after a successful run")
    args = parser.parse_args()

    if not args.pdf_dir.is_dir():
        print(f"[ERROR] --pdf-dir does not exist: {args.pdf_dir}")
        return 1

    work_dir = args.work_dir or (
        Path(__file__).resolve().parent / "_work" / dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    raw_dir, clean_dir, chunks_dir = work_dir / "raw", work_dir / "clean", work_dir / "chunks"

    print(f"=== Ingestion pipeline: {args.pdf_dir} (category: {args.category}) ===\n")

    print("--- Step 1/4: Extract (PDF -> text, OCR fallback) ---")
    extract_step.run(args.pdf_dir, raw_dir)

    print("\n--- Step 2/4: Clean ---")
    clean_step.run(raw_dir, clean_dir)

    print("\n--- Step 3/4: Chunk ---")
    chunk_step.run(clean_dir, chunks_dir, args.category)

    print("\n--- Step 4/4: Embed + merge into live index ---")
    rc = embed_step.run(chunks_dir, args.data_dir)

    if rc == 0 and not args.keep_work:
        shutil.rmtree(work_dir, ignore_errors=True)
    elif rc == 0:
        print(f"\n[*] Intermediate files kept at: {work_dir}")

    print("\n=== Done. ===" if rc == 0 else "\n=== Finished with errors - see above. ===")
    return rc


if __name__ == "__main__":
    sys.exit(main())
