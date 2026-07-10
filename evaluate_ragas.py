"""evaluate_ragas.py
=============================================================================
RAGAS evaluation of the UPI RAG pipeline, fully local (no API keys).

Pipeline per question (sampled from the clean 1018 knowledge layer):
  1. retrieve top-k chunks from the SAME FAISS index the chatbot uses
     (intfloat/multilingual-e5-base, "query: " prefix, cosine)
  2. generate a grounded answer via Ollama (default judge+gen model qwen2.5:7b-instruct)
  3. score with RAGAS using a local Ollama judge + local embeddings

Metrics (all 0-1, higher = better):
  - faithfulness       : answer is supported by the retrieved context (anti-hallucination)
  - answer_relevancy   : answer actually addresses the question
  - context_precision  : retrieved chunks are relevant (low noise), needs reference
  - context_recall     : retrieved chunks cover the reference answer, needs reference

Ground truth = expected_answer_short from expected_answers.jsonl.

USAGE
    python evaluate_ragas.py                       # 50 samples, qwen2.5:7b-instruct judge, e5 emb
    python evaluate_ragas.py --limit 3             # quick smoke test
    python evaluate_ragas.py --sample 50 --judge qwen2.5:7b-instruct --embeddings e5
    python evaluate_ragas.py --embeddings nomic    # use nomic-embed-text (ollama pull first)

Requirements (already installed): ragas<0.3, langchain 0.3.x, langchain-ollama,
langchain-huggingface, datasets, faiss, sentence-transformers. Ollama running.
=============================================================================
"""
from __future__ import annotations

# --- Windows native-crash workaround -------------------------------------- #
# faiss + torch (sentence_transformers) loaded together segfault (exit code
# 0xC0000005) before main() can even log. Preloading the ragas -> torch ->
# faiss stack in this exact order at import time loads cleanly (the order that
# was verified to work). The KMP flag is added as belt-and-suspenders.
import os as _os
_os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
import ragas  # noqa: F401,E402
import langchain_ollama  # noqa: F401,E402
import sentence_transformers  # noqa: F401,E402
import faiss  # noqa: F401,E402
# -------------------------------------------------------------------------- #

import argparse
import json
import random
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

# Windows consoles default to cp1252, which cannot encode the emoji/box-drawing
# characters used in the per-category console report -> a UnicodeEncodeError would
# crash the run AFTER all result files are already written. Force UTF-8 stdout.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001 - older/edge streams without reconfigure
        pass

RAG_ROOT = Path(r"D:\Project\RAG_UPI")
DEFAULT_KL = RAG_ROOT / "knowledge_layer"
DEFAULT_INDEX_DIR = RAG_ROOT / "Dataset" / "_pipeline" / "index"
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
OLLAMA_BASE_URL = "http://localhost:11434"


def log(m: str) -> None:
    print(f"[ragas] {m}", flush=True)


import re as _re
from collections import defaultdict as _defaultdict
_TOKEN_RE = _re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


def _rrf_fuse(rankings: list[list[int]], k0: int = 60) -> list[int]:
    score: dict[int, float] = _defaultdict(float)
    for ranking in rankings:
        for rank, row in enumerate(ranking, start=1):
            score[row] += 1.0 / (k0 + rank)
    return [row for row, _ in sorted(score.items(), key=lambda x: x[1], reverse=True)]


def _make_reuse_embeddings_cls():
    """Build the reuse-embeddings class lazily (needs langchain_core at runtime)."""
    from langchain_core.embeddings import Embeddings

    class _ReuseE5(Embeddings):
        """RAGAS embeddings that reuse an already-loaded SentenceTransformer e5,
        so no second copy of the model is loaded into RAM."""
        def __init__(self, st_model, use_prefix: bool):
            self._m = st_model
            self._p = use_prefix

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            t = [("passage: " + x) if self._p else x for x in texts]
            return self._m.encode(t, normalize_embeddings=True,
                                  convert_to_numpy=True).tolist()

        def embed_query(self, text: str) -> list[float]:
            t = ("query: " + text) if self._p else text
            return self._m.encode([t], normalize_embeddings=True,
                                  convert_to_numpy=True)[0].tolist()

    return _ReuseE5


def _ReuseE5Embeddings(st_model, use_prefix: bool):
    return _make_reuse_embeddings_cls()(st_model, use_prefix)


