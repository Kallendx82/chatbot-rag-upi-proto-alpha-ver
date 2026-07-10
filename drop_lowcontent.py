"""drop_lowcontent.py
=============================================================================
Remove low-content (unreadable) chunks from the live index. These are chunks
that are mostly digits/punctuation (raw number-table dumps) — they are already
filtered from the LLM prompt by prompt._is_low_content, so removing them does
NOT change any answer; it only cleans up retrieval ranks and UI citations.

Safety:
  - Reuses stored vectors via faiss reconstruct (no re-embed, no torch).
  - Backs up the live index dir before writing.
  - NEVER drops curated reference / per-prodi UKT chunks (ref_* / ukt_*), even
    if they somehow matched, and never drops web/pdf prose.

Definition of low-content (matches prompt._is_low_content spirit):
  len(text) >= 60 AND letters/len < 0.35.
=============================================================================
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import faiss
import numpy as np

INDEX_DIR = Path(r"D:\Project\RAG_UPI\Dataset\_pipeline\index")
PIPE = INDEX_DIR.parent

PROTECT_PREFIXES = ("ref_", "ukt_")   # curated chunks — never drop


def letters_ratio(t: str) -> float:
    return sum(c.isalpha() for c in t) / max(1, len(t))


def is_low_content(row: dict) -> bool:
    cid = str(row.get("chunk_id", ""))
    if any(cid.startswith(p) for p in PROTECT_PREFIXES):
        return False
    doc = str(row.get("doc_id", ""))
    if any(doc.startswith(p) for p in PROTECT_PREFIXES):
        return False
    t = row.get("text", "") or ""
    return len(t) >= 60 and letters_ratio(t) < 0.35


def main() -> None:
    t0 = time.time()
    idx_path = INDEX_DIR / "faiss.index"
    meta_path = INDEX_DIR / "chunks_meta.json"
    info_path = INDEX_DIR / "index_info.json"

    index = faiss.read_index(str(idx_path))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    n = index.ntotal
    if n != len(meta):
        raise SystemExit(f"index/meta mismatch: {n} vs {len(meta)}")

    keep_mask = np.array([not is_low_content(r) for r in meta])
    n_drop = int((~keep_mask).sum())
    print(f"[drop] total={n:,}  low-content to drop={n_drop:,}  keep={int(keep_mask.sum()):,}")
    if n_drop == 0:
        print("[drop] nothing to drop.")
        return

    # Reconstruct kept vectors (no re-embed) and rebuild a flat IP index.
    all_vecs = index.reconstruct_n(0, n)
    kept_vecs = np.ascontiguousarray(all_vecs[keep_mask]).astype("float32")
    new_index = faiss.IndexFlatIP(index.d)
    new_index.add(kept_vecs)
    kept_meta = [m for m, k in zip(meta, keep_mask) if k]

    backup = PIPE / f"index_backup_{time.strftime('%Y%m%d_%H%M%S')}"
    shutil.copytree(INDEX_DIR, backup)
    print(f"[drop] backed up live index -> {backup}")

    faiss.write_index(new_index, str(idx_path))
    meta_path.write_text(json.dumps(kept_meta, ensure_ascii=False), encoding="utf-8")
    info = json.loads(info_path.read_text(encoding="utf-8"))
    info["n_vectors"] = int(new_index.ntotal)
    info["includes"] = (info.get("includes", "") + " (low-content pruned)").strip()
    info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")

    print(f"[drop] index {n:,} -> {new_index.ntotal:,} in {time.time()-t0:.1f}s")
    print("[drop] restart the backend to load it.")


if __name__ == "__main__":
    main()
