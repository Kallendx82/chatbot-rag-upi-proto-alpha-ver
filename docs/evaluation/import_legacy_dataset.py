"""One-time/reusable importer: convert the legacy QA dataset from the
previous evaluation project (D:/Project/RAG_UPI/knowledge_layer) into the
dataset.json schema used by run_eval.py.

The legacy dataset has chunk-level ground truth (expected_chunk_ids), which
is more precise than the doc-title matching used by the hand-written
10-question dataset.json. This script resolves each legacy chunk_id against
the CURRENT backend index (chunks_meta.json) so stale references (docs that
were re-ingested, removed, or never in this repo's corpus) are dropped
rather than silently producing an unverifiable ground truth.

Usage:
    python import_legacy_dataset.py \
        --expected-answers "D:/Project/RAG_UPI/knowledge_layer/expected_answers.jsonl" \
        --retrieval-eval "D:/Project/RAG_UPI/knowledge_layer/retrieval_eval.jsonl" \
        --chunks-meta "D:/Project/chatbot-rag-upi-alpha/backend/app/data/chunks_meta.json" \
        --output dataset.json

Unresolvable questions (chunk_id not found in the current index - e.g.
synthetic/reference rows added later that were never actually ingested) are
skipped and reported, not silently dropped without a trace.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Import legacy RAG_UPI QA dataset into dataset.json schema")
    parser.add_argument("--expected-answers", required=True, help="Path to expected_answers.jsonl")
    parser.add_argument("--retrieval-eval", required=True, help="Path to retrieval_eval.jsonl")
    parser.add_argument("--chunks-meta", required=True, help="Path to the CURRENT backend chunks_meta.json")
    parser.add_argument("--output", default="dataset.json", help="Output path")
    parser.add_argument("--keep-unresolved", action="store_true",
                         help="Keep questions whose chunks are not found in the current index "
                              "(ground truth kept, but expected_chunk_ids/expected_doc_title will be empty)")
    args = parser.parse_args()

    chunks = json.load(open(args.chunks_meta, encoding="utf-8"))
    chunk_by_id = {c["chunk_id"]: c for c in chunks}

    expected_answers = {d["question_id"]: d for d in load_jsonl(Path(args.expected_answers))}
    retrieval_eval = {d["question_id"]: d for d in load_jsonl(Path(args.retrieval_eval))}

    out: list[dict] = []
    n_resolved = 0
    n_unresolved = 0
    unresolved_ids: list[str] = []

    for qid, ea in expected_answers.items():
        re_entry = retrieval_eval.get(qid, {})
        chunk_ids = ea.get("supporting_chunks", []) or re_entry.get("expected_chunk_ids", [])
        doc_ids = ea.get("supporting_documents", []) or re_entry.get("expected_doc_ids", [])

        resolved_chunks = [cid for cid in chunk_ids if cid in chunk_by_id]
        fully_resolved = len(resolved_chunks) == len(chunk_ids) and len(chunk_ids) > 0

        if not fully_resolved:
            n_unresolved += 1
            unresolved_ids.append(qid)
            if not args.keep_unresolved:
                continue
        else:
            n_resolved += 1

        # Doc title + keywords derived from the resolved chunks in the
        # CURRENT index, not copied from the legacy dataset, so they stay
        # accurate even if titles/keywords changed since the legacy run.
        titles = []
        keywords: Counter = Counter()
        for cid in resolved_chunks:
            c = chunk_by_id[cid]
            if c.get("title") and c["title"] not in titles:
                titles.append(c["title"])
            for kw in (c.get("keywords") or [])[:4]:
                keywords[kw] += 1

        out.append({
            "id": qid,
            "question": ea["question"],
            "expected_doc_title": titles[0] if len(titles) == 1 else "",
            "expected_doc_titles": titles if len(titles) > 1 else None,
            "expected_chunk_ids": resolved_chunks or None,
            "expected_keywords": [kw for kw, _ in keywords.most_common(5)],
            "ground_truth": ea.get("expected_answer_long") or ea.get("expected_answer_short", ""),
            "category": re_entry.get("category", ""),
            "difficulty": re_entry.get("difficulty", ""),
            "source": "legacy_RAG_UPI",
        })

    # Drop the None placeholders (JSON has no "omit if None" - clean up for a tidy file)
    for item in out:
        if item["expected_doc_titles"] is None:
            del item["expected_doc_titles"]
        if item["expected_chunk_ids"] is None:
            del item["expected_chunk_ids"]

    output_path = Path(args.output)
    output_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Imported {len(out)} questions -> {output_path}")
    print(f"  Fully resolved against current index: {n_resolved}")
    print(f"  Unresolved (chunk not in current index): {n_unresolved}"
          f"{' (kept, unverified)' if args.keep_unresolved else ' (dropped)'}")
    if unresolved_ids:
        print(f"  Sample unresolved IDs: {unresolved_ids[:10]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