# --------------------------------------------------------------------------- #
# Retriever (same config as the deployed chatbot / evaluate_rag.py)
# --------------------------------------------------------------------------- #
class Retriever:
    def __init__(self, index_dir: Path, need_bm25: bool = False):
        import faiss
        from sentence_transformers import SentenceTransformer

        info = index_dir / "index_info.json"
        self.info = json.loads(info.read_text(encoding="utf-8")) if info.exists() else {}
        self.model_name = self.info.get("embedding_model", EMBEDDING_MODEL)
        self.use_prefix = bool(self.info.get("use_e5_prefixes", True))
        log(f"loading FAISS index + meta ...")
        self.index = faiss.read_index(str(index_dir / "faiss.index"))
        self.meta = json.loads((index_dir / "chunks_meta.json").read_text(encoding="utf-8"))
        # Keep the embedder on CPU so it does NOT compete with Ollama for the
        # 6 GB VRAM (e5-base on CPU is plenty fast for a few-dozen queries).
        log(f"loading embedder {self.model_name} (CPU) ...")
        self.embedder = SentenceTransformer(self.model_name, device="cpu")
        self.bm25 = None
        if need_bm25:
            from rank_bm25 import BM25Okapi
            log(f"building BM25 over {len(self.meta):,} chunks ...")
            self.bm25 = BM25Okapi([_tokenize(m.get("text", "")) for m in self.meta])
        log(f"retriever ready: {self.index.ntotal:,} vectors")

    def search(self, query: str, k: int, mode: str = "dense", candidates: int = 50) -> list[dict]:
        q = ("query: " + query) if self.use_prefix else query
        vec = self.embedder.encode([q], convert_to_numpy=True,
                                   normalize_embeddings=True).astype("float32")
        pool = max(k, candidates) if (mode == "hybrid" and self.bm25 is not None) else k
        scores, idxs = self.index.search(vec, pool)
        dense_rows = [int(i) for i in idxs[0] if i >= 0]
        dense_score = {int(i): float(s) for s, i in zip(scores[0], idxs[0]) if i >= 0}

        if mode == "hybrid" and self.bm25 is not None:
            import numpy as np
            bm = self.bm25.get_scores(_tokenize(query))
            bm25_rows = [int(i) for i in np.argsort(bm)[::-1][:pool]]
            ordered = _rrf_fuse([dense_rows, bm25_rows])[:k]
        else:
            ordered = dense_rows[:k]

        out = []
        for row in ordered:
            c = dict(self.meta[row])
            c["score"] = dense_score.get(row, 0.0)
            out.append(c)
        return out


# --------------------------------------------------------------------------- #
# Grounded answer generation via Ollama (mirrors the backend prompt)
# --------------------------------------------------------------------------- #
GEN_PROMPT = """Anda adalah asisten informasi resmi Universitas Pendidikan Indonesia (UPI).
Jawab HANYA berdasarkan SUMBER bernomor di bawah, dalam Bahasa Indonesia baku.
Sertakan nomor sumber [1], [2] untuk setiap fakta. Jika SUMBER tidak memuat jawaban,
katakan informasinya tidak tersedia. Jangan mengarang.

SUMBER:
{context}

PERTANYAAN: {question}

JAWABAN:"""


def ollama_generate(model: str, prompt: str, temperature: float = 0.1,
                    num_ctx: int = 4096, num_predict: int = 1024,
                    timeout: int = 240) -> str:
    payload = {
        "model": model, "prompt": prompt, "stream": False,
        "options": {"temperature": temperature, "num_predict": num_predict, "num_ctx": num_ctx},
    }
    data = json.dumps(payload).encode("utf-8")
    # Retry on transient Ollama failures (restart, cold-load, brief unavailability)
    # so a single hiccup does not kill a multi-hour run.
    last = None
    for attempt in range(5):
        try:
            req = urllib.request.Request(
                f"{OLLAMA_BASE_URL}/api/generate", data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return (json.loads(r.read().decode("utf-8")).get("response") or "").strip()
        except Exception as e:  # noqa: BLE001
            last = e
            log(f"  ! Ollama gagal (attempt {attempt+1}/5): {e} -> retry")
            time.sleep(min(30, 6 * (attempt + 1)))
    log(f"  !! Ollama gagal permanen di item ini: {last} -> jawaban kosong, lanjut")
    return ""


def build_context(chunks: list[dict]) -> tuple[str, list[str]]:
    blocks, texts = [], []
    for i, c in enumerate(chunks, 1):
        t = (c.get("text") or "").strip()
        if not t:
            continue
        title = c.get("title", "Dokumen")
        page = c.get("page")
        ref = f"{title}" + (f", hal. {page}" if page is not None else "")
        blocks.append(f"[{i}] {ref}\n{t}")
        texts.append(t)
    return "\n\n".join(blocks), texts


# --------------------------------------------------------------------------- #
# Build the evaluation samples (retrieve + generate)
# --------------------------------------------------------------------------- #
def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


# --------------------------------------------------------------------------- #
# Resumable checkpoints (survive a mid-run crash / power loss)
# --------------------------------------------------------------------------- #
def _sig(*parts) -> str:
    import hashlib
    return hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:16]


