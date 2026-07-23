"""Application configuration.

All settings are environment-driven (12-factor style). Defaults are chosen so
the backend boots even before the .env file is filled in, but RAG endpoints
will report "not ready" until a real FAISS index path is provided.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "UPI RAG Chatbot API"
    app_env: Literal["development", "production"] = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api"

    # --- CORS (comma-separated origins) ---
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # --- RAG: vector store + metadata ---
    # These point at artefacts produced by 03_vectorstore_rag_evaluation.ipynb.
    # Defaults match that notebook's layout:
    #   _pipeline/index/faiss.index
    #   _pipeline/index/chunks_meta.json
    #   _pipeline/index/index_info.json
    faiss_index_path: str = "./app/data/faiss.index"
    chunks_meta_path: str = "./app/data/chunks_meta.json"
    index_info_path: str = "./app/data/index_info.json"

    # --- Embeddings ---
    # Should match the model recorded in index_info.json. A mismatch is detected
    # at startup and surfaced via /health rather than silently degrading.
    embedding_model: str = "intfloat/multilingual-e5-base"
    use_e5_prefixes: bool = True
    embedding_batch_size: int = 32

    # --- Retrieval ---
    default_top_k: int = 8
    max_top_k: int = 20
    retrieval_score_threshold: float = 0.0  # 0 = keep all hits

    # --- Hybrid retrieval (BM25 + dense, fused with Reciprocal Rank Fusion) ---
    # Improves keyword-heavy queries (program names, fees) that pure dense
    # retrieval misses. Builds a BM25 index over chunk text at startup (~20s).
    hybrid_retrieval: bool = True
    hybrid_candidates: int = 50  # candidate pool per retriever before fusion

    # --- Example-augmented prompting (style few-shot from the knowledge layer) ---
    # Inject the most similar Q&A examples as STYLE/FORMAT exemplars only; the
    # FACTS still come solely from retrieved SOURCES (avoids hallucination).
    examples_enabled: bool = True
    examples_path: str = "D:/Project/RAG_UPI/knowledge_layer/expected_answers.jsonl"
    examples_top_k: int = 2
    # Light reasoning directive in the prompt (analyse sources before answering).
    reasoning_enabled: bool = True

    # --- LLM backend ---
    # "extractive" needs no LLM and always works (good for first-run / CI).
    # "ollama" talks to a local Ollama server. "openai" uses an OpenAI-compatible API.
    llm_backend: Literal["extractive", "ollama", "openai"] = "extractive"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024
    llm_request_timeout: float = 90.0

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    # Context window passed to Ollama. 2048 is too small (truncates chunks), but
    # 8192 makes a 7B model spill out of a 6 GB GPU onto the CPU (very slow ->
    # request timeouts -> HTTP 500). 4096 fits a 7B on 6 GB VRAM AND holds the
    # system prompt + ~5 chunks (top_k=5) + question comfortably. Raise only if
    # you have more VRAM or use large top_k.
    ollama_num_ctx: int = 4096

    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # --- Request limits ---
    max_query_chars: int = 2000

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def faiss_index_file(self) -> Path:
        return Path(self.faiss_index_path).expanduser()

    @property
    def chunks_meta_file(self) -> Path:
        return Path(self.chunks_meta_path).expanduser()

    @property
    def index_info_file(self) -> Path:
        return Path(self.index_info_path).expanduser()


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor. Used as a FastAPI dependency."""
    return Settings()
