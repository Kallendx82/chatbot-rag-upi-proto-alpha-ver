"""add_ukt_rows.py
=============================================================================
Add ONE high-signal chunk per study-program to the live index for exact UKT
lookups like "UKT Teknik Komputer golongan 4".

Problem: the UKT tables live as big multi-prodi chunks, so dense retrieval
favours prose and the LLM grabs the wrong prodi row. Fix: emit a dedicated,
natural-language chunk per prodi (with BOTH "golongan" and "kelompok/KEL"
wording) so retrieval and the LLM lock onto the exact program.

Source: the "Master" sheet of the two UKT Lampiran spreadsheets.
  - Lampiran NOMOR 4 → Jalur Seleksi Nasional (SNBP/SNBT), UKT only.
  - Lampiran NOMOR 5 → Jalur Seleksi Mandiri, UKT + IPI (uang pangkal).

Vectors for the new rows are embedded (e5, CPU) and APPENDED to the existing
faiss index + chunks_meta.json (no full rebuild).
=============================================================================
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import faiss
import numpy as np
import pandas as pd

from ingest_new_dataset import EMBED_MODEL, clean

ROOT = Path(r"D:\Project\RAG_UPI")
PMB = ROOT / "Dataset" / "PMB UPI" / "Biaya Pendidikan UPI Tahun Akademik 2025-2026"
INDEX_DIR = ROOT / "Dataset" / "_pipeline" / "index"

FILES = [
    {
        "path": PMB / "KEPUTUSAN REKTOR UNIVERSITAS PENDIDIKAN INDONESIA NOMOR 4-UN40-KU.00.00-2026"
                    / "Lampiran NOMOR 4-UN40-KU.00.00-2026.xlsx",
        "jalur": "Jalur Seleksi Nasional (SNBP dan SNBT)",
        "keputusan": "Keputusan Rektor UPI Nomor 4/UN40/KU.00.00/2026",
        "include_ipi": False,
    },
    {
        "path": PMB / "KEPUTUSAN REKTOR UNIVERSITAS PENDIDIKAN INDONESIA NOMOR 5-UN40-KU.00.00-2026"
                    / "Lampiran NOMOR 5-UN40-KU.00.00-2026.xlsx",
        "jalur": "Jalur Seleksi Mandiri",
        "keputusan": "Keputusan Rektor UPI Nomor 5/UN40/KU.00.00/2026",
        "include_ipi": True,
    },
]


def rp(v: str) -> str:
    v = clean(str(v))
    return f"Rp {v}" if v and v.lower() != "nan" else "-"


def build_rows() -> list[dict]:
    rows: list[dict] = []
    for spec in FILES:
        path = spec["path"]
        if not path.is_file():
            print(f"[ukt] MISSING: {path}")
            continue
        df = pd.read_excel(path, sheet_name="Master", header=0, dtype=str)
        cols = list(df.columns)
        # Column layout: No, Fakultas/Kampus, Jenjang, Nama Program Studi,
        # Kode Prodi, then alternating UKT KEL n / IPI KEL n.
        for _, r in df.iterrows():
            prodi = clean(str(r[cols[3]]))
            if not prodi or prodi.lower() == "nan":
                continue
            fakultas = clean(str(r[cols[1]]))
            jenjang = clean(str(r[cols[2]]))
            kode = clean(str(r[cols[4]]))
            ukt = [clean(str(r[cols[5 + (n - 1) * 2]])) for n in range(1, 9)]
            ipi = [clean(str(r[cols[6 + (n - 1) * 2]])) for n in range(1, 9)]

            ukt_line = "; ".join(
                f"golongan {n} (Kelompok {n} / UKT KEL {n}) = {rp(ukt[n-1])}"
                for n in range(1, 9)
            )
            text = (
                f"Uang Kuliah Tunggal (UKT) program studi {jenjang} {prodi} "
                f"(kode prodi {kode}), {fakultas}, Universitas Pendidikan "
                f"Indonesia (UPI), {spec['jalur']}, sesuai {spec['keputusan']}. "
                f"Besaran UKT per golongan/kelompok: {ukt_line}."
            )
            if spec["include_ipi"]:
                ipi_line = "; ".join(
                    f"golongan {n} = {rp(ipi[n-1])}" for n in range(1, 9)
                )
                text += (
                    f" Iuran Pengembangan Institusi (IPI / uang pangkal) per "
                    f"golongan/kelompok: {ipi_line}."
                )

            tag = "mandiri" if spec["include_ipi"] else "nasional"
            doc_id = f"ukt_{tag}_{kode}".lower()
            rows.append({
                "doc_id": doc_id,
                "source": str(path),
                "url": None,
                "title": f"UKT {prodi} — {spec['jalur']}",
                "category": "PMB UPI",
                "source_type": "xlsx",
                "page": 1,
                "section": "UKT per program studi",
                "text": text,
                "chunk_length": len(text),
                "chunk_index": 0,
                "chunk_id": f"{doc_id}::0",
                "keywords": ["ukt", "golongan", "kelompok", prodi.lower(), kode.lower()],
            })
    return rows


def main() -> None:
    t0 = time.time()
    rows = build_rows()
    print(f"[ukt] built {len(rows)} per-prodi chunks")
    if not rows:
        raise SystemExit("no rows built")

    # Embed (CPU is reliable here; GPU hit a pagefile limit earlier).
    from sentence_transformers import SentenceTransformer
    print("[ukt] loading embedder on cpu ...")
    model = SentenceTransformer(EMBED_MODEL, device="cpu")
    texts = ["passage: " + r["text"] for r in rows]
    vecs = model.encode(texts, batch_size=16, convert_to_numpy=True,
                        normalize_embeddings=True, show_progress_bar=True).astype("float32")

    # Append to the live index + metadata.
    idx_path = INDEX_DIR / "faiss.index"
    meta_path = INDEX_DIR / "chunks_meta.json"
    info_path = INDEX_DIR / "index_info.json"
    index = faiss.read_index(str(idx_path))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    before = index.ntotal
    if index.d != vecs.shape[1]:
        raise SystemExit(f"dim mismatch: index {index.d} vs new {vecs.shape[1]}")

    # De-dup: drop any prior chunk with the same chunk_id (idempotent re-runs).
    new_ids = {r["chunk_id"] for r in rows}
    keep = [m for m in meta if m.get("chunk_id") not in new_ids]
    if len(keep) != len(meta):
        # Rebuild vectors for kept rows via reconstruct, then re-add.
        print(f"[ukt] removing {len(meta)-len(keep)} previously-added UKT rows")
        all_vecs = index.reconstruct_n(0, before)
        keep_mask = [m.get("chunk_id") not in new_ids for m in meta]
        kept_vecs = np.ascontiguousarray(all_vecs[np.array(keep_mask)]).astype("float32")
        index = faiss.IndexFlatIP(index.d)
        index.add(kept_vecs)
        meta = keep

    index.add(vecs)
    meta.extend(rows)

    faiss.write_index(index, str(idx_path))
    meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    info = json.loads(info_path.read_text(encoding="utf-8"))
    info["n_vectors"] = int(index.ntotal)
    info["includes"] = (info.get("includes", "") + " + per-prodi UKT rows").strip(" +")
    info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")

    print(f"[ukt] index {before:,} -> {index.ntotal:,} vectors (+{len(rows)}) in {time.time()-t0:.1f}s")
    print("[ukt] restart the backend to load it.")


if __name__ == "__main__":
    main()