def _load_ckpt(ckpt: Path, meta: Path, sig: str) -> dict[str, dict]:
    """Return {question_id: record} from a checkpoint IFF its signature matches.
    A mismatch (different question set / model) wipes the stale checkpoint."""
    if not ckpt.exists():
        return {}
    ok = False
    if meta.exists():
        try:
            # a crash mid-write can leave meta empty/truncated -> treat as stale, not fatal
            ok = json.loads(meta.read_text(encoding="utf-8")).get("sig") == sig
        except Exception:  # noqa: BLE001
            ok = False
    if not ok:
        log(f"  checkpoint {ckpt.name} is stale/corrupt -> starting fresh")
        ckpt.unlink(missing_ok=True)
        meta.unlink(missing_ok=True)
        return {}
    done: dict[str, dict] = {}
    for line in ckpt.open(encoding="utf-8"):
        if line.strip():
            try:
                r = json.loads(line)
                done[r["question_id"]] = r
            except Exception:  # noqa: BLE001 - tolerate a torn final line from a crash
                pass
    if done:
        log(f"  resume: {ckpt.name} has {len(done)} completed items")
    return done


def _chunks(seq: list, n: int):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def pick_questions(kl: Path, sample_n: int, seed: int, limit: int | None):
    """Pick the evaluation questions ONCE (so dense/hybrid score the same set)."""
    retrieval = read_jsonl(kl / "retrieval_eval.jsonl")
    answers = {r["question_id"]: r for r in read_jsonl(kl / "expected_answers.jsonl")}
    joined = []
    for r in retrieval:
        a = answers.get(r["question_id"])
        if a and a.get("expected_answer_short"):
            joined.append({
                "question_id": r["question_id"],
                "question": r["query"],
                "reference": a["expected_answer_short"].strip(),
                "category": r.get("category", "?"),
            })
    log(f"{len(joined)} questions have a reference answer")
    rng = random.Random(seed)
    rng.shuffle(joined)
    picked = joined[: (limit or sample_n)]
    log(f"sampling {len(picked)} questions (seed={seed})")
    return picked


def build_for_mode(picked, retr: Retriever, gen_model: str, top_k: int,
                   num_ctx: int, mode: str, temperature: float,
                   num_predict: int, timeout: int,
                   ckpt_dir: Path | None = None, gensig: str = "", resume: bool = True):
    """Retrieve (in the given mode) + generate an answer for each picked question.

    Resumable: each generated answer is appended to <ckpt_dir>/gen_<mode>.jsonl as
    it completes, so a crash mid-run continues instead of regenerating from zero.
    """
    ckpt = meta = None
    done: dict[str, dict] = {}
    fout = None
    if ckpt_dir is not None and resume:
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        ckpt = ckpt_dir / f"gen_{mode}.jsonl"
        meta = ckpt_dir / f"gen_{mode}.meta.json"
        done = _load_ckpt(ckpt, meta, gensig)
        meta.write_text(json.dumps({"sig": gensig}), encoding="utf-8")
        fout = ckpt.open("a", encoding="utf-8")

    rows = []
    for n, item in enumerate(picked, 1):
        qid = item["question_id"]
        if qid in done:
            rows.append(done[qid])
            if n % 25 == 0 or n == len(picked):
                log(f"  [{mode}] [{n}/{len(picked)}] resumed from checkpoint")
            continue
        chunks = retr.search(item["question"], top_k, mode=mode)
        context, ctx_texts = build_context(chunks)
        t0 = time.time()
        answer = ollama_generate(gen_model,
                                 GEN_PROMPT.format(context=context, question=item["question"]),
                                 temperature=temperature,
                                 num_ctx=num_ctx,
                                 num_predict=num_predict,
                                 timeout=timeout)
        gen_ms = round((time.time() - t0) * 1000)
        row = {
            "question_id": qid,
            "category": item["category"],
            "user_input": item["question"],
            "retrieved_contexts": ctx_texts or ["(tidak ada konteks)"],
            "response": answer or "(kosong)",
            "reference": item["reference"],
            "gen_ms": gen_ms,
        }
        rows.append(row)
        if fout is not None:
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            fout.flush()
        log(f"  [{mode}] [{n}/{len(picked)}] gen {gen_ms} ms | {item['question'][:55]}")
    if fout is not None:
        fout.close()
    return rows


