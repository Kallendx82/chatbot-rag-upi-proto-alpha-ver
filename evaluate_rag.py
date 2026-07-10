"""evaluate_rag.py
=============================================================================
Turn the UPI knowledge layer into THESIS RESULTS.

Scores the *real* deployed retriever (the existing FAISS index built with
intfloat/multilingual-e5-base) against the generated evaluation datasets:

  retrieval_eval.jsonl   -> Recall@K, Hit@K, MRR, nDCG@K, Precision@K
                            at CHUNK and DOCUMENT level,
                            broken down overall / by difficulty / by category
  query_variations.jsonl -> paraphrase robustness (retrieval stability)
  hallucination_test.jsonl -> score-gate refusal analysis (in- vs out-of-corpus)

This replicates the backend's retrieval EXACTLY:
  * SentenceTransformer("intfloat/multilingual-e5-base")
  * "query: " prefix, normalize_embeddings=True, float32
  * FAISS IndexFlatIP (cosine) over the row-aligned chunks_meta.json
so the numbers reflect the system you actually ship. No LLM is required; the
whole run is deterministic and finishes in minutes.

OUTPUTS (in knowledge_layer/eval/):
  eval_report.md            human-readable tables for the thesis
  retrieval_metrics.json    machine-readable metrics
  per_query_results.csv     per-query rows for error analysis / appendix
  (optional) *.png charts if matplotlib is installed

USAGE
    python evaluate_rag.py
    python evaluate_rag.py --ks 1 3 5 10 --limit 200      # quick subset
    python evaluate_rag.py --no-variations                # skip robustness pass
=============================================================================
"""
from __future__ import annotations

# --- Windows native-crash workaround (faiss + torch). Preload heavy native libs
# in the order verified to load cleanly, else faiss+torch segfault (0xC0000005). ---
import os as _os
_os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
import ragas  # noqa: F401,E402
import langchain_ollama  # noqa: F401,E402
import sentence_transformers  # noqa: F401,E402
import faiss  # noqa: F401,E402
# ------------------------------------------------------------------------------

import argparse
import csv
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

RAG_ROOT = Path(r"D:\Project\RAG_UPI")
DEFAULT_KL = RAG_ROOT / "knowledge_layer"
DEFAULT_INDEX_DIR = RAG_ROOT / "Dataset" / "_pipeline" / "index"
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"


def log(m: str) -> None:
    print(f"[eval] {m}", flush=True)


# --------------------------------------------------------------------------- #
# Retriever (mirrors app/rag/vectorstore.py + embedder.py)
# --------------------------------------------------------------------------- #
class Retriever:
    def __init__(self, index_dir: Path, model_name: str = EMBEDDING_MODEL):
        import faiss
        from sentence_transformers import SentenceTransformer

        info_path = index_dir / "index_info.json"
        self.info = json.loads(info_path.read_text(encoding="utf-8")) if info_path.exists() else {}
        model_name = self.info.get("embedding_model", model_name)
        self.use_prefix = bool(self.info.get("use_e5_prefixes", True))

        log(f"loading FAISS index: {index_dir / 'faiss.index'}")
        self.index = faiss.read_index(str(index_dir / "faiss.index"))
        log("loading chunks_meta.json (row-aligned)...")
        self.meta = json.loads((index_dir / "chunks_meta.json").read_text(encoding="utf-8"))
        if self.index.ntotal != len(self.meta):
            raise SystemExit(f"index/meta mismatch: {self.index.ntotal} vs {len(self.meta)}")
        log(f"loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        log(f"retriever ready: {self.index.ntotal:,} vectors, dim={self.index.d}")

        # quick lookup of which chunk_ids actually exist in the index
        self.valid_chunk_ids = {m.get("chunk_id") for m in self.meta}

    def encode_queries(self, queries: list[str]) -> np.ndarray:
        prepared = [("query: " + q) if self.use_prefix else q for q in queries]
        vecs = self.model.encode(
            prepared, batch_size=64, convert_to_numpy=True,
            normalize_embeddings=True, show_progress_bar=False,
        )
        return vecs.astype("float32")

    def search_batch(self, queries: list[str], k: int) -> tuple[np.ndarray, np.ndarray]:
        qv = self.encode_queries(queries)
        scores, idxs = self.index.search(qv, k)
        return scores, idxs

    def chunk_id(self, row: int) -> str:
        return self.meta[row].get("chunk_id", "")

    def doc_id(self, row: int) -> str:
        return self.meta[row].get("doc_id", "")


# --------------------------------------------------------------------------- #
# Metric helpers (per-query, given the ranked list of retrieved ids)
# --------------------------------------------------------------------------- #
def per_query_metrics(retrieved: list[str], expected: set[str], ks: list[int]) -> dict:
    """retrieved: ranked ids (best first). expected: gold id set."""
    out: dict[str, float] = {}
    n_rel = len(expected)
    # first relevant rank (for MRR)
    first_rel = 0
    for i, rid in enumerate(retrieved, start=1):
        if rid in expected:
            first_rel = i
            break
    out["mrr"] = 1.0 / first_rel if first_rel else 0.0
    for k in ks:
        topk = retrieved[:k]
        hit = sum(1 for r in topk if r in expected)
        out[f"hit@{k}"] = 1.0 if hit > 0 else 0.0
        out[f"recall@{k}"] = hit / n_rel if n_rel else 0.0
        out[f"precision@{k}"] = hit / k if k else 0.0
        # nDCG@k with binary relevance
        dcg = sum((1.0 / math.log2(i + 1)) for i, r in enumerate(topk, start=1) if r in expected)
        ideal = min(n_rel, k)
        idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal + 1))
        out[f"ndcg@{k}"] = (dcg / idcg) if idcg else 0.0
    return out


