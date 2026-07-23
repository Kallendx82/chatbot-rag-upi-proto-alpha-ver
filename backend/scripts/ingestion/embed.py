"""Step 4 - Embedding: chunk records -> vectors, merged into the live FAISS index.

Reuses the app's own Embedder (app/rag/embedder.py) so new vectors are
produced with the exact same model + e5 prefixing as retrieval uses at
query time - a mismatch here would silently degrade search quality.

Safe re-ingestion: if a doc_id being embedded already exists in the index
(you're updating a PDF you ingested before), its old rows are dropped and
replaced rather than duplicated. This is done by reconstructing the kept
vectors straight out of the existing FAISS index (no re-embedding of
untouched documents) and only embedding what's new/changed.

Usage (standalone, after chunk.py):
    python embed.py --in data_chunks/ --data-dir ../app/data

Writes (after backing up the previous versions to <data-dir>/backups/):
    faiss.index, chunks_meta.json, index_info.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path
from typing import Any

# Make "app.*" importable regardless of the caller's cwd.
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


def _load_new_chunks(in_dir: Path) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for f in sorted(in_dir.glob("*.json")):
        chunks.extend(json.loads(f.read_text(encoding="utf-8")))
    return chunks


def _backup(data_dir: Path, files: list[str]) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = data_dir / "backups" / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    for name in files:
        src = data_dir / name
        if src.is_file():
            shutil.copy2(src, backup_dir / name)
    print(f"[OK] Backed up existing index files -> {backup_dir}")
    return backup_dir


def merge_and_embed(
    new_chunks: list[dict[str, Any]],
    existing_index,
    existing_meta: list[dict[str, Any]],
    embedder,
):
    """Return (new_faiss_index, new_meta_list) with new_chunks merged in.

    Existing vectors are reconstructed directly from the FAISS index (no
    re-embedding), so this stays fast even when the live index already holds
    tens of thousands of chunks.
    """
    import faiss
    import numpy as np

    new_doc_ids = {c["doc_id"] for c in new_chunks}
    keep_mask = [m["doc_id"] not in new_doc_ids for m in existing_meta]
    dropped = len(keep_mask) - sum(keep_mask)
    if dropped:
        print(f"[*] Replacing {dropped} existing chunk(s) that belong to the "
              f"{len(new_doc_ids)} document(s) being re-ingested.")

    kept_meta = [m for m, keep in zip(existing_meta, keep_mask) if keep]

    dim = embedder.dimension
    if existing_index.ntotal:
        all_vectors = existing_index.reconstruct_n(0, existing_index.ntotal)
        kept_vectors = all_vectors[np.array(keep_mask, dtype=bool)]
    else:
        kept_vectors = np.empty((0, dim), dtype="float32")

    print(f"[*] Embedding {len(new_chunks)} new chunk(s) with {embedder.model_name} ...")
    texts_to_embed = []
    for c in new_chunks:
        title = c.get("title", "")
        text = c["text"]
        if title and not text.startswith(title):
            texts_to_embed.append(f"{title}\n{text}")
        else:
            texts_to_embed.append(text)
    new_vectors = embedder.encode(texts_to_embed, kind="passage")

    combined_vectors = (
        np.vstack([kept_vectors, new_vectors]) if kept_vectors.shape[0] else new_vectors
    )
    combined_meta = kept_meta + new_chunks

    new_index = faiss.IndexFlatIP(dim)
    new_index.add(combined_vectors)

    assert new_index.ntotal == len(combined_meta), (
        f"Post-merge mismatch: {new_index.ntotal} vectors vs {len(combined_meta)} meta rows"
    )
    return new_index, combined_meta


def run(in_dir: Path, data_dir: Path) -> int:
    import faiss

    from app.core.config import Settings
    from app.rag.embedder import Embedder

    faiss_path = data_dir / "faiss.index"
    meta_path = data_dir / "chunks_meta.json"
    info_path = data_dir / "index_info.json"

    new_chunks = _load_new_chunks(in_dir)
    if not new_chunks:
        print(f"[!] No chunk files found in {in_dir} - nothing to embed.")
        return 0

    settings = Settings()
    embedder = Embedder(settings)
    embedder.load()
    if not embedder.ready:
        print(f"[ERROR] Could not load embedding model: {embedder.load_error}")
        return 1

    if faiss_path.is_file() and meta_path.is_file():
        existing_index = faiss.read_index(str(faiss_path))
        existing_meta = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        print("[*] No existing index found - creating a brand new one.")
        existing_index = faiss.IndexFlatIP(embedder.dimension)
        existing_meta = []

    _backup(data_dir, ["faiss.index", "chunks_meta.json", "index_info.json"])

    new_index, new_meta = merge_and_embed(new_chunks, existing_index, existing_meta, embedder)

    faiss.write_index(new_index, str(faiss_path))
    meta_path.write_text(json.dumps(new_meta, ensure_ascii=False), encoding="utf-8")
    info_path.write_text(
        json.dumps(
            {
                "embedding_model": embedder.model_name,
                "embedding_dim": embedder.dimension,
                "n_vectors": new_index.ntotal,
                "use_e5_prefixes": settings.use_e5_prefixes,
                "rebuilt_at": dt.datetime.now().isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"[OK] Index now has {new_index.ntotal} vectors ({len(new_chunks)} added/replaced) -> {data_dir}")
    print("[!] Restart the backend for the new documents to be searchable.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Embed chunked records and merge them into the live FAISS index.")
    parser.add_argument("--in", dest="in_dir", required=True, type=Path, help="Folder of chunk JSON files from chunk.py")
    parser.add_argument("--data-dir", required=True, type=Path, help="Folder holding faiss.index / chunks_meta.json / index_info.json (e.g. app/data)")
    args = parser.parse_args()

    if not args.in_dir.is_dir():
        print(f"[ERROR] --in does not exist: {args.in_dir}")
        return 1
    args.data_dir.mkdir(parents=True, exist_ok=True)

    return run(args.in_dir, args.data_dir)


if __name__ == "__main__":
    sys.exit(main())
