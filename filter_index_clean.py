"""filter_index_clean.py
=============================================================================
Build a clean, UPI-student-focused index by FILTERING the full combined index
(web scraping + PDF + docx/xlsx) instead of re-embedding.

Source : Dataset/_pipeline/index_backup_20260704_135855  (83,785 vectors:
         web md + pdf + xlsx/docx — the full corpus before the chunk-size
         experiments shrank the live index to 1,226).

Dropped:
  1. National research-funding noise (Daftar Penerima Pendanaan, BIMA,
     Kosabangsa, Panduan Penelitian) — reuses ingest_new_dataset.is_noise.
  2. BiroSDM lecturer-staffing data (FORMASI DOSEN ...) — HR data that is
     irrelevant to students/applicants and was dominating retrieval.

Vectors for the kept rows are RECONSTRUCTED from the source FAISS index (no
re-embedding), so this runs in ~1-2 minutes on CPU. Writes the result to the
live index/ dir (backing up whatever is there first).
=============================================================================
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import faiss
import numpy as np

from ingest_new_dataset import EMBED_MODEL, is_noise

ROOT = Path(r"D:\Project\RAG_UPI")
PIPE = ROOT / "Dataset" / "_pipeline"
SRC_DIR = PIPE / "index_backup_20260704_135855"   # full combined index
INDEX_DIR = PIPE / "index"                          # live index (target)


def is_biro_sdm_staffing(row: dict) -> bool:
    """Lecturer-recruitment / HR formation data — noise for a student chatbot."""
    cat = (row.get("category") or "").lower()
    if cat == "birosdm":
        return True
    title = (row.get("title") or "").lower()
    return title.startswith("formasi") or "formasi dosen" in title


def log(m: str) -> None:
    print(f"[filter] {m}", flush=True)


def main() -> None:
    t0 = time.time()
    src_faiss = SRC_DIR / "faiss.index"
    src_meta = SRC_DIR / "chunks_meta.json"
    log(f"loading source index: {src_faiss}")
    index = faiss.read_index(str(src_faiss))
    meta = json.loads(src_meta.read_text(encoding="utf-8"))
    n = index.ntotal
    log(f"source: {n:,} vectors, {len(meta):,} metadata rows")
    if n != len(meta):
        raise SystemExit(f"index/meta mismatch: {n} vs {len(meta)}")

    # Decide which rows to keep.
    keep_idx: list[int] = []
    dropped_noise = 0
    dropped_biro = 0
    for i, row in enumerate(meta):
        if is_noise(row):
            dropped_noise += 1
            continue
        if is_biro_sdm_staffing(row):
            dropped_biro += 1
            continue
        keep_idx.append(i)
    log(f"dropped {dropped_noise:,} national-noise + {dropped_biro:,} BiroSDM staffing")
    log(f"keeping {len(keep_idx):,} chunks")

    # Reconstruct kept vectors (no re-embed) and rebuild a flat IP index.
    log("reconstructing vectors from source index ...")
    all_vecs = index.reconstruct_n(0, n)               # (n, dim) float32
    kept_vecs = np.ascontiguousarray(all_vecs[keep_idx]).astype("float32")
    dim = kept_vecs.shape[1]
    new_index = faiss.IndexFlatIP(dim)
    new_index.add(kept_vecs)
    kept_meta = [meta[i] for i in keep_idx]
    log(f"new index: {new_index.ntotal:,} vectors, dim={dim}")

    # Back up whatever is currently live, then write the clean index.
    if INDEX_DIR.exists():
        backup = PIPE / f"index_backup_{time.strftime('%Y%m%d_%H%M%S')}"
        shutil.copytree(INDEX_DIR, backup)
        log(f"backed up live index -> {backup}")
        shutil.rmtree(INDEX_DIR)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    faiss.write_index(new_index, str(INDEX_DIR / "faiss.index"))
    (INDEX_DIR / "chunks_meta.json").write_text(
        json.dumps(kept_meta, ensure_ascii=False), encoding="utf-8")
    (INDEX_DIR / "index_info.json").write_text(json.dumps({
        "embedding_model": EMBED_MODEL,
        "embedding_dim": int(dim),
        "n_vectors": int(new_index.ntotal),
        "use_e5_prefixes": True,
        "rebuilt_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "includes": "web + pdf + docx/xlsx, minus national-noise & BiroSDM staffing",
    }, indent=2), encoding="utf-8")

    log("=" * 60)
    log(f"DONE in {time.time()-t0:.1f}s — clean index = {new_index.ntotal:,} vectors.")
    log("Restart the backend to load it.")


if __name__ == "__main__":
    main()