def mean_metrics(rows: list[dict], keys: list[str]) -> dict:
    if not rows:
        return {k: 0.0 for k in keys}
    return {k: round(sum(r[k] for r in rows) / len(rows), 4) for k in keys}


def dedup_keep_order(seq: list[str]) -> list[str]:
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


# --------------------------------------------------------------------------- #
# Core retrieval evaluation
# --------------------------------------------------------------------------- #
def evaluate_retrieval(retr: Retriever, rows: list[dict], ks: list[int], batch: int = 256):
    maxk = max(ks)
    metric_keys = ["mrr"] + [f"{m}@{k}" for k in ks for m in ("hit", "recall", "precision", "ndcg")]

    chunk_rows: list[dict] = []
    doc_rows: list[dict] = []
    per_query_csv: list[dict] = []
    top1_scores: list[float] = []
    missing_gold = 0

    for start in range(0, len(rows), batch):
        chunk = rows[start:start + batch]
        queries = [r["query"] for r in chunk]
        scores, idxs = retr.search_batch(queries, maxk)
        for j, r in enumerate(chunk):
            exp_chunks = set(r.get("expected_chunk_ids") or [])
            exp_docs = set(r.get("expected_doc_ids") or [])
            # validity check
            if exp_chunks and not (exp_chunks & retr.valid_chunk_ids):
                missing_gold += 1
            ret_chunk_ids, ret_doc_ids, row_scores = [], [], []
            for rank, row_idx in enumerate(idxs[j]):
                if row_idx < 0:
                    continue
                ret_chunk_ids.append(retr.chunk_id(int(row_idx)))
                ret_doc_ids.append(retr.doc_id(int(row_idx)))
                row_scores.append(float(scores[j][rank]))
            if row_scores:
                top1_scores.append(row_scores[0])

            cm = per_query_metrics(ret_chunk_ids, exp_chunks, ks)
            dm = per_query_metrics(dedup_keep_order(ret_doc_ids), exp_docs, ks)
            cm.update({"difficulty": r.get("difficulty", "?"), "category": r.get("category", "?")})
            dm.update({"difficulty": r.get("difficulty", "?"), "category": r.get("category", "?")})
            chunk_rows.append(cm)
            doc_rows.append(dm)
            per_query_csv.append({
                "question_id": r.get("question_id", ""),
                "query": r["query"][:120],
                "difficulty": r.get("difficulty", "?"),
                "category": r.get("category", "?"),
                "n_expected_chunks": len(exp_chunks),
                f"hit@{ks[0]}_chunk": cm[f"hit@{ks[0]}"],
                f"recall@{maxk}_chunk": cm[f"recall@{maxk}"],
                "mrr_chunk": round(cm["mrr"], 4),
                f"hit@{ks[0]}_doc": dm[f"hit@{ks[0]}"],
                f"recall@{maxk}_doc": dm[f"recall@{maxk}"],
                "mrr_doc": round(dm["mrr"], 4),
                "top1_score": round(row_scores[0], 4) if row_scores else 0.0,
            })
        log(f"  retrieval {min(start + batch, len(rows))}/{len(rows)}")

    return {
        "metric_keys": metric_keys,
        "chunk_overall": mean_metrics(chunk_rows, metric_keys),
        "doc_overall": mean_metrics(doc_rows, metric_keys),
        "chunk_rows": chunk_rows,
        "doc_rows": doc_rows,
        "per_query_csv": per_query_csv,
        "top1_scores": top1_scores,
        "missing_gold": missing_gold,
    }