# --------------------------------------------------------------------------- #
# RAGAS scoring
# --------------------------------------------------------------------------- #
RAGAS_METRIC_COLS = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")


def build_ragas_judge_emb(judge_model: str, judge_provider: str, embeddings: str,
                          num_ctx: int = 4096, reuse_embedder=None, use_prefix: bool = True,
                          judge_num_predict: int = 512, judge_timeout: int = 300):
    """Build the judge LLM + embeddings + metrics ONCE (reused across score batches)."""
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.run_config import RunConfig

    # Initialize judge based on provider
    if judge_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        log(f"judge = {judge_model} (Anthropic API, timeout={judge_timeout}s)")
        judge = ChatAnthropic(model=judge_model, temperature=0.0,
                             timeout=judge_timeout, max_retries=3)
    elif judge_provider == "openai":
        from langchain_openai import ChatOpenAI
        log(f"judge = {judge_model} (OpenAI API, timeout={judge_timeout}s)")
        judge = ChatOpenAI(model=judge_model, temperature=0.0,
                          timeout=judge_timeout, max_retries=3)
    else:  # ollama (default/legacy)
        from langchain_ollama import ChatOllama
        log(f"judge = {judge_model} (Ollama local, num_ctx={num_ctx})")
        judge = ChatOllama(model=judge_model, base_url=OLLAMA_BASE_URL,
                          temperature=0.0, num_ctx=num_ctx, num_predict=judge_num_predict)

    ragas_llm = LangchainLLMWrapper(judge)

    if embeddings == "nomic":
        from langchain_ollama import OllamaEmbeddings
        log("embeddings = nomic-embed-text (Ollama)")
        emb = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_BASE_URL)
    elif reuse_embedder is not None:
        # Reuse the retriever's already-loaded e5 -> no second model load
        # (avoids the 'paging file too small' OOM on a memory-tight machine).
        log(f"embeddings = {EMBEDDING_MODEL} (REUSED from retriever, no 2nd load)")
        emb = _ReuseE5Embeddings(reuse_embedder, use_prefix)
    else:
        from langchain_huggingface import HuggingFaceEmbeddings
        log(f"embeddings = {EMBEDDING_MODEL} (HuggingFace, CPU)")
        emb = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL,
                                    model_kwargs={"device": "cpu"})
    ragas_emb = LangchainEmbeddingsWrapper(emb)

    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
    # Local Ollama is serial; keep concurrency low and timeouts generous so a slow
    # judge call doesn't get cancelled (which would show up as NaN).
    run_config = RunConfig(max_workers=2, timeout=judge_timeout, max_retries=3)
    return ragas_llm, ragas_emb, metrics, run_config


def score_batch(rows: list[dict], ragas_llm, ragas_emb, metrics, run_config) -> list[dict]:
    """Score one batch of rows; return per-row {metric: value|None} aligned to input order."""
    from ragas import evaluate, EvaluationDataset
    dataset = EvaluationDataset.from_list([
        {"user_input": r["user_input"], "retrieved_contexts": r["retrieved_contexts"],
         "response": r["response"], "reference": r["reference"]}
        for r in rows
    ])
    result = evaluate(dataset=dataset, metrics=metrics, llm=ragas_llm,
                      embeddings=ragas_emb, run_config=run_config)
    df = result.to_pandas()
    cols = [c for c in df.columns if c in RAGAS_METRIC_COLS]
    out = []
    for i in range(len(rows)):
        if i >= len(df):
            out.append({c: None for c in cols})
        else:
            out.append({c: (None if np_isnan(df.iloc[i][c]) else float(df.iloc[i][c]))
                        for c in cols})
    return out


