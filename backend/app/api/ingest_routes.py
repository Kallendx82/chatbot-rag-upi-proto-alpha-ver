"""Admin-only PDF ingestion endpoint.

Allows authenticated admin users to upload PDF files through the web
interface.  The uploaded file is saved to a temporary directory, then the
full ingestion pipeline (extract → clean → chunk → embed) is executed
synchronously.  The updated index is hot-reloaded so new documents are
searchable immediately without restarting the server.

Security: guarded by ``get_admin_user`` — only users with ``is_admin=True``
can call this endpoint.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel

from app.api.auth_routes import get_admin_user
from app.core.config import Settings, get_settings
from app.core.container import Container, get_container

router = APIRouter()


class IngestResponse(BaseModel):
    message: str
    filename: str
    category: str
    subcategory: str | None = None
    chunks_added: int | None = None


@router.post(
    "/ingest",
    response_model=IngestResponse,
    tags=["admin"],
    summary="Upload & ingest a PDF into the knowledge base (admin only)",
)
async def ingest_pdf(
    file: UploadFile = File(..., description="PDF file to ingest"),
    category: str = Form(..., description="Category label, e.g. 'PPID UPI', 'PMB UPI'"),
    subcategory: str | None = Form(None, description="Optional sub-category label, e.g. 'Kalender-Akademik-2026'"),
    title: str | None = Form(None, description="Optional document title (defaults to filename)"),
    publish_year: int | None = Form(None, description="Optional publication year of the document, e.g. 2026"),
    chunk_size: int | None = Form(None, description="Max chars per chunk (default auto: 350 for tables, 900 for text)"),
    overlap: int | None = Form(None, description="Overlap sentences between chunks (default 1)"),
    admin: dict[str, Any] = Depends(get_admin_user),
    settings: Settings = Depends(get_settings),
    container: Container = Depends(get_container),
) -> IngestResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Hanya file PDF yang diterima.",
        )

    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "Ukuran file maksimal 50 MB.",
        )

    # Resolve to absolute path so file writes never depend on the server's CWD.
    data_dir = settings.faiss_index_file.resolve().parent

    tmp_dir = Path(tempfile.mkdtemp(prefix="rag_ingest_"))
    pdf_dir = tmp_dir / "pdfs"
    pdf_dir.mkdir()

    try:
        dest = pdf_dir / file.filename
        with open(dest, "wb") as f:
            content = await file.read()
            f.write(content)

        import importlib
        import sys

        scripts_dir = str(Path(__file__).resolve().parents[2] / "scripts" / "ingestion")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        import extract as extract_step
        import clean as clean_step
        import chunk as chunk_step
        import embed as embed_step
        # Always reload so that changes to the ingestion scripts take effect
        # without a full backend restart.
        for _mod in (extract_step, clean_step, chunk_step, embed_step):
            importlib.reload(_mod)

        work_dir = tmp_dir / "work"
        raw_dir, clean_dir, chunks_dir = work_dir / "raw", work_dir / "clean", work_dir / "chunks"
        sources_dir = data_dir / "sources"

        extract_step.run(pdf_dir, raw_dir, sources_dir=sources_dir, title_override=title)
        clean_step.run(raw_dir, clean_dir)
        chunk_step.run(
            clean_dir, chunks_dir, category,
            subcategory=subcategory,
            max_chars_override=chunk_size,
            overlap_override=overlap,
            publish_year=publish_year,
        )
        rc = embed_step.run(chunks_dir, data_dir)

        if rc != 0:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Pipeline embedding gagal. Periksa log server.",
            )

        import json
        chunks_added = 0
        for cf in chunks_dir.glob("*.json"):
            data = json.loads(cf.read_text(encoding="utf-8"))
            chunks_added += len(data) if isinstance(data, list) else len(data.get("chunks", []))

        container.reload_vectorstore()

        return IngestResponse(
            message=f"Berhasil mengingest '{file.filename}' ke kategori '{category}'" + (f" ({subcategory})" if subcategory else "") + ".",
            filename=file.filename,
            category=category,
            subcategory=subcategory,
            chunks_added=chunks_added,
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


class DocumentItem(BaseModel):
    doc_id: str
    title: str
    category: str | None = None
    subcategory: str | None = None
    chunks_count: int
    created_at: str | None = None


@router.get(
    "/documents",
    response_model=list[DocumentItem],
    tags=["admin"],
    summary="List all ingested documents and their chunk counts (admin only)",
)
def list_documents(
    admin: dict[str, Any] = Depends(get_admin_user),
    settings: Settings = Depends(get_settings),
) -> list[DocumentItem]:
    import json
    meta_path = settings.chunks_meta_file.resolve()
    if not meta_path.is_file():
        return []

    meta: list[dict[str, Any]] = json.loads(meta_path.read_text(encoding="utf-8"))
    doc_map: dict[str, dict[str, Any]] = {}
    data_dir = meta_path.parent

    for m in meta:
        did = str(m.get("doc_id") or m.get("title") or "unknown")
        title = str(m.get("title") or did)
        category = m.get("category")
        subcategory = m.get("subcategory")
        source = m.get("source")
        
        if did not in doc_map:
            created_at = None
            if source:
                p = Path(source)
                if not p.is_absolute():
                    p = data_dir / "sources" / p.name
                if p.is_file():
                    import datetime
                    created_at = datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
            
            doc_map[did] = {
                "doc_id": did,
                "title": title,
                "category": category,
                "subcategory": subcategory,
                "chunks_count": 0,
                "created_at": created_at,
            }
        doc_map[did]["chunks_count"] += 1

    return list(doc_map.values())


class DeleteDocumentResponse(BaseModel):
    message: str
    doc_id: str
    chunks_removed: int
    total_chunks_remaining: int


@router.delete(
    "/documents",
    response_model=DeleteDocumentResponse,
    tags=["admin"],
    summary="Delete a document and all its chunks from the FAISS index (admin only)",
)
def delete_document(
    doc_id: str,
    admin: dict[str, Any] = Depends(get_admin_user),
    settings: Settings = Depends(get_settings),
    container: Container = Depends(get_container),
) -> DeleteDocumentResponse:
    import json
    import faiss
    import numpy as np

    data_dir = settings.faiss_index_file.resolve().parent
    faiss_path = data_dir / "faiss.index"
    meta_path = data_dir / "chunks_meta.json"
    info_path = data_dir / "index_info.json"

    if not faiss_path.is_file() or not meta_path.is_file():
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Vector store belum diinisialisasi atau file tidak ditemukan.",
        )

    index = faiss.read_index(str(faiss_path))
    meta: list[dict[str, Any]] = json.loads(meta_path.read_text(encoding="utf-8"))

    if index.ntotal != len(meta):
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Korupsi index terdeteksi: {index.ntotal} vector vs {len(meta)} metadata.",
        )

    keep_mask: list[bool] = []
    new_meta: list[dict[str, Any]] = []
    removed_count = 0

    for m in meta:
        m_did = str(m.get("doc_id") or "")
        m_title = str(m.get("title") or "")
        if m_did == doc_id or m_title == doc_id or doc_id.lower() in m_title.lower():
            keep_mask.append(False)
            removed_count += 1
        else:
            keep_mask.append(True)
            new_meta.append(m)

    if removed_count == 0:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Dokumen dengan ID/Judul '{doc_id}' tidak ditemukan.",
        )

    all_vectors = index.reconstruct_n(0, index.ntotal)
    kept_vectors = all_vectors[np.array(keep_mask, dtype=bool)]

    new_index = faiss.IndexFlatIP(index.d)
    if len(kept_vectors) > 0:
        new_index.add(kept_vectors)

    # Backup before write
    backup_dir = data_dir / "backups" / f"del_{doc_id[:10]}_{int(data_dir.stat().st_mtime)}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for p in (faiss_path, meta_path, info_path):
        if p.is_file():
            shutil.copy2(p, backup_dir / p.name)

    # Safe write
    faiss_tmp = faiss_path.with_suffix(".index.tmp")
    meta_tmp = meta_path.with_suffix(".json.tmp")
    info_tmp = info_path.with_suffix(".json.tmp")

    faiss.write_index(new_index, str(faiss_tmp))
    meta_tmp.write_text(json.dumps(new_meta, ensure_ascii=False, indent=2), encoding="utf-8")

    info_data = {}
    if info_path.is_file():
        info_data = json.loads(info_path.read_text(encoding="utf-8"))
    info_data["n_vectors"] = new_index.ntotal
    info_tmp.write_text(json.dumps(info_data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _safe_replace(src: Path, dst: Path) -> None:
        try:
            src.replace(dst)
        except PermissionError:
            if dst.exists():
                dst.unlink()
            shutil.move(str(src), str(dst))

    _safe_replace(faiss_tmp, faiss_path)
    _safe_replace(meta_tmp, meta_path)
    _safe_replace(info_tmp, info_path)

    # Hot reload vectorstore in memory
    container.reload_vectorstore()

    return DeleteDocumentResponse(
        message=f"Berhasil menghapus dokumen '{doc_id}' dan {removed_count} chunk terkait.",
        doc_id=doc_id,
        chunks_removed=removed_count,
        total_chunks_remaining=new_index.ntotal,
    )

