"""FAISS vector store: loading, integrity checks, and retrieval.

Loads the three artefacts produced by 03_vectorstore_rag_evaluation.ipynb:
  - faiss.index        the FAISS index (IndexFlatIP on normalised vectors)
  - chunks_meta.json   chunk metadata, row-aligned to the index
  - index_info.json    model name + dim recorded at build time

The class is deliberately a thin adapter over FAISS. Swapping to Chroma later
means writing a class with the same `search()` / `ready` / `info` surface;
nothing else in the backend needs to change.
"""
from __future__ import annotations

import json
import re
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.core.logging import get_logger
from app.rag.embedder import Embedder

logger = get_logger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    """Lowercase word tokenizer shared by BM25 indexing and querying."""
    return _TOKEN_RE.findall((text or "").lower())


def _rrf_fuse(rankings: list[list[int]], k0: int = 60) -> list[int]:
    """Reciprocal Rank Fusion: merge several ranked row-id lists into one."""
    score: dict[int, float] = defaultdict(float)
    for ranking in rankings:
        for rank, row in enumerate(ranking, start=1):
            score[row] += 1.0 / (k0 + rank)
    return [row for row, _ in sorted(score.items(), key=lambda x: x[1], reverse=True)]


class VectorStoreError(RuntimeError):
    """Raised when the vector store cannot serve retrieval requests."""