# --------------------------------------------------------------------------- #
# Per-kategori console printing + recommendations
# --------------------------------------------------------------------------- #
def print_per_category_console(report: dict, mcols: list[str]) -> None:
    """Print per-kategori scores to console for quick visual assessment."""
    by_cat = report.get("by_category", {})
    if not by_cat:
        return
    print("\n" + "="*80)
    print("📊 SCORES PER KATEGORI (untuk penelitian selanjutnya)")
    print("="*80)
    # Header
    print(f"{'Kategori':<20} | " + " | ".join(f"{c.replace('_', ' '):<12}" for c in mcols))
    print("-"*80)
    # Rows
    for cat in sorted(by_cat.keys()):
        vals = by_cat[cat]
        print(f"{cat:<20} | " + " | ".join(f"{vals.get(c, float('nan')):>12.3f}" for c in mcols))
    # Overall
    means = report["metrics_mean"]
    print("-"*80)
    print(f"{'OVERALL':<20} | " + " | ".join(f"{means.get(c, float('nan')):>12.3f}" for c in mcols))
    print("="*80)

    # Recommendations
    recommendations = generate_recommendations(report)
    if recommendations:
        print("\n💡 REKOMENDASI UNTUK PENELITIAN SELANJUTNYA:")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec}")


def generate_recommendations(report: dict) -> list[str]:
    """Generate recommendations based on per-kategori performance."""
    by_cat = report.get("by_category", {})
    mcols = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    recs = []

    for cat, vals in sorted(by_cat.items()):
        faith = vals.get("faithfulness", 0)
        rel = vals.get("answer_relevancy", 0)
        prec = vals.get("context_precision", 0)
        recall = vals.get("context_recall", 0)

        if faith < 0.7:
            recs.append(f"[{cat}] Faithfulness rendah ({faith:.3f}) → Jawaban kurang grounded di konteks. "
                       "Perbaiki retrieval atau perketat prompt agar LLM tidak mengarang.")
        if rel < 0.7:
            recs.append(f"[{cat}] Answer Relevancy rendah ({rel:.3f}) → Jawaban tidak fokus menjawab soal. "
                       "Perlu synonym expansion / query understanding yang lebih baik.")
        if prec < 0.6:
            recs.append(f"[{cat}] Context Precision rendah ({prec:.3f}) → Chunk yang diambil banyak noise. "
                       "Consider: chunk size tuning, reference answer improvement, atau metadata filtering.")
        if recall < 0.6:
            recs.append(f"[{cat}] Context Recall rendah ({recall:.3f}) → Chunk yang relevan terlewat. "
                       "Coba hybrid retrieval (BM25+dense), semantic similarity tuning, atau data augmentation.")

    return recs


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description="RAGAS evaluation of the UPI RAG with per-kategori breakdown.")
    ap.add_argument("--kl", default=str(DEFAULT_KL))
    ap.add_argument("--index-dir", default=str(DEFAULT_INDEX_DIR))
    ap.add_argument("--sample", type=int, default=50, help="How many questions to evaluate.")
    ap.add_argument("--limit", type=int, default=None, help="Override sample for a quick test (e.g., --limit 10).")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--judge", default="claude-haiku-4-5-20251001", help="Judge model (default: Anthropic Haiku).")
    ap.add_argument("--judge-provider", choices=["anthropic", "openai", "ollama"], default="anthropic",
                    help="Judge API provider: anthropic (default, $$$), openai, or ollama (local, free).")
    ap.add_argument("--gen-model", default=None,
                    help="Ollama model to GENERATE answers (default = llama3.1:8b-instruct).")
    ap.add_argument("--embeddings", choices=["e5", "nomic"], default="e5")
    ap.add_argument("--retrieval", choices=["dense", "hybrid", "compare"], default="hybrid",
                    help="dense | hybrid (BM25+dense RRF) | compare (run both, before/after).")
    ap.add_argument("--num-ctx", type=int, default=4096,
                    help="Ollama context window. 4096 fits a 7B on a 6 GB GPU; "
                         "8192 may force CPU fallback (much slower).")
    ap.add_argument("--temperature", type=float, default=0.1,
                    help="Generation temperature for the answer model.")
    ap.add_argument("--num-predict", type=int, default=1024,
                    help="Maximum generated tokens for the answer model.")
    ap.add_argument("--ollama-timeout", type=int, default=240,
                    help="Timeout in seconds for each answer-generation Ollama call.")
    ap.add_argument("--judge-num-predict", type=int, default=512,
                    help="Maximum generated tokens for the RAGAS judge model.")
    ap.add_argument("--judge-timeout", type=int, default=300,
                    help="Timeout in seconds for each RAGAS judge call.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--score-batch", type=int, default=25,
                    help="Score this many samples per RAGAS batch before checkpointing.")
    ap.add_argument("--no-resume", dest="resume", action="store_false",
                    help="Ignore checkpoints and evaluate from scratch.")
    ap.add_argument("--ckpt-dir", default=None,
                    help="Where to store resumable checkpoints (default: <out_dir>/_ckpt).")
    ap.add_argument("--tag", default="",
                    help="Label for this run (e.g. 'llama', 'qwen25'). Writes results + "
                         "checkpoints to <kl>/eval/ragas/<tag>/ so multiple generators don't "
                         "overwrite each other.")
    args = ap.parse_args()

    t0 = time.time()
    kl = Path(args.kl)
    out_dir = kl / "eval" / "ragas"
    if args.tag:
        out_dir = out_dir / args.tag
    out_dir.mkdir(parents=True, exist_ok=True)
    # Generator = Ollama local, Judge = API or Ollama
    gen_model = args.gen_model or "llama3.1:8b-instruct"

    resume = args.resume
    ckpt_dir = Path(args.ckpt_dir) if args.ckpt_dir else (out_dir / "_ckpt")
    if resume:
        log(f"resumable checkpoints: {ckpt_dir} (use --no-resume to disable)")

    need_bm25 = args.retrieval in ("hybrid", "compare")
    retr = Retriever(Path(args.index_dir), need_bm25=need_bm25)
    picked = pick_questions(kl, args.sample, args.seed, args.limit)

    # signature that invalidates the generation checkpoint if the question set,
    # generator model, or retrieval settings change
    gensig = _sig(gen_model, args.sample, args.limit, args.seed, args.top_k,
                  args.temperature, args.num_predict,
                  ",".join(p["question_id"] for p in picked))

    def free_bm25():
        """Release the BM25 index (large) before the memory-heavy scoring phase."""
        if getattr(retr, "bm25", None) is not None:
            retr.bm25 = None
            import gc
            gc.collect()
            log("BM25 freed before scoring (memory)")

    def score_write(rows: list[dict], mode: str, sub: Path, tm: float) -> dict:
        sub.mkdir(parents=True, exist_ok=True)
        mcols = list(RAGAS_METRIC_COLS)

        # ---- resumable, batched RAGAS scoring -------------------------------
        # A crash during scoring must not re-spend the judge budget on samples
        # already scored, so per-row scores are checkpointed as each batch lands.
        scoresig = _sig(gen_model, args.judge, args.judge_provider, args.embeddings,
                        args.sample, args.limit, args.seed, args.top_k, mode,
                        ",".join(r["question_id"] for r in rows))
        scored: dict[str, dict] = {}
        sfout = None
        if ckpt_dir is not None and resume:
            ckpt_dir.mkdir(parents=True, exist_ok=True)
            sckpt = ckpt_dir / f"scored_{mode}.jsonl"
            smeta = ckpt_dir / f"scored_{mode}.meta.json"
            scored = _load_ckpt(sckpt, smeta, scoresig)
            smeta.write_text(json.dumps({"sig": scoresig}), encoding="utf-8")
            sfout = sckpt.open("a", encoding="utf-8")

        todo = [r for r in rows if r["question_id"] not in scored]
        if todo:
            log(f"[{mode}] scoring {len(todo)} unscored samples "
                f"({len(scored)} already done) with RAGAS...")
            judge_emb = build_ragas_judge_emb(
                args.judge, args.judge_provider, args.embeddings,
                num_ctx=args.num_ctx, reuse_embedder=retr.embedder,
                use_prefix=retr.use_prefix, judge_num_predict=args.judge_num_predict,
                judge_timeout=args.judge_timeout)
            n_done = 0
            for batch in _chunks(todo, max(1, args.score_batch)):
                vals = score_batch(batch, *judge_emb)
                for r, v in zip(batch, vals):
                    rec = {"question_id": r["question_id"], **v}
                    scored[r["question_id"]] = v
                    if sfout is not None:
                        sfout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        sfout.flush()
                n_done += len(batch)
                log(f"[{mode}] scored {n_done}/{len(todo)} (batch of {len(batch)})")
        else:
            log(f"[{mode}] all {len(rows)} samples already scored (resumed from checkpoint)")
        if sfout is not None:
            sfout.close()

        # merge checkpointed scores back onto every row
        for r in rows:
            sc = scored.get(r["question_id"], {})
            for c in mcols:
                r[c] = sc.get(c)

        means = {c: round(float(np.nanmean([r[c] for r in rows if r[c] is not None] or [np.nan])), 4)
                 for c in mcols}
        n_nan = {c: int(sum(1 for r in rows if r[c] is None)) for c in mcols}
        import csv as _csv
        cols = ["question_id", "category", "gen_ms"] + mcols + ["user_input", "reference", "response"]
        with (sub / "ragas_per_sample.csv").open("w", encoding="utf-8", newline="") as f:
            w = _csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow({**r, "user_input": r["user_input"][:200],
                            "reference": r["reference"][:200], "response": (r["response"] or "")[:300]})
        by_cat = {}
        cats: dict = {}
        for r in rows:
            cats.setdefault(r["category"], []).append(r)
        for cat, rs in cats.items():
            by_cat[cat] = {c: round(float(np.nanmean([x[c] for x in rs if x[c] is not None] or [np.nan])), 4)
                           for c in mcols}
        report = {
            "judge_model": args.judge, "judge_provider": args.judge_provider, "gen_model": gen_model,
            "embeddings": args.embeddings if args.embeddings == "nomic" else EMBEDDING_MODEL,
            "retrieval": mode, "n_samples": len(rows), "top_k": args.top_k,
            "mean_gen_ms": round(sum(r["gen_ms"] for r in rows) / max(len(rows), 1)),
            "metrics_mean": means, "metrics_nan_count": n_nan, "by_category": by_cat,
            "elapsed_s": round(time.time() - tm, 1),
        }
        (sub / "ragas_metrics.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        write_md(sub / "ragas_report.md", report, mcols)

        # Print per-kategori to console untuk quick feedback
        print_per_category_console(report, mcols)

        log(f"[{mode}] selesai {report['elapsed_s']}s: "
            + "  ".join(f"{c}={means[c]:.3f}" for c in mcols))
        return report

    if args.retrieval == "compare":
        # Generate answers for BOTH modes first (BM25 needed for hybrid), THEN
        # free BM25 and score — keeps peak memory low.
        tmd = time.time()
        rows_d = build_for_mode(picked, retr, gen_model, args.top_k, args.num_ctx, "dense",
                                args.temperature, args.num_predict, args.ollama_timeout,
                                ckpt_dir=ckpt_dir, gensig=gensig, resume=resume)
        tmh = time.time()
        rows_h = build_for_mode(picked, retr, gen_model, args.top_k, args.num_ctx, "hybrid",
                                args.temperature, args.num_predict, args.ollama_timeout,
                                ckpt_dir=ckpt_dir, gensig=gensig, resume=resume)
        free_bm25()
        rep_d = score_write(rows_d, "dense", out_dir / "dense", tmd)
        rep_h = score_write(rows_h, "hybrid", out_dir / "hybrid", tmh)
        write_compare(out_dir / "ragas_compare.md", rep_d, rep_h)
        log("=" * 60)
        log(f"COMPARE DONE in {round(time.time()-t0,1)}s -> {out_dir / 'ragas_compare.md'}")
    else:
        tm = time.time()
        rows = build_for_mode(picked, retr, gen_model, args.top_k, args.num_ctx, args.retrieval,
                              args.temperature, args.num_predict, args.ollama_timeout,
                              ckpt_dir=ckpt_dir, gensig=gensig, resume=resume)
        free_bm25()
        score_write(rows, args.retrieval, out_dir, tm)
        log("=" * 60)
        log(f"RAGAS DONE in {round(time.time()-t0,1)}s -> {out_dir}")


def np_isnan(v) -> bool:
    try:
        return bool(np.isnan(v))
    except Exception:
        return v is None


def df_safe_cols(rows) -> set:
    return set().union(*[r.keys() for r in rows]) if rows else set()


def write_compare(path: Path, dense: dict, hybrid: dict) -> None:
    cols = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    labels = {"faithfulness": "Faithfulness", "answer_relevancy": "Answer Relevancy",
              "context_precision": "Context Precision", "context_recall": "Context Recall"}
    def g(r, c): return r["metrics_mean"].get(c, float("nan"))
    lines = [
        "# UPI RAG — RAGAS Before/After (Dense vs Hybrid)",
        "",
        f"_Judge {dense['judge_model']} · {dense['n_samples']} sampel (set bersih) · "
        f"top_k={dense['top_k']} · embedding {dense['embeddings']}_",
        "",
        "| Metric | Dense (before) | Hybrid (after) | Δ |",
        "| --- | --- | --- | --- |",
    ]
    for c in cols:
        a, b = g(dense, c), g(hybrid, c)
        lines.append(f"| {labels[c]} | {a:.3f} | **{b:.3f}** | {b-a:+.3f} |")
    lines += [
        "",
        f"_Latensi generasi: dense {dense['mean_gen_ms']} ms, hybrid {hybrid['mean_gen_ms']} ms/jawaban._",
        "",
        "## Cara membaca",
        "- **Context Precision / Recall** mengukur kualitas RETRIEVAL → kenaikan di sini = "
        "bukti langsung hybrid memperbaiki retrieval (selaras dengan `evaluate_retrieval_hybrid.py`).",
        "- **Faithfulness / Answer Relevancy** bergantung pada jawaban yang dihasilkan; "
        "idealnya tidak turun (atau ikut naik karena konteks lebih relevan).",
        "",
        "Detail per mode ada di subfolder `dense/` dan `hybrid/` (ragas_report.md + ragas_per_sample.csv).",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_md(path: Path, report: dict, metric_cols: list[str]) -> None:
    m = report["metrics_mean"]
    jp = report.get("judge_provider", "ollama")
    lines = [
        "# UPI RAG — RAGAS Evaluation",
        "",
        f"_Judge: **{report['judge_model']}** ({jp}) · Gen: **{report['gen_model']}** · "
        f"Embeddings: **{report['embeddings']}** · {report['n_samples']} samples · "
        f"top_k={report['top_k']} · {report['elapsed_s']}s_",
        "",
        "## Scores (mean, 0–1, higher better)",
        "| Metric | Score | What it means |",
        "| --- | --- | --- |",
        f"| Faithfulness | **{m.get('faithfulness', float('nan')):.3f}** | Jawaban didukung konteks (anti-halusinasi) |",
        f"| Answer Relevancy | **{m.get('answer_relevancy', float('nan')):.3f}** | Jawaban menjawab pertanyaan |",
        f"| Context Precision | **{m.get('context_precision', float('nan')):.3f}** | Chunk yang diambil relevan (sedikit noise) |",
        f"| Context Recall | **{m.get('context_recall', float('nan')):.3f}** | Chunk memuat info jawaban referensi |",
        "",
        f"_Mean generation latency: {report['mean_gen_ms']} ms/answer._",
    ]
    nan = report.get("metrics_nan_count", {})
    if any(nan.values()):
        lines += ["", "> ⚠️ Beberapa sampel gagal diskor: " + ", ".join(f"{k}={v}" for k, v in nan.items() if v)
                  + ". Skor di atas = rata-rata sampel yang valid."]
    if report.get("by_category"):
        lines += ["", "## Per Kategori", "| Kategori | " + " | ".join(metric_cols) + " |",
                  "| --- |" + " --- |" * len(metric_cols)]
        for cat, vals in sorted(report["by_category"].items()):
            lines.append(f"| {cat} | " + " | ".join(f"{vals.get(c, float('nan')):.3f}" for c in metric_cols) + " |")

    # Add recommendations
    recs = generate_recommendations(report)
    if recs:
        lines += ["", "## 🎯 Rekomendasi untuk Penelitian Selanjutnya"]
        for i, rec in enumerate(recs, 1):
            lines.append(f"{i}. {rec}")

    lines += ["", "## Interpretasi (untuk skripsi)",
              "- **Faithfulness ≥ 0.8** = grounding baik, jarang berhalusinasi.",
              "- **Answer Relevancy ≥ 0.7** = jawaban tidak melantur.",
              "- **Context Precision/Recall** rendah → masalah RETRIEVAL (sejalan dgn evaluate_rag.py).",
              "- Lampirkan `ragas_per_sample.csv` sebagai apendiks untuk analisis kesalahan.",
              "", "## Files",
              "- `ragas_metrics.json` — angka machine-readable",
              "- `ragas_per_sample.csv` — skor per pertanyaan + jawaban yang dihasilkan"]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
