"""RAG orchestration service.

Ties together the embedder, FAISS vector store, prompt builder and LLM service.
The API layer talks only to this service, never to the RAG components directly,
so the endpoints stay thin and the orchestration logic is unit-testable.
"""
from __future__ import annotations

import re
import time
from typing import Any

from app.core.config import Settings
from app.core.logging import get_logger
from app.rag.embedder import Embedder
from app.rag.llm import LLMService
from app.rag.prompt import build_prompt, detect_language
from app.rag.vectorstore import FaissVectorStore
from app.services import logging_service

logger = get_logger(__name__)

# --- Small-talk / greeting detection ---------------------------------------
# Greetings and chit-chat should NOT go through retrieval: they retrieve random
# documents and trigger a confusing "info tidak tersedia" refusal. Instead we
# answer with a short, friendly capability intro.
_GREETING_WORDS = {
    "halo", "hai", "hi", "hello", "hey", "hei", "pagi", "siang", "sore", "malam",
    "assalamualaikum", "assalamualaykum", "salam", "test", "tes", "ping", "p",
}
_SMALLTALK_PHRASES = {
    "halo", "hai", "hi", "hello", "hey", "apa kabar", "apakabar",
    "selamat pagi", "selamat siang", "selamat sore", "selamat malam",
    "assalamualaikum", "assalamualaikum wr wb", "terima kasih", "terimakasih",
    "makasih", "thanks", "thank you", "ok", "oke", "okay", "siapa kamu",
    "kamu siapa", "kamu bisa apa", "bisa apa", "kenalkan diri", "tes", "test",
}


def _is_smalltalk(message: str) -> bool:
    norm = re.sub(r"[^\w\s]", "", message.lower()).strip()
    if not norm:
        return True
    if norm in _SMALLTALK_PHRASES:
        return True
    tokens = norm.split()
    # very short and starts with a greeting word (e.g. "halo", "pagi kak")
    if len(tokens) <= 2 and tokens[0] in _GREETING_WORDS:
        return True
    return False


def _smalltalk_reply(language: str) -> str:
    if language == "en":
        return (
            "Hi! 👋 I'm the UPI Information Assistant. I can answer questions about "
            "Universitas Pendidikan Indonesia — for example new-student admission "
            "(PMB), tuition fees (UKT), scholarships, study programs, public "
            "information (PPID), and academic matters. What would you like to know?"
        )
    return (
        "Halo! 👋 Saya Asisten Informasi UPI. Saya dapat membantu menjawab "
        "pertanyaan seputar Universitas Pendidikan Indonesia — misalnya "
        "penerimaan mahasiswa baru (PMB), biaya kuliah (UKT), beasiswa, program "
        "studi, layanan informasi publik (PPID), dan hal akademik lainnya. "
        "Silakan ketik pertanyaan Anda."
    )