def grouped(rows: list[dict], by: str, keys: list[str]) -> dict[str, dict]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        buckets[r.get(by, "?")].append(r)
    return {g: {"n": len(rs), **mean_metrics(rs, keys)} for g, rs in sorted(buckets.items())}


# --------------------------------------------------------------------------- #
# Query-variation robustness
# --------------------------------------------------------------------------- #
def evaluate_robustness(retr: Retriever, var_rows: list[dict], ks: list[int],
                        limit: int | None = None) -> dict:
    maxk = max(ks)
    rep_k = ks[len(ks) // 2]  # a representative K (e.g. 5)
    canonical_hit, var_hit = [], []
    canonical_recall, var_recall = [], []
    jaccard = []
    rows = var_rows[:limit] if limit else var_rows
    for r in rows:
        exp = set(r.get("expected_chunk_ids") or [])
        if not exp:
            continue
        canon = r.get("canonical_query") or ""
        variations = [v for v in (r.get("variations") or []) if v.strip()]
        if not canon or not variations:
            continue
        queries = [canon] + variations
        _, idxs = retr.search_batch(queries, maxk)
        ret_sets = []
        for j in range(len(queries)):
            ids = [retr.chunk_id(int(x)) for x in idxs[j] if x >= 0]
            ret_sets.append(ids)
        # canonical
        cm = per_query_metrics(ret_sets[0], exp, [rep_k])
        canonical_hit.append(cm[f"hit@{rep_k}"])
        canonical_recall.append(cm[f"recall@{rep_k}"])
        canon_topset = set(ret_sets[0][:maxk])
        # variations
        for vi in range(1, len(queries)):
            vm = per_query_metrics(ret_sets[vi], exp, [rep_k])
            var_hit.append(vm[f"hit@{rep_k}"])
            var_recall.append(vm[f"recall@{rep_k}"])
            vset = set(ret_sets[vi][:maxk])
            union = canon_topset | vset
            jaccard.append(len(canon_topset & vset) / len(union) if union else 0.0)
    def m(x): return round(sum(x) / len(x), 4) if x else 0.0
    return {
        "rep_k": rep_k,
        "n_base": len(canonical_hit),
        "n_variations": len(var_hit),
        "canonical_hit": m(canonical_hit),
        "variation_hit": m(var_hit),
        "hit_drop": round(m(canonical_hit) - m(var_hit), 4),
        "canonical_recall": m(canonical_recall),
        "variation_recall": m(var_recall),
        "topk_jaccard_stability": m(jaccard),
    }


# --------------------------------------------------------------------------- #
# Hallucination: score-gate analysis (in-corpus vs out-of-corpus top-1 score)
# --------------------------------------------------------------------------- #
def evaluate_hallucination(retr: Retriever, halluc_rows: list[dict],
                           in_corpus_top1: list[float]) -> dict:
    queries = [h["question"] for h in halluc_rows]
    scores, _ = retr.search_batch(queries, 1)
    out_top1 = [float(scores[j][0]) for j in range(len(queries))]
    in_arr = np.array(in_corpus_top1) if in_corpus_top1 else np.array([0.0])
    out_arr = np.array(out_top1) if out_top1 else np.array([0.0])

    # candidate gate = 5th percentile of in-corpus top1 scores (keep ~95% of real queries)
    gate = float(np.percentile(in_arr, 5))
    # refusal recall: fraction of out-of-corpus queries correctly below the gate
    refusal_recall = float((out_arr < gate).mean())
    # false refusal: fraction of in-corpus queries wrongly below the gate
    false_refusal = float((in_arr < gate).mean())
    return {
        "n_hallucination": len(out_top1),
        "in_corpus_top1_mean": round(float(in_arr.mean()), 4),
        "in_corpus_top1_p5": round(float(np.percentile(in_arr, 5)), 4),
        "in_corpus_top1_median": round(float(np.median(in_arr)), 4),
        "out_corpus_top1_mean": round(float(out_arr.mean()), 4),
        "out_corpus_top1_median": round(float(np.median(out_arr)), 4),
        "out_corpus_top1_max": round(float(out_arr.max()), 4),
        "suggested_score_gate": round(gate, 4),
        "refusal_recall_at_gate": round(refusal_recall, 4),
        "false_refusal_rate_at_gate": round(false_refusal, 4),
    }


# --------------------------------------------------------------------------- #
# Optional charts
# --------------------------------------------------------------------------- #
def make_charts(out_dir: Path, chunk_overall: dict, doc_overall: dict, ks: list[int],
                in_top1: list[float], out_top1: list[float]) -> list[str]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return []
    made = []
    # 1. Recall@K / nDCG@K curves
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(ks, [chunk_overall[f"recall@{k}"] for k in ks], "o-", label="Recall@K (chunk)")
    ax.plot(ks, [doc_overall[f"recall@{k}"] for k in ks], "s--", label="Recall@K (doc)")
    ax.plot(ks, [chunk_overall[f"ndcg@{k}"] for k in ks], "^-", label="nDCG@K (chunk)")
    ax.set_xlabel("K"); ax.set_ylabel("score"); ax.set_ylim(0, 1.0)
    ax.set_title("Retrieval quality vs K"); ax.legend(); ax.grid(alpha=0.3)
    p = out_dir / "retrieval_at_k.png"; fig.tight_layout(); fig.savefig(p, dpi=130); plt.close(fig)
    made.append(p.name)
    # 2. score distributions
    if in_top1 and out_top1:
        fig, ax = plt.subplots(figsize=(7, 4.2))
        ax.hist(in_top1, bins=30, alpha=0.6, label="in-corpus (answerable)", density=True)
        ax.hist(out_top1, bins=12, alpha=0.6, label="out-of-corpus (should refuse)", density=True)
        ax.set_xlabel("top-1 cosine score"); ax.set_ylabel("density")
        ax.set_title("Top-1 retrieval score: answerable vs out-of-corpus")
        ax.legend(); ax.grid(alpha=0.3)
        p = out_dir / "score_distribution.png"; fig.tight_layout(); fig.savefig(p, dpi=130); plt.close(fig)
        made.append(p.name)
    return made


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def fmt_table(headers: list[str], rows: list[list[str]]) -> str:
    line1 = "| " + " | ".join(headers) + " |"
    line2 = "| " + " | ".join("---" for _ in headers) + " |"
    body = "\n".join("| " + " | ".join(str(c) for c in r) + " |" for r in rows)
    return "\n".join([line1, line2, body])


def write_report(out_dir: Path, ks: list[int], res: dict, by_diff_chunk: dict,
                 by_cat_chunk: dict, by_diff_doc: dict, robustness: dict | None,
                 halluc: dict | None, retr_info: dict, n_queries: int,
                 charts: list[str], elapsed: float) -> None:
    co, do = res["chunk_overall"], res["doc_overall"]
    lines = [
        "# UPI RAG — Retrieval Evaluation Results",
        "",
        f"_Generated: {time.strftime('%Y-%m-%d %H:%M:%S')} · {elapsed:.1f}s_",
        "",
        "## Setup",
        f"- Retriever: **{retr_info.get('embedding_model', EMBEDDING_MODEL)}**, "
        f"FAISS IndexFlatIP (cosine), **{retr_info.get('n_vectors','?')}** vectors.",
        f"- Evaluation queries: **{n_queries}** (from `retrieval_eval.jsonl`).",
        f"- Gold = the chunk(s) each question was generated from. "
        f"Chunk-level is strict; document-level credits retrieving the right source document.",
        "",
        "## Headline metrics (mean over all queries)",
        "",
        "**Chunk-level**",
        fmt_table(["Metric"] + [f"@{k}" for k in ks],
                  [["Recall"] + [f"{co[f'recall@{k}']:.3f}" for k in ks],
                   ["Hit"] + [f"{co[f'hit@{k}']:.3f}" for k in ks],
                   ["nDCG"] + [f"{co[f'ndcg@{k}']:.3f}" for k in ks],
                   ["Precision"] + [f"{co[f'precision@{k}']:.3f}" for k in ks]]),
        "",
        f"**MRR (chunk-level): {co['mrr']:.3f}**",
        "",
        "**Document-level**",
        fmt_table(["Metric"] + [f"@{k}" for k in ks],
                  [["Recall"] + [f"{do[f'recall@{k}']:.3f}" for k in ks],
                   ["Hit"] + [f"{do[f'hit@{k}']:.3f}" for k in ks],
                   ["nDCG"] + [f"{do[f'ndcg@{k}']:.3f}" for k in ks]]),
        f"\n**MRR (document-level): {do['mrr']:.3f}**",
        "",
    ]
    repk = ks[len(ks) // 2]
    # breakdowns
    lines += ["## By difficulty (chunk-level)",
              fmt_table(["Difficulty", "n", f"Hit@{ks[0]}", f"Recall@{repk}", f"nDCG@{repk}", "MRR"],
                        [[g, v["n"], f"{v[f'hit@{ks[0]}']:.3f}", f"{v[f'recall@{repk}']:.3f}",
                          f"{v[f'ndcg@{repk}']:.3f}", f"{v['mrr']:.3f}"] for g, v in by_diff_chunk.items()]),
              "",
              "## By category (chunk-level)",
              fmt_table(["Category", "n", f"Hit@{ks[0]}", f"Recall@{repk}", f"nDCG@{repk}", "MRR"],
                        [[g, v["n"], f"{v[f'hit@{ks[0]}']:.3f}", f"{v[f'recall@{repk}']:.3f}",
                          f"{v[f'ndcg@{repk}']:.3f}", f"{v['mrr']:.3f}"] for g, v in by_cat_chunk.items()]),
              ""]
    if robustness:
        rk = robustness["rep_k"]
        lines += ["## Query-variation robustness (paraphrase stability)",
                  f"- Base questions tested: {robustness['n_base']}, paraphrases: {robustness['n_variations']}",
                  f"- Hit@{rk}: canonical **{robustness['canonical_hit']:.3f}** -> "
                  f"paraphrase **{robustness['variation_hit']:.3f}** (drop {robustness['hit_drop']:.3f})",
                  f"- Recall@{rk}: canonical **{robustness['canonical_recall']:.3f}** -> "
                  f"paraphrase **{robustness['variation_recall']:.3f}**",
                  f"- Top-{max(ks)} set stability (Jaccard canonical vs paraphrase): "
                  f"**{robustness['topk_jaccard_stability']:.3f}**",
                  ""]
    if halluc:
        lines += ["## Hallucination resistance (retrieval score gate)",
                  f"- Out-of-corpus questions: {halluc['n_hallucination']}",
                  f"- Top-1 cosine score — answerable mean **{halluc['in_corpus_top1_mean']:.3f}** "
                  f"(median {halluc['in_corpus_top1_median']:.3f}), "
                  f"out-of-corpus mean **{halluc['out_corpus_top1_mean']:.3f}** "
                  f"(median {halluc['out_corpus_top1_median']:.3f}, max {halluc['out_corpus_top1_max']:.3f})",
                  f"- Suggested score gate (5th pct of answerable): **{halluc['suggested_score_gate']:.3f}**",
                  f"- At that gate: refusal recall (out-of-corpus correctly flagged) "
                  f"**{halluc['refusal_recall_at_gate']:.3f}**, "
                  f"false-refusal rate (answerable wrongly flagged) "
                  f"**{halluc['false_refusal_rate_at_gate']:.3f}**",
                  "",
                  "_Interpretation: a similarity gate alone "
                  + ("separates" if halluc['refusal_recall_at_gate'] >= 0.5 else "only weakly separates")
                  + " out-of-corpus questions; surface-vocabulary overlap inflates "
                  "out-of-corpus scores, motivating an explicit grounding/refusal step in the generator._",
                  ""]
    if charts:
        lines += ["## Charts"] + [f"![{c}]({c})" for c in charts] + [""]
    if res["missing_gold"]:
        lines += [f"> Note: {res['missing_gold']} queries had gold chunk ids not present in the "
                  f"index (excluded from credit). Usually means the index predates a corpus change.",
                  ""]
    lines += ["## Files",
              "- `retrieval_metrics.json` — all metrics, machine-readable",
              "- `per_query_results.csv` — per-query rows for error analysis",
              ""]
    (out_dir / "eval_report.md").write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluate the UPI RAG retriever against the knowledge layer.")
    ap.add_argument("--kl", default=str(DEFAULT_KL), help="knowledge_layer folder.")
    ap.add_argument("--index-dir", default=str(DEFAULT_INDEX_DIR))
    ap.add_argument("--ks", type=int, nargs="+", default=[1, 3, 5, 10])
    ap.add_argument("--limit", type=int, default=None, help="Cap #queries (quick run).")
    ap.add_argument("--no-variations", action="store_true")
    ap.add_argument("--no-charts", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    kl = Path(args.kl)
    out_dir = kl / "eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    ks = sorted(set(args.ks))

    retr = Retriever(Path(args.index_dir))
    retr_info = {"embedding_model": retr.info.get("embedding_model", EMBEDDING_MODEL),
                 "n_vectors": retr.index.ntotal}

    rows = read_jsonl(kl / "retrieval_eval.jsonl")
    if args.limit:
        rows = rows[:args.limit]
    log(f"evaluating retrieval on {len(rows)} queries, K={ks}")
    res = evaluate_retrieval(retr, rows, ks)

    mk = res["metric_keys"]
    by_diff_chunk = grouped(res["chunk_rows"], "difficulty", mk)
    by_cat_chunk = grouped(res["chunk_rows"], "category", mk)
    by_diff_doc = grouped(res["doc_rows"], "difficulty", mk)

    robustness = None
    if not args.no_variations and (kl / "query_variations.jsonl").exists():
        var_rows = read_jsonl(kl / "query_variations.jsonl")
        if args.limit:
            var_rows = var_rows[:args.limit]
        log(f"evaluating robustness on {len(var_rows)} base questions...")
        robustness = evaluate_robustness(retr, var_rows, ks, limit=args.limit)

    halluc = None
    if (kl / "hallucination_test.jsonl").exists():
        halluc_rows = read_jsonl(kl / "hallucination_test.jsonl")
        log(f"evaluating hallucination gate on {len(halluc_rows)} out-of-corpus questions...")
        halluc = evaluate_hallucination(retr, halluc_rows, res["top1_scores"])

    charts = []
    if not args.no_charts:
        charts = make_charts(out_dir, res["chunk_overall"], res["doc_overall"], ks,
                             res["top1_scores"],
                             None if not halluc else
                             [s for s in _safe_out_scores(retr, kl)] )

    # write machine-readable metrics
    metrics = {
        "setup": retr_info,
        "n_queries": len(rows),
        "ks": ks,
        "chunk_level_overall": res["chunk_overall"],
        "doc_level_overall": res["doc_overall"],
        "by_difficulty_chunk": by_diff_chunk,
        "by_category_chunk": by_cat_chunk,
        "by_difficulty_doc": by_diff_doc,
        "robustness": robustness,
        "hallucination": halluc,
        "missing_gold": res["missing_gold"],
    }
    (out_dir / "retrieval_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    # per-query csv
    csv_rows = res["per_query_csv"]
    if csv_rows:
        with (out_dir / "per_query_results.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
            w.writeheader(); w.writerows(csv_rows)

    write_report(out_dir, ks, res, by_diff_chunk, by_cat_chunk, by_diff_doc,
                 robustness, halluc, retr_info, len(rows), charts, time.time() - t0)

    co = res["chunk_overall"]; do = res["doc_overall"]
    log("=" * 60)
    log(f"DONE in {time.time() - t0:.1f}s")
    log(f"  chunk: Recall@{ks[-1]}={co[f'recall@{ks[-1]}']:.3f}  MRR={co['mrr']:.3f}  "
        f"nDCG@{ks[-1]}={co[f'ndcg@{ks[-1]}']:.3f}")
    log(f"  doc:   Recall@{ks[-1]}={do[f'recall@{ks[-1]}']:.3f}  MRR={do['mrr']:.3f}")
    if halluc:
        log(f"  hallucination refusal-recall@gate={halluc['refusal_recall_at_gate']:.3f}")
    log(f"  -> {out_dir}")


def _safe_out_scores(retr: Retriever, kl: Path) -> list[float]:
    """Recompute out-of-corpus top-1 scores for the chart (cheap; 12 queries)."""
    p = kl / "hallucination_test.jsonl"
    if not p.exists():
        return []
    rows = read_jsonl(p)
    scores, _ = retr.search_batch([r["question"] for r in rows], 1)
    return [float(scores[j][0]) for j in range(len(rows))]


if __name__ == "__main__":
    main()
