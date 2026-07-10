"""embed_reference_rows.py  (run with the backend VENV python — CPU torch)
=============================================================================
Stage 2: read reference_rows.json (built by build_reference_rows.py with system
python), embed with e5 on CPU, and APPEND to the live FAISS index + metadata.
Idempotent: replaces any existing chunk with the same chunk_id.

    "D:\\Project\\RAG_UPI\\Source code\\backend\\.venv\\Scripts\\python.exe" embed_reference_rows.py
=============================================================================
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import faiss
import numpy as np

from ingest_new_dataset import EMBED_MODEL

ROOT = Path(r"D:\Project\RAG_UPI")
INDEX_DIR = ROOT / "Dataset" / "_pipeline" / "index"
ROWS_JSON = ROOT / "reference_rows.json"


def main() -> None:
    t0 = time.time()
    rows = json.loads(ROWS_JSON.read_text(encoding="utf-8"))
    print(f"[embed] {len(rows)} reference rows from {ROWS_JSON.name}")

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBED_MODEL, device="cpu")
    vecs = model.encode(["passage: " + r["text"] for r in rows], batch_size=16,
                        convert_to_numpy=True, normalize_embeddings=True,
                        show_progress_bar=True).astype("float32")

    idx_path = INDEX_DIR / "faiss.index"
    meta_path = INDEX_DIR / "chunks_meta.json"
    info_path = INDEX_DIR / "index_info.json"
    index = faiss.read_index(str(idx_path))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    before = index.ntotal
    if index.d != vecs.shape[1]:
        raise SystemExit(f"dim mismatch {index.d} vs {vecs.shape[1]}")

    # Idempotent: drop prior versions of these chunk_ids via reconstruct.
    new_ids = {r["chunk_id"] for r in rows}
    if any(m.get("chunk_id") in new_ids for m in meta):
        all_vecs = index.reconstruct_n(0, before)
        mask = np.array([m.get("chunk_id") not in new_ids for m in meta])
        kept = np.ascontiguousarray(all_vecs[mask]).astype("float32")
        index = faiss.IndexFlatIP(index.d)
        index.add(kept)
        meta = [m for m in meta if m.get("chunk_id") not in new_ids]
        print(f"[embed] replaced {int((~mask).sum())} existing reference chunks")

    index.add(vecs)
    meta.extend(rows)
    faiss.write_index(index, str(idx_path))
    meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    info = json.loads(info_path.read_text(encoding="utf-8"))
    info["n_vectors"] = int(index.ntotal)
    info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(f"[embed] index {before:,} -> {index.ntotal:,} in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
