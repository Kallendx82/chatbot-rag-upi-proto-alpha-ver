"""add_reference_facts.py
=============================================================================
Append a few concise, high-signal REFERENCE chunks for common "list" questions
whose answer already exists in the corpus but is buried inside a large document
and therefore ranks poorly / gets cut across chunk boundaries.

Each fact below is grounded VERBATIM in an official UPI document (attributed via
`source`), just re-expressed as one compact chunk so retrieval + a small LLM
return the COMPLETE list. Same idea as the per-prodi UKT chunks.

Idempotent: re-running replaces any chunk with the same chunk_id.
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
PEDOMAN = ROOT / "Dataset" / "Pedoman-Penyelenggaran-Pendidikan-UPI-Tahun-2024-rev.pdf"

# Each fact: a short id, a display title, the source file, and the text.
FACTS = [
    {
        "id": "ref_fakultas_upi",
        "title": "Daftar Fakultas di UPI",
        "source": str(PEDOMAN),
        "category": "Referensi UPI",
        "text": (
            "Daftar fakultas di Universitas Pendidikan Indonesia (UPI). "
            "Berdasarkan Pedoman Penyelenggaraan Pendidikan UPI Tahun 2024, UPI "
            "memiliki 9 (sembilan) fakultas, Sekolah Pascasarjana, dan 5 kampus "
            "daerah. Fakultas/jurusan di UPI yaitu: "
            "1. Fakultas Ilmu Pendidikan (FIP); "
            "2. Fakultas Pendidikan Ilmu Pengetahuan Sosial (FPIPS); "
            "3. Fakultas Pendidikan Bahasa dan Sastra (FPBS); "
            "4. Fakultas Pendidikan Matematika dan Ilmu Pengetahuan Alam (FPMIPA); "
            "5. Fakultas Pendidikan Teknologi dan Kejuruan (FPTK); "
            "6. Fakultas Pendidikan Olahraga dan Kesehatan (FPOK); "
            "7. Fakultas Pendidikan Ekonomi dan Bisnis (FPEB); "
            "8. Fakultas Pendidikan Seni dan Desain (FPSD); "
            "9. Fakultas Kedokteran (FK). "
            "Selain itu terdapat Sekolah Pascasarjana (SPs) serta 5 Kampus UPI di "
            "Daerah, yaitu Kampus Cibiru, Kampus Sumedang, Kampus Tasikmalaya, "
            "Kampus Purwakarta, dan Kampus Serang."
        ),
        "keywords": ["fakultas", "daftar fakultas", "fip", "fpmipa", "fpteb", "upi"],
    },
    {
        "id": "ref_kampus_upi",
        "title": "Kampus UPI di Daerah",
        "source": str(PEDOMAN),
        "category": "Referensi UPI",
        "text": (
            "Lokasi kampus Universitas Pendidikan Indonesia (UPI). Kampus utama "
            "UPI adalah Kampus Bumi Siliwangi di Kota Bandung. Selain itu, UPI "
            "memiliki 5 (lima) kampus daerah, yaitu: Kampus UPI di Cibiru "
            "(Bandung), Kampus UPI di Sumedang, Kampus UPI di Tasikmalaya, "
            "Kampus UPI di Purwakarta, dan Kampus UPI di Serang. UPI juga "
            "menyelenggarakan Sekolah Pascasarjana (SPs) untuk program magister "
            "dan doktor."
        ),
        "keywords": ["kampus", "kampus daerah", "cibiru", "sumedang", "serang", "upi"],
    },
]


def build_rows() -> list[dict]:
    rows = []
    for f in FACTS:
        rows.append({
            "doc_id": f["id"],
            "source": f["source"],
            "url": None,
            "title": f["title"],
            "category": f["category"],
            "source_type": "pdf",
            "page": 1,
            "section": "Referensi ringkas",
            "text": f["text"],
            "chunk_length": len(f["text"]),
            "chunk_index": 0,
            "chunk_id": f"{f['id']}::0",
            "keywords": f["keywords"],
        })
    return rows


def main() -> None:
    t0 = time.time()
    rows = build_rows()
    print(f"[ref] {len(rows)} reference chunks")

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBED_MODEL, device="cpu")
    vecs = model.encode(["passage: " + r["text"] for r in rows], batch_size=8,
                        convert_to_numpy=True, normalize_embeddings=True,
                        show_progress_bar=False).astype("float32")

    idx_path = INDEX_DIR / "faiss.index"
    meta_path = INDEX_DIR / "chunks_meta.json"
    info_path = INDEX_DIR / "index_info.json"
    index = faiss.read_index(str(idx_path))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    before = index.ntotal

    # Idempotent: drop prior versions of these chunk_ids (rebuild via reconstruct).
    new_ids = {r["chunk_id"] for r in rows}
    if any(m.get("chunk_id") in new_ids for m in meta):
        all_vecs = index.reconstruct_n(0, before)
        mask = np.array([m.get("chunk_id") not in new_ids for m in meta])
        kept = np.ascontiguousarray(all_vecs[mask]).astype("float32")
        index = faiss.IndexFlatIP(index.d)
        index.add(kept)
        meta = [m for m in meta if m.get("chunk_id") not in new_ids]
        print(f"[ref] replaced existing reference chunks")

    index.add(vecs)
    meta.extend(rows)
    faiss.write_index(index, str(idx_path))
    meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    info = json.loads(info_path.read_text(encoding="utf-8"))
    info["n_vectors"] = int(index.ntotal)
    info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(f"[ref] index {before:,} -> {index.ntotal:,} (+{len(rows)}) in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