# Meta / identity questions about the chatbot ITSELF (5W1H). Patterns are
# bot-directed (require words like kamu/anda/chatbot/you) so real UPI questions
# such as "apa fungsi UKT?" or "siapa rektor UPI?" are NOT caught.
_IDENTITY_RE = re.compile(
    "|".join(
        [
            r"siapa(kah)?\s+(kamu|anda|kau)\b",
            r"\b(kamu|anda|kau)\s+siapa\b",
            r"\bkamu\s+(chatbot|bot|asisten|ai)\s+apa\b",
            r"\bapa\s+(itu\s+)?(chatbot|bot|asisten)\s+ini\b",
            r"\b(chatbot|bot|asisten|aplikasi|sistem)\s+ini\s+apa\b",
            r"\bini\s+(chatbot|bot|aplikasi)\s+apa\b",
            r"\b(untuk|buat)\s+apa\s+(kamu|anda|chatbot|bot)\b",
            r"\b(kamu|anda|chatbot)\s+(untuk|buat)\s+apa\b",
            r"\bapa\s+(tujuan|fungsi|kegunaan|kemampuan)\s*(mu\b|kamu\b|anda\b)",
            r"\b(tujuan|fungsi|kegunaan|kemampuan)\s*(mu\b|kamu\b|anda\b)",
            r"\b(kamu|anda|chatbot)\s+(bisa|dapat)\s+(apa|ngapain)\b",
            r"\bapa\s+(saja\s+)?(yang\s+)?(bisa|dapat)\s+(kamu|anda|chatbot)\s+(lakukan|jawab|bantu)\b",
            r"\bcara\s+kerja\s*(mu|kamu|anda)\b",
            r"\bbagaimana\s+(kamu|anda|chatbot)\b.*\b(kerja|bekerja|menjawab|jalan)\b",
            r"\bsiapa\s+(yang\s+)?(membuat|buat|bikin|menciptakan|mengembangkan|membangun)(mu\b|\s+(kamu|anda|chatbot|mu)\b)",
            r"\b(kamu|anda|chatbot)\s+(dibuat|diciptakan|dikembangkan|dibangun|buatan)\s+(oleh\s+)?siapa\b",
            r"\b(pembuat|pencipta|pengembang)\s*(mu|kamu|chatbot)\b",
            r"\b(kenalkan|perkenalkan|ceritakan)\s+(diri|tentang)\s*(mu|kamu|dirimu)?\b",
            # English
            r"\bwho\s+are\s+you\b",
            r"\bwhat\s+are\s+you\b",
            r"\bwhat\s+is\s+this(\s+(chat\s*bot|bot|assistant|app))?\b",
            r"\bwhat\s+(can|do)\s+you\s+do\b",
            r"\bhow\s+do\s+you\s+work\b",
            r"\bhow\s+(do|can)\s+you\s+(answer|help)\b",
            r"\bwho\s+(made|created|built|developed)\s+you\b",
            r"\b(what\s+is\s+your\s+purpose|why\s+do\s+you\s+exist|what\s+are\s+you\s+for)\b",
            r"\bintroduce\s+yourself\b",
        ]
    ),
    re.IGNORECASE,
)


def _is_identity_question(message: str) -> bool:
    return bool(_IDENTITY_RE.search(message.lower()))


def _identity_reply(language: str) -> str:
    if language == "en":
        return (
            "I am the **UPI Information Assistant**, a chatbot based on "
            "Retrieval-Augmented Generation (RAG).\n\n"
            "- **What I am**: a chatbot that answers questions about "
            "Universitas Pendidikan Indonesia (UPI).\n"
            "- **Why / what I'm for**: to help students and prospective "
            "applicants find official UPI information quickly, without browsing "
            "many documents.\n"
            "- **How I work**: when you ask something, I search the most "
            "relevant pieces of official documents in my knowledge base, then a "
            "language model composes an answer based only on those documents, "
            "complete with source citations.\n"
            "- **My data**: official documents from PPID, PMB, LPPM, the "
            "Directorate of Education, and the regional UPI campus websites "
            "(Cibiru, Sumedang, Tasikmalaya, Purwakarta, Serang).\n"
            "- **Who made me**: I was developed as a prototype for an "
            "undergraduate (skripsi) research project in Computer Engineering "
            "at UPI.\n"
            "- **What I can help with**: new-student admission (PMB), tuition "
            "(UKT), scholarships, study programs, public information (PPID), and "
            "other academic topics.\n\n"
            "Feel free to ask your question. 🙂"
        )
    return (
        "Saya adalah **Asisten Informasi UPI**, sebuah chatbot berbasis "
        "Retrieval-Augmented Generation (RAG).\n\n"
        "- **Apa saya**: chatbot yang menjawab pertanyaan seputar Universitas "
        "Pendidikan Indonesia (UPI).\n"
        "- **Untuk apa / mengapa**: membantu sivitas dan calon mahasiswa "
        "menemukan informasi resmi UPI dengan cepat tanpa perlu menelusuri "
        "banyak dokumen.\n"
        "- **Bagaimana cara kerja**: ketika Anda bertanya, saya mencari "
        "potongan dokumen resmi yang paling relevan dari basis pengetahuan, "
        "lalu sebuah model bahasa menyusun jawaban hanya berdasarkan dokumen "
        "tersebut, lengkap dengan rujukan sumbernya.\n"
        "- **Sumber data**: dokumen resmi dari PPID, PMB, LPPM, Direktorat "
        "Pendidikan, serta laman kampus daerah UPI (Cibiru, Sumedang, "
        "Tasikmalaya, Purwakarta, Serang).\n"
        "- **Siapa pembuat**: saya dikembangkan sebagai purwarupa dalam "
        "penelitian skripsi mahasiswa Teknik Komputer UPI.\n"
        "- **Yang bisa saya bantu**: penerimaan mahasiswa baru (PMB), biaya "
        "kuliah (UKT), beasiswa, program studi, layanan informasi publik "
        "(PPID), dan informasi akademik lainnya.\n\n"
        "Silakan ajukan pertanyaan Anda. 🙂"
    )