class FaissVectorStore:
    """Loads a FAISS index + chunk metadata and serves top-k retrieval."""

    def __init__(self, settings: Settings, embedder: Embedder) -> None:
        self._settings = settings
        self._embedder = embedder
        self._index = None
        self._meta: list[dict[str, Any]] = []
        self._info: dict[str, Any] = {}
        self._bm25 = None  # BM25 keyword index (built at load if hybrid enabled)
        self._lock = threading.Lock()
        self._load_error: str | None = None

    # -- lifecycle ---------------------------------------------------------
    def load(self) -> None:
        """Load index + metadata. Idempotent. Records failure instead of raising."""
        if self._index is not None or self._load_error is not None:
            return
        with self._lock:
            if self._index is not None or self._load_error is not None:
                return
            try:
                self._do_load()
            except Exception as exc:  # noqa: BLE001
                # Include the exception TYPE (MemoryError etc. often have an empty
                # message) and log the full traceback to backend.log for diagnosis.
                self._load_error = f"{type(exc).__name__}: {exc}".rstrip(": ")
                logger.exception("Vector store load failed (%s)", type(exc).__name__)

    def _do_load(self) -> None:
        import faiss

        idx_path = self._settings.faiss_index_file
        meta_path = self._settings.chunks_meta_file
        info_path = self._settings.index_info_file

        # --- existence checks with actionable messages ---
        missing = [str(p) for p in (idx_path, meta_path) if not p.exists()]
        if missing:
            raise VectorStoreError(
                "Missing vector store files: "
                + ", ".join(missing)
                + ". Run 03_vectorstore_rag_evaluation.ipynb and copy its "
                "index/ artefacts to the paths in your .env file."
            )

        t0 = time.time()
        index = faiss.read_index(str(idx_path))
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        info = {}
        if info_path.exists():
            info = json.loads(info_path.read_text(encoding="utf-8"))
        else:
            logger.warning("index_info.json not found - skipping model check.")

        # --- integrity checks ---
        if not isinstance(meta, list):
            raise VectorStoreError("chunks_meta.json must be a JSON list.")
        if index.ntotal != len(meta):
            raise VectorStoreError(
                f"Index/metadata mismatch: {index.ntotal} vectors vs "
                f"{len(meta)} metadata records. The index and metadata are "
                "out of sync - rebuild both together."
            )
        recorded_model = info.get("embedding_model")
        if recorded_model and recorded_model != self._settings.embedding_model:
            # Not fatal, but retrieval quality will be wrong - surface loudly.
            logger.warning(
                "Embedding model mismatch: index built with '%s' but config "
                "uses '%s'. Set EMBEDDING_MODEL to match, or rebuild the index.",
                recorded_model, self._settings.embedding_model,
            )

        self._index = index
        self._meta = meta
        self._info = info
        logger.info(
            "Vector store loaded: %d vectors, dim=%d, %.2fs",
            index.ntotal, index.d, time.time() - t0,
        )

        # Build BM25 keyword index for hybrid retrieval (optional, ~20s).
        if self._settings.hybrid_retrieval:
            try:
                from rank_bm25 import BM25Okapi
                tb = time.time()
                self._bm25 = BM25Okapi([_tokenize(m.get("text", "")) for m in meta])
                logger.info("BM25 index built for hybrid retrieval in %.1fs", time.time() - tb)
            except Exception as exc:  # noqa: BLE001 - hybrid is optional
                logger.warning("BM25 build failed (%s); falling back to dense-only.", exc)
                self._bm25 = None

    # -- properties --------------------------------------------------------
    @property
    def ready(self) -> bool:
        return self._index is not None

    @property
    def load_error(self) -> str | None:
        return self._load_error

    @property
    def size(self) -> int:
        return self._index.ntotal if self._index is not None else 0

    @property
    def info(self) -> dict[str, Any]:
        """Build-time metadata (model, dim, n_vectors, built_at)."""
        return dict(self._info)

    def _chunk_row_by_id(self) -> dict[str, int]:
        """Lazily built chunk_id -> row-index map, for O(1) neighbor lookup."""
        idx = getattr(self, "_chunk_row_idx", None)
        if idx is None:
            idx = {
                row["chunk_id"]: i
                for i, row in enumerate(self._meta)
                if row.get("chunk_id")
            }
            self._chunk_row_idx = idx
        return idx

    def doc_source(self, doc_id: str) -> str | None:
        """Original source path for a document id (used to serve the PDF).

        Built lazily and cached from the loaded chunk metadata. Returns None if
        the document is unknown or has no source path.
        """
        cache = getattr(self, "_doc_sources", None)
        if cache is None:
            cache = {}
            for row in self._meta:
                did = row.get("doc_id")
                src = row.get("source")
                if did and src and did not in cache:
                    cache[str(did)] = str(src)
            self._doc_sources = cache
        return cache.get(str(doc_id))

    def resolve_source(self, doc_id: str) -> str | None:
        """Return an EXISTING file path for a document id, or None.

        Chunk metadata stores absolute source paths recorded at ingestion time.
        Some files have since moved within the dataset tree, so the stored path
        no longer resolves. When that happens we fall back to a lazily-built
        index of the actual files under the dataset root, matched by filename.
        This recovers documents that were merely relocated (not deleted).

        Web-scraped chunks store a `.md` source under a `text/` subfolder
        (e.g. `.../UPI Cibiru/text/page.md`); the scraper also saved the
        rendered page as a sibling PDF one level up (`.../UPI Cibiru/page.pdf`).
        We prefer that PDF twin when it exists, so these sources can be opened
        the same way as native PDF documents.
        """
        src = self.doc_source(doc_id)
        if not src:
            return None
        path = Path(src)
        if path.suffix.lower() == ".md" and path.parent.name.lower() == "text":
            pdf_twin = path.parent.parent / f"{path.stem}.pdf"
            if pdf_twin.is_file():
                return str(pdf_twin)
        if path.is_file():
            return src
        return self._basename_index().get(path.name.lower())

    def _basename_index(self) -> dict[str, str]:
        """Lazily map lowercased filename -> existing path, scanned once."""
        idx = getattr(self, "_basename_idx", None)
        if idx is not None:
            return idx
        idx = {}
        root = self._dataset_root()
        if root is not None and root.is_dir():
            for p in root.rglob("*"):
                if p.is_file():
                    idx.setdefault(p.name.lower(), str(p))
        self._basename_idx = idx
        return idx

    def _dataset_root(self) -> Path | None:
        """Derive the dataset root (the 'Dataset' dir) from a stored source path."""
        for row in self._meta:
            src = row.get("source")
            if not src:
                continue
            parts = Path(src).parts
            for i, part in enumerate(parts):
                if part.lower() == "dataset":
                    return Path(*parts[: i + 1])
            return Path(src).parent.parent
        return None

    # -- retrieval ---------------------------------------------------------
    def search(
        self,
        query: str,
        top_k: int,
        score_threshold: float = 0.0,
    ) -> tuple[list[dict[str, Any]], dict[str, float]]:
        """Retrieve top-k chunks for a query.

        Returns (results, timings). Each result is the stored chunk metadata
        with an added float `score`. `timings` has embedding/search/total in ms.

        Raises VectorStoreError if the store is not ready.
        """
        if self._index is None:
            raise VectorStoreError(
                self._load_error or "Vector store is not loaded."
            )
        if not query.strip():
            return [], {"embedding_ms": 0.0, "search_ms": 0.0, "total_ms": 0.0}

        k = max(1, min(top_k, self._index.ntotal))
        # Dense candidate pool: enough rows for fusion (and for the caller's
        # oversample-then-dedupe), but at least the requested k.
        pool = max(k, self._settings.hybrid_candidates) if self._bm25 is not None else k

        t0 = time.time()
        qvec = self._embedder.encode([query], kind="query")
        t1 = time.time()
        d_scores, d_idxs = self._index.search(qvec, min(pool, self._index.ntotal))
        dense_rows = [int(i) for i in d_idxs[0] if i >= 0]
        dense_score = {int(i): float(s) for s, i in zip(d_scores[0], d_idxs[0]) if i >= 0}
        t2 = time.time()

        if self._bm25 is not None:
            # Hybrid: fuse dense + BM25 keyword ranking via RRF.
            import numpy as np
            bm = self._bm25.get_scores(_tokenize(query))
            bm25_rows = [int(i) for i in np.argsort(bm)[::-1][:pool]]
            ordered = _rrf_fuse([dense_rows, bm25_rows])[:k]
        else:
            ordered = dense_rows[:k]
        t3 = time.time()

        results: list[dict[str, Any]] = []
        for rank, row in enumerate(ordered, start=1):
            # Score shown = dense cosine when available (for the UI's % bar).
            # A row absent from dense_score matched ONLY via BM25 keyword
            # overlap with zero semantic similarity to the query - RRF's rank
            # fusion can still rank these highly on lucky keyword coincidence
            # (e.g. an unrelated article sharing a common word), and because
            # they carry no dense score they were previously immune to
            # score_threshold entirely. Drop them outright: BM25 should only
            # re-rank candidates dense search already considered plausible,
            # not inject content dense retrieval never found relevant.
            if row not in dense_score:
                continue
            score = dense_score[row]
            if score < score_threshold:
                continue
            chunk = dict(self._meta[row])
            chunk["score"] = score
            chunk["rank"] = rank
            results.append(chunk)

        timings = {
            "embedding_ms": round((t1 - t0) * 1000, 2),
            "search_ms": round((t3 - t1) * 1000, 2),
            "total_ms": round((t3 - t0) * 1000, 2),
        }
        return results, timings

    def expand_with_next_neighbor(
        self, results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Append each hit's immediate next chunk from the same document.

        Long enumerated lists (e.g. "these are UPI's 8 faculties: ...") often
        span a chunk boundary: the chunk with the framing sentence scores
        well against a query like "what faculties does UPI have", but its
        continuation (items 3 onward) reads as a bare list with no framing
        and scores too low to be retrieved on its own - so the model only
        ever sees a truncated list and truthfully reports an incomplete
        answer. Pulling in chunk_index+1 from the same doc_id (when it
        exists) gives the model that continuation without needing a bigger
        top_k or re-chunking the source document.
        """
        row_by_id = self._chunk_row_by_id()
        seen = {c["chunk_id"] for c in results if c.get("chunk_id")}
        expanded = list(results)
        for chunk in results:
            doc_id = chunk.get("doc_id")
            idx = chunk.get("chunk_index")
            if doc_id is None or idx is None:
                continue
            next_id = f"{doc_id}::{idx + 1}"
            if next_id in seen:
                continue
            row = row_by_id.get(next_id)
            if row is None:
                continue
            neighbor = dict(self._meta[row])
            neighbor["score"] = chunk.get("score", 0.0)
            neighbor["rank"] = chunk.get("rank")
            neighbor["neighbor_of"] = chunk["chunk_id"]
            expanded.append(neighbor)
            seen.add(next_id)
        return expanded
