"""Reusable evaluation & model-comparison script for Chatbot RAG UPI.

Evaluates retrieval quality (deterministic, free) and answer quality
(LLM-as-a-Judge, RAGAS-inspired: faithfulness, answer relevancy, context
precision, context recall) for one or more generation models served by the
backend's /api/chat model override — talks to the running backend via its
REST API, so start the backend first.

The judge is Claude (Anthropic API), independent of the Ollama models being
compared, run under a hard USD budget so a re-evaluation never silently
overspends.

Usage:
    python run_eval.py
    python run_eval.py --models llama3.1:8b-instruct-q4_K_M qwen3.5:4b-q4_K_M
    python run_eval.py --budget 8.0 --ragas-sample 50
    python run_eval.py --retrieval-only          # skip LLM judge entirely (free)
    python run_eval.py --skip-judge --top-k 5    # generation only, no judge

Requires ANTHROPIC_API_KEY (or an `ant auth login` profile) unless
--retrieval-only / --skip-judge is used.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
import yaml

try:
    import anthropic
except ImportError:  # judge is optional if the user only wants retrieval metrics
    anthropic = None


# ---------------------------------------------------------------------------
# Config / dataset loading
# ---------------------------------------------------------------------------

def load_config(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_dataset(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Budget tracking for the LLM judge
# ---------------------------------------------------------------------------

@dataclass
class BudgetTracker:
    limit_usd: float
    price_input_per_mtok: float
    price_output_per_mtok: float
    spent_usd: float = 0.0
    n_calls: int = 0
    n_skipped: int = 0
    exhausted: bool = False

    def cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens / 1_000_000) * self.price_input_per_mtok + (
            output_tokens / 1_000_000
        ) * self.price_output_per_mtok

    def can_afford(self, est_input_tokens: int, est_output_tokens: int = 400) -> bool:
        if self.exhausted:
            return False
        projected = self.spent_usd + self.cost(est_input_tokens, est_output_tokens)
        return projected <= self.limit_usd

    def record(self, usage: Any) -> float:
        c = self.cost(usage.input_tokens, usage.output_tokens)
        self.spent_usd += c
        self.n_calls += 1
        if self.spent_usd >= self.limit_usd:
            self.exhausted = True
        return c

    def skip(self) -> None:
        self.n_skipped += 1
        self.exhausted = True

    def summary(self) -> dict:
        return {
            "limit_usd": self.limit_usd,
            "spent_usd": round(self.spent_usd, 4),
            "remaining_usd": round(max(0.0, self.limit_usd - self.spent_usd), 4),
            "judge_calls_made": self.n_calls,
            "judge_calls_skipped_over_budget": self.n_skipped,
        }


# ---------------------------------------------------------------------------
# Retrieval evaluation (deterministic, shared across all generation models)
# ---------------------------------------------------------------------------

def evaluate_retrieval(
    question: str,
    expected_doc_title: str,
    expected_keywords: list[str],
    base_url: str,
    top_k: int,
    score_threshold: float,
    expected_chunk_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Call /api/retrieve/debug and compute retrieval metrics for one question.

    If `expected_chunk_ids` is provided (chunk-level ground truth), the hit
    rank is computed by exact chunk_id match - far more precise than the
    doc-title substring fallback, since a document can be retrieved for the
    wrong section/page and still count as a "hit" under title matching.
    """
    params = {"query": question, "top_k": top_k, "score_threshold": score_threshold}
    resp = requests.get(f"{base_url}/api/retrieve/debug", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    chunks = data.get("results", [])
    scores = [c.get("score", 0) for c in chunks]
    titles = [c.get("title", "") for c in chunks]
    chunk_ids = [c.get("chunk_id", "") for c in chunks]

    hit_rank = None
    match_level = "none"
    if expected_chunk_ids:
        expected_set = set(expected_chunk_ids)
        for i, cid in enumerate(chunk_ids):
            if cid in expected_set:
                hit_rank = i + 1
                match_level = "chunk"
                break
    if hit_rank is None and expected_doc_title:
        for i, t in enumerate(titles):
            if expected_doc_title.lower() in t.lower():
                hit_rank = i + 1
                match_level = "doc_title"
                break

    keyword_hits = 0
    if expected_keywords:
        all_text = " ".join(c.get("text", "") for c in chunks).lower()
        for kw in expected_keywords:
            if kw.lower() in all_text:
                keyword_hits += 1

    has_ground_truth = bool(expected_chunk_ids) or bool(expected_doc_title)
    ground_truth_level = "chunk" if expected_chunk_ids else ("doc_title" if expected_doc_title else "none")

    return {
        "num_results": len(chunks),
        "scores": scores,
        "avg_score": sum(scores) / len(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "hit_rank": hit_rank,
        "hit_found": hit_rank is not None,
        "match_level": match_level,
        "has_ground_truth": has_ground_truth,
        "ground_truth_level": ground_truth_level,
        "keyword_coverage": keyword_hits / len(expected_keywords) if expected_keywords else 1.0,
        "top_titles": titles[:5],
        "chunks": chunks,  # kept for the judge; stripped before final JSON write
        "timings_ms": data.get("timings", {}),
    }


def compute_retrieval_aggregate(retrieval_results: list[dict], hit_rate_ks: list[int]) -> dict:
    # Only questions that actually carry ground truth (chunk or doc-title)
    # count toward recall/precision/MRR - a question with no ground truth
    # can't be scored as a "miss".
    with_expected = [r for r in retrieval_results if r.get("has_ground_truth")]
    n = len(with_expected) or 1
    n_chunk_level_gt = sum(1 for r in with_expected if r.get("ground_truth_level") == "chunk")

    agg: dict[str, Any] = {
        "n_questions": len(retrieval_results),
        "n_with_ground_truth": len(with_expected),
        "n_with_chunk_level_ground_truth": n_chunk_level_gt,
        "avg_score_mean": sum(r["avg_score"] for r in retrieval_results) / (len(retrieval_results) or 1),
        "avg_max_score": sum(r["max_score"] for r in retrieval_results) / (len(retrieval_results) or 1),
        "hit_rate": sum(1 for r in with_expected if r["hit_found"]) / n,
        "mrr": sum((1.0 / r["hit_rank"]) for r in with_expected if r["hit_rank"]) / n,
        "avg_keyword_coverage": sum(r["keyword_coverage"] for r in retrieval_results) / (len(retrieval_results) or 1),
        "recall_at_k": {},
        "precision_at_k": {},
    }
    for k in hit_rate_ks:
        agg["recall_at_k"][str(k)] = sum(
            1 for r in with_expected if r["hit_rank"] is not None and r["hit_rank"] <= k
        ) / n
        # Precision@k here is an upper-bound estimate (1/k on a hit) unless
        # the ground truth is chunk-level, in which case it's still a single
        # relevant-chunk assumption per question - documented caveat, see README.
        agg["precision_at_k"][str(k)] = sum(
            (1.0 / k) for r in with_expected if r["hit_rank"] is not None and r["hit_rank"] <= k
        ) / n
    return agg


# ---------------------------------------------------------------------------
# Generation (per model, via /api/chat model override)
# ---------------------------------------------------------------------------

def generate_answer(question: str, base_url: str, model: str, top_k: int) -> dict[str, Any]:
    body = {"message": question, "language": "id", "top_k": top_k, "model": model}
    t0 = time.time()
    resp = requests.post(f"{base_url}/api/chat", json=body, timeout=180)
    latency_ms = (time.time() - t0) * 1000
    resp.raise_for_status()
    data = resp.json()
    return {
        "answer": data.get("answer", ""),
        "backend_used": data.get("backend") or data.get("backend_used"),
        "sources": data.get("sources", []),
        "latency_ms": latency_ms,
    }


# ---------------------------------------------------------------------------
# LLM-as-a-Judge (RAGAS-inspired: faithfulness, answer relevancy,
# context precision, context recall)
# ---------------------------------------------------------------------------

ANSWER_JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "faithfulness_score": {
            "type": "number",
            "description": "0.0-1.0: fraction of claims in the answer that are directly supported by the context. 1.0 = fully grounded, no hallucination.",
        },
        "faithfulness_reasoning": {"type": "string"},
        "answer_relevancy_score": {
            "type": "number",
            "description": "0.0-1.0: how directly and completely the answer addresses the question, ignoring groundedness.",
        },
        "answer_relevancy_reasoning": {"type": "string"},
    },
    "required": [
        "faithfulness_score",
        "faithfulness_reasoning",
        "answer_relevancy_score",
        "answer_relevancy_reasoning",
    ],
    "additionalProperties": False,
}