class RagService:
    """High-level retrieve + generate operations."""

    def __init__(
        self,
        settings: Settings,
        embedder: Embedder,
        store: FaissVectorStore,
        llm: LLMService,
        example_store=None,
    ) -> None:
        self._settings = settings
        self._embedder = embedder
        self._store = store
        self._llm = llm
        self._examples = example_store

    # -- readiness ---------------------------------------------------------
    @property
    def ready(self) -> bool:
        return self._embedder.ready and self._store.ready

    def readiness_detail(self) -> dict[str, Any]:
        return {
            "embedder_ready": self._embedder.ready,
            "embedder_error": self._embedder.load_error,
            "store_ready": self._store.ready,
            "store_error": self._store.load_error,
            "index_size": self._store.size,
        }

    # -- retrieval ---------------------------------------------------------
    @staticmethod
    def _dedupe_near_duplicates(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Drop chunks whose text is essentially identical to one already kept.

        Many UPI PDFs (Surat Rekomendasi PMBP, Pengumuman Hasil Seleksi, etc.)
        share boilerplate pages verbatim - the same 'Persyaratan Akademik'
        paragraph appears in 50+ doc variants. Without this filter, top-5
        retrieval returns five identical paragraphs and the LLM has no new
        information past rank 1.

        Fingerprint: first 200 chars of normalised text. Two chunks with the
        same fingerprint are treated as duplicates; the higher-scoring one wins.
        """
        seen: set[str] = set()
        kept: list[dict[str, Any]] = []
        for c in chunks:
            text = (c.get("text") or "").strip().lower()
            # Collapse whitespace so minor formatting differences don't matter.
            fingerprint = " ".join(text.split())[:200]
            if not fingerprint or fingerprint in seen:
                continue
            seen.add(fingerprint)
            kept.append(c)
        return kept

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        score_threshold: float | None = None,
    ) -> dict[str, Any]:
        """Run retrieval and return a structured result + timings.

        We oversample by 3x then dedupe by content fingerprint, then trim to
        the requested top_k. Net effect: the user sees k DIFFERENT chunks
        instead of k copies of the same boilerplate.
        """
        k = top_k or self._settings.default_top_k
        threshold = (
            self._settings.retrieval_score_threshold
            if score_threshold is None
            else score_threshold
        )
        # Oversample to give the deduper headroom; cap at max_top_k * 3.
        oversample = min(k * 3, max(self._settings.max_top_k * 3, 30))
        results, timings = self._store.search(query, oversample, threshold)

        # Drop near-duplicate paragraphs (same boilerplate across many docs).
        deduped = self._dedupe_near_duplicates(results)[:k]

        # Pull in each hit's immediate next chunk from the same document, if
        # any. Must happen AFTER the [:k] cut, not before: a chunk's neighbor
        # is appended past the end of the oversampled pool, so expanding
        # earlier just gets it discarded by this same truncation instead of
        # ever reaching the model. See FaissVectorStore.expand_with_next_neighbor.
        deduped = self._store.expand_with_next_neighbor(deduped)

        # Normalise each chunk into the SourceChunk shape the API promises.
        normalised = [self._to_source(c) for c in deduped]
        top_score = normalised[0]["score"] if normalised else None
        logging_service.log_retrieval(
            query=query,
            top_k=k,
            n_results=len(normalised),
            latency_ms=timings["total_ms"],
            top_score=top_score,
        )
        return {
            "query": query,
            "top_k": k,
            "score_threshold": threshold,
            "embedding_model": self._embedder.model_name,
            "timings": timings,
            "index_size": self._store.size,
            "results": normalised,
        }

    # -- chat --------------------------------------------------------------
    @staticmethod
    def _resolve_language(query: str, language: str | None) -> str:
        """Resolve the answer language: explicit value wins, else auto-detect from query."""
        if language and language not in ("auto", ""):
            return language
        return detect_language(query)

    def chat(
        self,
        message: str,
        top_k: int | None = None,
        temperature: float | None = None,
        language: str = "id",
        model: str | None = None,
    ) -> dict[str, Any]:
        """Full RAG turn: retrieve -> build grounded prompt -> generate answer."""
        t0 = time.time()

        # Short-circuit greetings / chit-chat: no retrieval, friendly intro.
        if _is_smalltalk(message):
            answer = _smalltalk_reply(self._resolve_language(message, language))
            total_ms = round((time.time() - t0) * 1000, 2)
            logging_service.log_chat(
                query=message, backend="smalltalk", grounded=False, n_sources=0,
                retrieval_ms=0.0, generation_ms=0.0, total_ms=total_ms,
            )
            return {
                "answer": answer, "backend": "smalltalk", "grounded": False,
                "sources": [], "retrieval_latency_ms": 0.0,
                "generation_latency_ms": 0.0, "total_latency_ms": total_ms,
            }

        # Short-circuit 5W1H questions ABOUT the chatbot itself: answer instantly
        # from a fixed self-description, with no retrieval and no LLM call.
        if _is_identity_question(message):
            answer = _identity_reply(self._resolve_language(message, language))
            total_ms = round((time.time() - t0) * 1000, 2)
            logging_service.log_chat(
                query=message, backend="identity", grounded=False, n_sources=0,
                retrieval_ms=0.0, generation_ms=0.0, total_ms=total_ms,
            )
            return {
                "answer": answer, "backend": "identity", "grounded": False,
                "sources": [], "retrieval_latency_ms": 0.0,
                "generation_latency_ms": 0.0, "total_latency_ms": total_ms,
            }

        retrieval = self.retrieve(message, top_k=top_k)
        chunks = retrieval["results"]
        retrieval_ms = retrieval["timings"]["total_ms"]

        # Style few-shot exemplars from the knowledge layer (facts still from SOURCES).
        examples = None
        if (self._examples is not None and self._settings.examples_enabled
                and self._examples.ready):
            examples = self._examples.top(message)

        t1 = time.time()
        answer, backend_used = self._llm.generate(
            query=message,
            chunks=chunks,
            language=self._resolve_language(message, language),
            temperature=temperature,
            model=model,
            examples=examples,
            reasoning=self._settings.reasoning_enabled,
        )
        generation_ms = round((time.time() - t1) * 1000, 2)
        total_ms = round((time.time() - t0) * 1000, 2)

        logging_service.log_chat(
            query=message,
            backend=backend_used,
            grounded=bool(chunks),
            n_sources=len(chunks),
            retrieval_ms=retrieval_ms,
            generation_ms=generation_ms,
            total_ms=total_ms,
        )
        return {
            "answer": answer,
            "backend": backend_used,
            "grounded": bool(chunks),
            "sources": chunks,
            "retrieval_latency_ms": retrieval_ms,
            "generation_latency_ms": generation_ms,
            "total_latency_ms": total_ms,
        }

    # -- debug -------------------------------------------------------------
    def retrieve_debug(
        self,
        query: str,
        top_k: int | None = None,
        score_threshold: float | None = None,
        language: str = "id",
    ) -> dict[str, Any]:
        """Verbose retrieval output including the exact prompt /chat would send."""
        retrieval = self.retrieve(query, top_k=top_k, score_threshold=score_threshold)
        prompt_preview = build_prompt(
            query, retrieval["results"], self._resolve_language(query, language)
        )
        return {**retrieval, "prompt_preview": prompt_preview}

    # -- helpers -----------------------------------------------------------
    @staticmethod
    def _to_source(chunk: dict[str, Any]) -> dict[str, Any]:
        """Project a raw stored chunk onto the SourceChunk schema fields.

        Tolerant of metadata variation across notebook versions: missing keys
        become None rather than raising.
        """
        return {
            "rank": chunk.get("rank", 0),
            "score": float(chunk.get("score", 0.0)),
            "chunk_id": str(chunk.get("chunk_id", chunk.get("chunk_index", ""))),
            "doc_id": str(chunk.get("doc_id", "")),
            "title": chunk.get("title", "Dokumen tanpa judul"),
            "category": chunk.get("category"),
            "source_type": chunk.get("source_type"),
            "source": chunk.get("source"),
            "url": chunk.get("url"),
            "page": chunk.get("page"),
            "section": chunk.get("section"),
            "text": chunk.get("text", ""),
        }
