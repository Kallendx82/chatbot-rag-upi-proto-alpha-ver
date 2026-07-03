"""Q&A example store for STYLE few-shot prompting.

Loads curated question/answer exemplars from the knowledge layer, embeds the
questions once at startup, and returns the most similar examples for a query.

These are used ONLY as a guide to answer STYLE/FORMAT (structure, citations,
how to refuse) — the actual FACTS in an answer must still come from the
retrieved SOURCES. This keeps grounding intact and avoids the hallucination
risk of treating example answers as fact sources.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import numpy as np

from app.core.config import Settings
from app.core.logging import get_logger
from app.rag.embedder import Embedder

logger = get_logger(__name__)


class ExampleStore:
    """Embeds Q&A exemplars and serves nearest-neighbour style examples."""

    def __init__(self, settings: Settings, embedder: Embedder) -> None:
        self._settings = settings
        self._embedder = embedder
        self._examples: list[dict] = []
        self._vecs: np.ndarray | None = None
        self._lock = threading.Lock()
        self._error: str | None = None

    @property
    def ready(self) -> bool:
        return self._vecs is not None and len(self._examples) > 0

    @property
    def size(self) -> int:
        return len(self._examples)

    def load(self) -> None:
        """Idempotent. Records failure instead of raising — few-shot is optional."""
        if not self._settings.examples_enabled:
            logger.info("Example store disabled (examples_enabled=false).")
            return
        if self._vecs is not None or self._error is not None:
            return
        with self._lock:
            if self._vecs is not None or self._error is not None:
                return
            try:
                self._do_load()
            except Exception as exc:  # noqa: BLE001 - optional feature
                self._error = str(exc)
                logger.warning("Example store load failed (%s); few-shot disabled.", exc)

    def _do_load(self) -> None:
        path = Path(self._settings.examples_path).expanduser()
        if not path.exists():
            logger.warning("Examples file not found: %s; few-shot disabled.", path)
            return
        if not self._embedder.ready:
            logger.warning("Embedder not ready; example store skipped.")
            return

        t0 = time.time()
        examples: list[dict] = []
        for line in path.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            q = (d.get("question") or "").strip()
            a = (d.get("expected_answer_short") or "").strip()
            # Only grounded, answerable exemplars make good style demos.
            if d.get("coverage") == "not_in_corpus" or not q or not a:
                continue
            examples.append({"question": q, "answer": a})

        if not examples:
            logger.warning("No usable examples in %s; few-shot disabled.", path)
            return

        vecs = self._embedder.encode([e["question"] for e in examples], kind="query")
        self._examples = examples
        self._vecs = np.asarray(vecs, dtype="float32")
        logger.info("Example store loaded: %d Q&A exemplars in %.1fs (from %s)",
                    len(examples), time.time() - t0, path.name)

    def top(self, query: str, k: int | None = None) -> list[dict]:
        """Return the k most similar exemplars to `query` (cosine similarity)."""
        if not self.ready or not query.strip():
            return []
        k = k or self._settings.examples_top_k
        qv = self._embedder.encode([query], kind="query")[0].astype("float32")
        sims = self._vecs @ qv  # vectors are L2-normalised -> dot == cosine
        order = np.argsort(sims)[::-1][:k]
        return [self._examples[int(i)] for i in order]
