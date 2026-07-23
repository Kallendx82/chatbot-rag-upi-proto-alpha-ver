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
    title: str | None = Form(None, description="Optional document title (defaults to filename)"),
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

    data_dir = Path(settings.faiss_index_path).parent

    tmp_dir = Path(tempfile.mkdtemp(prefix="rag_ingest_"))
    pdf_dir = tmp_dir / "pdfs"
    pdf_dir.mkdir()

    try:
        dest = pdf_dir / file.filename
        with open(dest, "wb") as f:
            content = await file.read()
            f.write(content)

        import sys
        scripts_dir = str(Path(__file__).resolve().parents[2] / "scripts" / "ingestion")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        import extract as extract_step
        import clean as clean_step
        import chunk as chunk_step
        import embed as embed_step

        work_dir = tmp_dir / "work"
        raw_dir, clean_dir, chunks_dir = work_dir / "raw", work_dir / "clean", work_dir / "chunks"
        sources_dir = data_dir / "sources"

        extract_step.run(pdf_dir, raw_dir, sources_dir=sources_dir, title_override=title)
        clean_step.run(raw_dir, clean_dir)
        chunk_step.run(
            clean_dir, chunks_dir, category,
            max_chars_override=chunk_size,
            overlap_override=overlap,
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
            message=f"Berhasil mengingest '{file.filename}' ke kategori '{category}'.",
            filename=file.filename,
            category=category,
            chunks_added=chunks_added,
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