CONTEXT_JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "context_precision_score": {
            "type": "number",
            "description": "0.0-1.0: fraction of retrieved chunks that are actually relevant/useful for answering the question.",
        },
        "context_precision_reasoning": {"type": "string"},
        "context_recall_score": {
            "type": "number",
            "description": "0.0-1.0: fraction of the ground-truth answer's information that is present somewhere in the retrieved context. Return -1 if no ground truth was provided.",
        },
        "context_recall_reasoning": {"type": "string"},
    },
    "required": [
        "context_precision_score",
        "context_precision_reasoning",
        "context_recall_score",
        "context_recall_reasoning",
    ],
    "additionalProperties": False,
}


def _format_context(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        title = c.get("title", "Dokumen")
        page = c.get("page")
        loc = f" (hal. {page})" if page is not None else ""
        parts.append(f"[{i}] {title}{loc}\n{c.get('text', '').strip()}")
    return "\n\n".join(parts) if parts else "(tidak ada konteks yang di-retrieve)"


def _judge_call(
    client: "anthropic.Anthropic",
    judge_model: str,
    system: str,
    user: str,
    schema: dict,
    budget: BudgetTracker,
) -> dict | None:
    """One structured-output judge call, budget-gated. Returns None if skipped."""
    # Rough pre-flight estimate (chars/4) to decide whether to even attempt
    # the call - avoids paying for a request we know will blow the budget.
    est_input_tokens = (len(system) + len(user)) // 4
    if not budget.can_afford(est_input_tokens):
        budget.skip()
        return None

    try:
        response = client.messages.create(
            model=judge_model,
            max_tokens=600,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
    except Exception as exc:  # noqa: BLE001
        print(f"    [judge error] {exc}", file=sys.stderr)
        return None

    budget.record(response.usage)
    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"    [judge parse error] raw={text[:200]!r}", file=sys.stderr)
        return None


def judge_context(
    client: "anthropic.Anthropic",
    judge_model: str,
    question: str,
    context: str,
    ground_truth: str,
    budget: BudgetTracker,
) -> dict | None:
    system = (
        "You are a meticulous evaluator for a Retrieval-Augmented Generation (RAG) "
        "system serving an Indonesian university (UPI). You judge RETRIEVED CONTEXT "
        "quality only, not any generated answer. Be strict and evidence-based. "
        "Respond only via the provided JSON schema."
    )
    gt_block = ground_truth.strip() or "(tidak tersedia - kosongkan context_recall_score = -1)"
    user = (
        f"PERTANYAAN:\n{question}\n\n"
        f"KONTEKS YANG DI-RETRIEVE:\n{context}\n\n"
        f"GROUND TRUTH (jawaban ideal, jika tersedia):\n{gt_block}\n\n"
        "Nilai context_precision (apakah chunk yang di-retrieve relevan untuk "
        "menjawab pertanyaan) dan context_recall (apakah informasi yang dibutuhkan "
        "ground truth tercakup dalam konteks; -1 jika ground truth tidak tersedia)."
    )
    return _judge_call(client, judge_model, system, user, CONTEXT_JUDGE_SCHEMA, budget)


def judge_answer(
    client: "anthropic.Anthropic",
    judge_model: str,
    question: str,
    context: str,
    answer: str,
    budget: BudgetTracker,
) -> dict | None:
    system = (
        "You are a meticulous evaluator for a Retrieval-Augmented Generation (RAG) "
        "system serving an Indonesian university (UPI). You judge a GENERATED ANSWER "
        "against its retrieved context and the question. Be strict and evidence-based - "
        "penalize hallucinated claims not present in the context, and penalize answers "
        "that dodge or only partially address the question. Respond only via the "
        "provided JSON schema."
    )
    user = (
        f"PERTANYAAN:\n{question}\n\n"
        f"KONTEKS YANG DI-RETRIEVE (satu-satunya sumber informasi yang sah):\n{context}\n\n"
        f"JAWABAN YANG DIHASILKAN MODEL:\n{answer}\n\n"
        "Nilai faithfulness (apakah jawaban hanya berdasarkan konteks di atas, tanpa "
        "klaim yang tidak didukung) dan answer_relevancy (apakah jawaban benar-benar "
        "menjawab pertanyaan)."
    )
    return _judge_call(client, judge_model, system, user, ANSWER_JUDGE_SCHEMA, budget)


# ---------------------------------------------------------------------------
# Per-model answer aggregate
# ---------------------------------------------------------------------------

def compute_answer_aggregate(entries: list[dict]) -> dict:
    judged = [e for e in entries if e.get("judge")]
    refusal_markers = [
        "tidak tersedia", "tidak ditemukan", "tidak ada informasi",
        "maaf", "tidak dapat menemukan",
    ]
    n = len(entries) or 1
    agg: dict[str, Any] = {
        "n_questions": len(entries),
        "n_judged": len(judged),
        "avg_latency_ms": sum(e["latency_ms"] for e in entries) / n,
        "avg_answer_length_chars": sum(len(e["answer"]) for e in entries) / n,
        "refusal_rate": sum(
            1 for e in entries if any(m in e["answer"].lower() for m in refusal_markers)
        ) / n,
    }
    if judged:
        faith = [e["judge"]["faithfulness_score"] for e in judged]
        rel = [e["judge"]["answer_relevancy_score"] for e in judged]
        agg["faithfulness"] = sum(faith) / len(faith)
        agg["answer_relevancy"] = sum(rel) / len(rel)
    return agg


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def print_comparison_table(model_labels: dict[str, str], per_model_agg: dict[str, dict], retrieval_agg: dict) -> None:
    print("\n" + "=" * 78)
    print("PERBANDINGAN MODEL - CHATBOT RAG UPI")
    print("=" * 78)

    print("\n[Retrieval - identik untuk semua model, dihitung sekali]")
    print(f"  Questions w/ ground truth: {retrieval_agg['n_with_ground_truth']}/{retrieval_agg['n_questions']} "
          f"({retrieval_agg['n_with_chunk_level_ground_truth']} chunk-level)")
    print(f"  Hit Rate:          {retrieval_agg['hit_rate']:.1%}")
    print(f"  MRR:               {retrieval_agg['mrr']:.3f}")
    for k, v in retrieval_agg["recall_at_k"].items():
        print(f"  Recall@{k}:         {v:.1%}")
    print(f"  Avg Keyword Cov:   {retrieval_agg['avg_keyword_coverage']:.1%}")

    print("\n[Answer Quality - per model]")
    header = f"{'Metric':<28}" + "".join(f"{model_labels.get(m, m):<28}" for m in per_model_agg)
    print(header)
    print("-" * len(header))

    def row(label: str, key: str, fmt: str = "{:.3f}") -> None:
        cells = []
        for m, agg in per_model_agg.items():
            v = agg.get(key)
            cells.append(f"{fmt.format(v):<28}" if v is not None else f"{'n/a':<28}")
        print(f"{label:<28}" + "".join(cells))

    row("Faithfulness", "faithfulness")
    row("Answer Relevancy", "answer_relevancy")
    row("Refusal Rate", "refusal_rate", "{:.1%}")
    row("Avg Latency (ms)", "avg_latency_ms", "{:.0f}")
    row("Avg Answer Len (chars)", "avg_answer_length_chars", "{:.0f}")
    row("Questions Judged", "n_judged", "{:.0f}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate & compare generation models for Chatbot RAG UPI")
    parser.add_argument("--models", nargs="+", default=None, help="Model names to compare (overrides config.yaml)")
    parser.add_argument("--budget", type=float, default=None, help="Judge budget in USD (overrides config.yaml)")
    parser.add_argument("--judge-model", type=str, default=None, help="Anthropic judge model (overrides config.yaml)")
    parser.add_argument("--ragas-sample", type=int, default=None, help="Number of questions to LLM-judge (default: all)")
    parser.add_argument("--retrieval-only", action="store_true", help="Skip generation and judging entirely")
    parser.add_argument("--skip-judge", action="store_true", help="Run generation but skip the LLM judge (free)")
    parser.add_argument("--top-k", type=int, default=None, help="Override retrieval top_k")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    parser.add_argument("--dataset", type=str, default="dataset.json", help="Dataset path")
    parser.add_argument("--config", type=str, default="config.yaml", help="Config path")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    dataset = load_dataset(Path(args.dataset))

    base_url = config["backend_url"].rstrip("/")
    top_k = args.top_k or config["retrieval"]["top_k"]
    score_threshold = config["retrieval"]["score_threshold"]
    hit_rate_ks = config["evaluation"].get("hit_rate_k", [1, 3, 5])

    model_cfgs = config.get("models", [])
    if args.models:
        models = [{"name": m, "label": m} for m in args.models]
    else:
        models = model_cfgs
    model_names = [m["name"] for m in models]
    model_labels = {m["name"]: m.get("label", m["name"]) for m in models}

    judge_cfg = config.get("judge", {})
    budget_usd = args.budget if args.budget is not None else judge_cfg.get("budget_usd", 8.0)
    judge_model = args.judge_model or judge_cfg.get("model", "claude-haiku-4-5")
    ragas_sample = args.ragas_sample if args.ragas_sample is not None else judge_cfg.get("ragas_sample_size")
    sample_seed = judge_cfg.get("sample_seed", 42)

    do_generation = not args.retrieval_only
    do_judge = do_generation and not args.retrieval_only and not args.skip_judge

    client = None
    if do_judge:
        if anthropic is None:
            print("[ERROR] Package 'anthropic' tidak terinstall. pip install -r requirements.txt "
                  "atau jalankan dengan --skip-judge.", file=sys.stderr)
            return 1
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("[WARNING] ANTHROPIC_API_KEY tidak diset - mencoba profil `ant auth login`.")
        client = anthropic.Anthropic()

    try:
        requests.get(f"{base_url}/health", timeout=5)
    except requests.ConnectionError:
        print(f"[ERROR] Backend tidak berjalan di {base_url}")
        print("        Jalankan backend terlebih dahulu: python -m uvicorn app.main:app")
        return 1

    print(f"Evaluasi dimulai: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Dataset: {len(dataset)} pertanyaan | top_k={top_k} | models={model_names}")
    print(f"Mode: generation={'on' if do_generation else 'off'} | judge={'on' if do_judge else 'off'}"
          f"{f' (budget=${budget_usd:.2f}, judge_model={judge_model})' if do_judge else ''}")
    print()

    # --- Retrieval (once, shared across all models) -----------------------
    print("[1/3] Evaluating retrieval (shared across models)...")
    retrieval_by_qid: dict[str, dict] = {}
    for i, item in enumerate(dataset, 1):
        qid = item.get("id", f"Q{i:02d}")
        print(f"  [{i}/{len(dataset)}] {qid}", end=" ", flush=True)
        t0 = time.time()
        ret = evaluate_retrieval(
            item["question"], item.get("expected_doc_title", ""),
            item.get("expected_keywords", []), base_url, top_k, score_threshold,
            expected_chunk_ids=item.get("expected_chunk_ids"),
        )
        retrieval_by_qid[qid] = ret
        print(f"({(time.time() - t0) * 1000:.0f}ms, hit={ret['hit_found']})")

    retrieval_agg = compute_retrieval_aggregate(list(retrieval_by_qid.values()), hit_rate_ks)

    if not do_generation:
        results = {
            "timestamp": datetime.now().isoformat(),
            "mode": "retrieval_only",
            "config": {"top_k": top_k, "score_threshold": score_threshold},
            "retrieval_aggregate": retrieval_agg,
            "retrieval_by_question": {
                qid: {k: v for k, v in r.items() if k != "chunks"} for qid, r in retrieval_by_qid.items()
            },
        }
        _write_report(config, args.output, results)
        return 0

    # --- Determine which questions get LLM-judged --------------------------
    judge_qids: set[str] = set()
    if do_judge:
        all_qids = [item.get("id", f"Q{i:02d}") for i, item in enumerate(dataset, 1)]
        if ragas_sample and ragas_sample < len(all_qids):
            rng = random.Random(sample_seed)
            judge_qids = set(rng.sample(all_qids, ragas_sample))
            print(f"[budget] Sampling {ragas_sample}/{len(all_qids)} questions for LLM judging "
                  f"(seed={sample_seed}).")
        else:
            judge_qids = set(all_qids)

    budget = BudgetTracker(
        limit_usd=budget_usd,
        price_input_per_mtok=judge_cfg.get("price_input_per_mtok", 1.0),
        price_output_per_mtok=judge_cfg.get("price_output_per_mtok", 5.0),
    ) if do_judge else None

    # --- Context judging (once per question, shared across models) --------
    context_judgments: dict[str, dict] = {}
    if do_judge:
        print(f"\n[2/3] Judging retrieved context quality (Claude {judge_model})...")
        for i, item in enumerate(dataset, 1):
            qid = item.get("id", f"Q{i:02d}")
            if qid not in judge_qids:
                continue
            if budget.exhausted:
                print(f"  [{i}/{len(dataset)}] {qid}: budget exhausted, skipping")
                budget.skip()
                continue
            context = _format_context(retrieval_by_qid[qid]["chunks"])
            j = judge_context(client, judge_model, item["question"], context,
                               item.get("ground_truth", ""), budget)
            if j:
                context_judgments[qid] = j
            print(f"  [{i}/{len(dataset)}] {qid}: precision={j.get('context_precision_score') if j else 'skipped'} "
                  f"(spent=${budget.spent_usd:.3f}/${budget_usd:.2f})")

    # --- Generation + answer judging (per model) ----------------------------
    print(f"\n[3/3] Generating & judging answers for {len(model_names)} model(s)...")
    per_model_entries: dict[str, list[dict]] = {m: [] for m in model_names}
    for mi, model in enumerate(model_names, 1):
        print(f"\n  --- Model {mi}/{len(model_names)}: {model} ---")
        for i, item in enumerate(dataset, 1):
            qid = item.get("id", f"Q{i:02d}")
            print(f"    [{i}/{len(dataset)}] {qid}", end=" ", flush=True)
            gen = generate_answer(item["question"], base_url, model, top_k)

            judge_result = None
            if do_judge and qid in judge_qids and not budget.exhausted:
                context = _format_context(retrieval_by_qid[qid]["chunks"])
                judge_result = judge_answer(client, judge_model, item["question"], context,
                                             gen["answer"], budget)
            elif do_judge and budget.exhausted:
                budget.skip()

            per_model_entries[model].append({
                "id": qid,
                "question": item["question"],
                "answer": gen["answer"],
                "backend_used": gen["backend_used"],
                "latency_ms": gen["latency_ms"],
                "judge": judge_result,
            })
            status = f"faith={judge_result['faithfulness_score']:.2f}" if judge_result else (
                "judged-skip" if do_judge else "")
            print(f"({gen['latency_ms']:.0f}ms{', ' + status if status else ''})")

    per_model_agg = {m: compute_answer_aggregate(entries) for m, entries in per_model_entries.items()}

    print_comparison_table(model_labels, per_model_agg, retrieval_agg)
    if do_judge:
        print("[Judge Budget]")
        for k, v in budget.summary().items():
            print(f"  {k}: {v}")
        print()

    results = {
        "timestamp": datetime.now().isoformat(),
        "mode": "full",
        "config": {
            "top_k": top_k,
            "score_threshold": score_threshold,
            "models": models,
            "judge_model": judge_model if do_judge else None,
        },
        "budget": budget.summary() if do_judge else None,
        "retrieval_aggregate": retrieval_agg,
        "per_model_aggregate": per_model_agg,
        "context_judgments": context_judgments,
        "retrieval_by_question": {
            qid: {k: v for k, v in r.items() if k != "chunks"} for qid, r in retrieval_by_qid.items()
        },
        "per_model_results": per_model_entries,
    }
    _write_report(config, args.output, results)
    return 0


def _write_report(config: dict, output_arg: str | None, report: dict) -> None:
    output_dir = Path(config["output"]["dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_arg or config["output"].get("filename")
    if not output_path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"eval_{ts}.json"
    else:
        output_path = Path(output_path)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Hasil disimpan ke: {output_path}")


if __name__ == "__main__":
    sys.exit(main())
