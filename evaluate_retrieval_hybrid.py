"""evaluate_retrieval_hybrid.py
=============================================================================
Compare retrieval strategies on the UPI eval set to quantify the gain from
HYBRID retrieval (BM25 + dense e5, fused with Reciprocal Rank Fusion).

Strategies compared (chunk-level + doc-level Recall@K / Hit@K / MRR / nDCG):
  - dense   : intfloat/multilingual-e5-base + FAISS (the current chatbot)
  - bm25    : keyword retrieval over chunk text (rank_bm25)
  - hybrid  : RRF fusion of dense + bm25  <-- the proposed improvement

No model downloads, fully offline. Runs in a couple of minutes (no LLM).

USAGE
    python evaluate_retrieval_hybrid.py
    python evaluate_retrieval_hybrid.py --ks 1 3 5 10 --candidates 50 --limit 200

Output: knowledge_layer/eval/retrieval_hybrid/{report.md,metrics.json}
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
import json
import math
import re
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

RAG_ROOT = Path(r"D:\Project\RAG_UPI")
DEFAULT_KL = RAG_ROOT / "knowledge_layer"
DEFAULT_INDEX_DIR = RAG_ROOT / "Dataset" / "_pipeline" / "index"
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def log(m: str) -> None:
    print(f"[hybrid] {m}", flush=True)


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


# --------------------------------------------------------------------------- #
# Metrics (binary relevance)
# --------------------------------------------------------------------------- #
def per_query(retrieved: list[str], expected: set[str], ks: list[int]) -> dict:
    out: dict[str, float] = {}
    n_rel = len(expected)
    first = next((i for i, r in enumerate(retrieved, 1) if r in expected), 0)
    out["mrr"] = 1.0 / first if first else 0.0
    for k in ks:
        top = retrieved[:k]
        hit = sum(1 for r in top if r in expected)
        out[f"hit@{k}"] = 1.0 if hit else 0.0
        out[f"recall@{k}"] = hit / n_rel if n_rel else 0.0
        dcg = sum(1.0 / math.log2(i + 1) for i, r in enumerate(top, 1) if r in expected)
        idcg = sum(1.0 / math.log2(i + 1) for i in range(1, min(n_rel, k) + 1))
        out[f"ndcg@{k}"] = dcg / idcg if idcg else 0.0
    return out


def mean_metrics(rows: list[dict], keys: list[str]) -> dict:
    if not rows:
        return {k: 0.0 for k in keys}
    return {k: round(sum(r[k] for r in rows) / len(rows), 4) for k in keys}


def dedup(seq: list[str]) -> list[str]:
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x); out.append(x)
    return out


def rrf_fuse(rankings: list[list[int]], k0: int = 60) -> list[int]:
    """Reciprocal Rank Fusion of several ranked row-id lists."""
    score: dict[int, float] = defaultdict(float)
    for ranking in rankings:
        for rank, row in enumerate(ranking, 1):
            score[row] += 1.0 / (k0 + rank)
    return [row for row, _ in sorted(score.items(), key=lambda x: x[1], reverse=True)]


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description="Compare dense / bm25 / hybrid retrieval.")
    ap.add_argument("--kl", default=str(DEFAULT_KL))
    ap.add_argument("--index-dir", default=str(DEFAULT_INDEX_DIR))
    ap.add_argument("--ks", type=int, nargs="+", default=[1, 3, 5, 10])
    ap.add_argument("--candidates", type=int, default=50,
                    help="Candidate pool per retriever before fusion / truncation.")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    import faiss
    from sentence_transformers import SentenceTransformer
    from rank_bm25 import BM25Okapi

    t0 = time.time()
    kl = Path(args.kl)
    out_dir = kl / "eval" / "retrieval_hybrid"
    out_dir.mkdir(parents=True, exist_ok=True)
    ks = sorted(set(args.ks))
    N = args.candidates

    idx_dir = Path(args.index_dir)
    info = json.loads((idx_dir / "index_info.json").read_text(encoding="utf-8"))
    use_prefix = bool(info.get("use_e5_prefixes", True))
    log("loading FAISS + meta ...")
    index = faiss.read_index(str(idx_dir / "faiss.index"))
    meta = json.loads((idx_dir / "chunks_meta.json").read_text(encoding="utf-8"))
    chunk_ids = [m.get("chunk_id", "") for m in meta]
    doc_ids = [m.get("doc_id", "") for m in meta]

    log(f"loading embedder {EMBEDDING_MODEL} (CPU) ...")
    embedder = SentenceTransformer(EMBEDDING_MODEL, device="cpu")

    log(f"building BM25 over {len(meta):,} chunks (tokenizing)...")
    bm25 = BM25Okapi([tokenize(m.get("text", "")) for m in meta])
    log(f"BM25 ready in {time.time() - t0:.0f}s")

    rows = [json.loads(l) for l in (kl / "retrieval_eval.jsonl").open(encoding="utf-8") if l.strip()]
    if args.limit:
        rows = rows[: args.limit]
    log(f"evaluating {len(rows)} queries (candidates={N}, K={ks})")

    keys = ["mrr"] + [f"{m}@{k}" for k in ks for m in ("hit", "recall", "ndcg")]
    agg = {s: {"chunk": [], "doc": []} for s in ("dense", "bm25", "hybrid")}

    for qi, r in enumerate(rows, 1):
        query = r["query"]
        exp_c = set(r.get("expected_chunk_ids") or [])
        exp_d = set(r.get("expected_doc_ids") or [])

        # dense candidates
        qv = embedder.encode([("query: " + query) if use_prefix else query],
                             convert_to_numpy=True, normalize_embeddings=True).astype("float32")
        _, didx = index.search(qv, N)
        dense_rows = [int(i) for i in didx[0] if i >= 0]

        # bm25 candidates
        scores = bm25.get_scores(tokenize(query))
        bm25_rows = [int(i) for i in np.argsort(scores)[::-1][:N]]

        # hybrid via RRF
        hybrid_rows = rrf_fuse([dense_rows, bm25_rows])

        for name, ranked in (("dense", dense_rows), ("bm25", bm25_rows), ("hybrid", hybrid_rows)):
            c_ids = [chunk_ids[i] for i in ranked]
            d_ids = dedup([doc_ids[i] for i in ranked])
            agg[name]["chunk"].append(per_query(c_ids, exp_c, ks))
            agg[name]["doc"].append(per_query(d_ids, exp_d, ks))
        if qi % 100 == 0:
            log(f"  ...{qi}/{len(rows)}")

    results = {s: {"chunk": mean_metrics(agg[s]["chunk"], keys),
                   "doc": mean_metrics(agg[s]["doc"], keys)} for s in agg}

    # ---- report ----
    def row(strat, level, k):
        return results[strat][level]
    lines = [
        "# UPI RAG — Retrieval Strategy Comparison (Dense vs BM25 vs Hybrid)",
        "",
        f"_{len(rows)} queries · e5-base · candidates={N} · RRF fusion · {time.time()-t0:.0f}s_",
        "",
        "## Chunk-level",
        "| Strategy | " + " | ".join(f"R@{k}" for k in ks) + " | MRR |",
        "| --- |" + " --- |" * (len(ks) + 1),
    ]
    for s in ("dense", "bm25", "hybrid"):
        c = results[s]["chunk"]
        lines.append(f"| {s} | " + " | ".join(f"{c[f'recall@{k}']:.3f}" for k in ks) + f" | {c['mrr']:.3f} |")
    lines += ["", "## Document-level",
              "| Strategy | " + " | ".join(f"R@{k}" for k in ks) + " | MRR |",
              "| --- |" + " --- |" * (len(ks) + 1)]
    for s in ("dense", "bm25", "hybrid"):
        d = results[s]["doc"]
        lines.append(f"| {s} | " + " | ".join(f"{d[f'recall@{k}']:.3f}" for k in ks) + f" | {d['mrr']:.3f} |")

    # improvement summary (hybrid vs dense)
    repk = ks[len(ks) // 2]
    dc, hc = results["dense"]["chunk"], results["hybrid"]["chunk"]
    dd, hd = results["dense"]["doc"], results["hybrid"]["doc"]
    def gain(a, b): return f"{(b-a):+.3f} ({(b-a)/a*100:+.0f}%)" if a else f"{b:+.3f}"
    lines += ["", "## Peningkatan hybrid vs dense (baseline)",
              f"- Chunk Recall@{repk}: {dc[f'recall@{repk}']:.3f} → **{hc[f'recall@{repk}']:.3f}**  ({gain(dc[f'recall@{repk}'], hc[f'recall@{repk}'])})",
              f"- Chunk MRR: {dc['mrr']:.3f} → **{hc['mrr']:.3f}**  ({gain(dc['mrr'], hc['mrr'])})",
              f"- Doc Recall@{repk}: {dd[f'recall@{repk}']:.3f} → **{hd[f'recall@{repk}']:.3f}**  ({gain(dd[f'recall@{repk}'], hd[f'recall@{repk}'])})",
              f"- Doc MRR: {dd['mrr']:.3f} → **{hd['mrr']:.3f}**  ({gain(dd['mrr'], hd['mrr'])})",
              "", "_Hybrid = Reciprocal Rank Fusion(dense, bm25). Gunakan tabel ini untuk bab "
              "'perbaikan retrieval' di skripsi (before/after)._"]
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "metrics.json").write_text(
        json.dumps({"n_queries": len(rows), "candidates": N, "ks": ks, "results": results},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    log("=" * 60)
    for s in ("dense", "bm25", "hybrid"):
        c = results[s]["chunk"]; d = results[s]["doc"]
        log(f"  {s:7s} | chunk R@{repk}={c[f'recall@{repk}']:.3f} MRR={c['mrr']:.3f} | "
            f"doc R@{repk}={d[f'recall@{repk}']:.3f} MRR={d['mrr']:.3f}")
    log(f"DONE in {time.time()-t0:.0f}s -> {out_dir}")


if __name__ == "__main__":
    main()
