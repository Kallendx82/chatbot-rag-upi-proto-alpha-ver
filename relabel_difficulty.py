"""relabel_difficulty.py
=============================================================================
Re-label the `difficulty` field of the eval Q&A set by QUESTION TYPE, replacing
the model's (skewed) labels. Scheme requested by the user:

  hard   (Sulit)  : reasoning / explanation questions
                    -> mengapa, kenapa, bagaimana, jelaskan, tujuan, fungsi, ...
  medium (Sedang) : numeric / date questions
                    -> berapa, kapan, tanggal, jumlah, biaya, tahun, ...
  easy   (Mudah)  : everything else = simple factual questions (siapa/apa/di mana/
                    apakah) that are light and need little retrieval reasoning.

Priority: hard > medium > easy (a question matching several buckets takes the
highest). Updates the difficulty in every file that carries it:
  - knowledge_layer/_rebuild/_work/*.jsonl        (export source)
  - knowledge_layer/_rebuild/retrieval_eval.jsonl (rebuild copy)
  - knowledge_layer/retrieval_eval.jsonl          (LIVE, used by evaluate scripts)

USAGE
    python relabel_difficulty.py            # apply
    python relabel_difficulty.py --dry-run  # just print the resulting distribution
=============================================================================
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

RAG_ROOT = Path(r"D:\Project\RAG_UPI")
KL = RAG_ROOT / "knowledge_layer"

# reasoning / explanation -> hard
_HARD = [
    "mengapa", "kenapa", "bagaimana", "jelaskan", "uraikan", "gambarkan",
    "deskripsikan", "apa tujuan", "tujuan dari", "tujuan utama", "apa fungsi",
    "fungsi dari", "apa manfaat", "manfaat dari", "apa peran", "peran dari",
    "apa alasan", "alasan ", "apa dampak", "dampak dari", "apa maksud",
    "maksud dari", "apa perbedaan", "perbedaan antara", "apa pengaruh",
    "pengaruh dari", "apa hubungan", "hubungan antara", "apa pentingnya",
    "mengapakah", "apa yang dimaksud", "apa saja tujuan", "apa saja fungsi",
    "apa saja manfaat", "apa saja peran",
]

# numeric / date -> medium
_MEDIUM = [
    "berapa", "berapakah", "kapan", "tanggal", "jumlah", "nominal", "biaya",
    "tarif", "harga", "persen", "persentase", "pukul", "jam berapa",
    "tahun berapa", "kuota", "besaran", "durasi", "berapa lama", "berapa banyak",
    "berapa kali",
]


def _compile(words: list[str]) -> re.Pattern:
    # word-boundary alternation so "jelaskan" does NOT match "menjelaskan",
    # "gambarkan" not "menggambarkan", etc. (descriptive verbs are not questions
    # asking to explain).
    return re.compile(r"\b(?:" + "|".join(re.escape(w.strip()) for w in words) + r")\b")


_HARD_RE = _compile(_HARD)
_MEDIUM_RE = _compile(_MEDIUM)


def classify(question: str) -> str:
    q = (question or "").lower()
    if _HARD_RE.search(q):
        return "hard"
    if _MEDIUM_RE.search(q):
        return "medium"
    return "easy"


def relabel_file(path: Path, dry: bool) -> Counter:
    if not path.exists():
        return Counter()
    rows = [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]
    dist = Counter()
    for r in rows:
        q = r.get("question") or r.get("query") or ""
        d = classify(q)
        r["difficulty"] = d
        dist[d] += 1
    if not dry:
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return dist


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    targets = list((KL / "_rebuild" / "_work").glob("*.jsonl"))
    targets += [KL / "_rebuild" / "retrieval_eval.jsonl", KL / "retrieval_eval.jsonl"]

    grand = Counter()
    for p in targets:
        dist = relabel_file(p, args.dry_run)
        if dist:
            # only count the live retrieval_eval once for the headline number
            if p == KL / "retrieval_eval.jsonl":
                grand = dist
            print(f"  {p.relative_to(RAG_ROOT)}: "
                  + ", ".join(f"{k}={v}" for k, v in sorted(dist.items())))

    print("\n=== FINAL DISTRIBUTION (live retrieval_eval.jsonl) ===")
    total = sum(grand.values())
    for lvl, label in [("easy", "Mudah"), ("medium", "Sedang"), ("hard", "Sulit")]:
        n = grand.get(lvl, 0)
        pct = 100 * n / total if total else 0
        print(f"  {label:7s} ({lvl:6s}): {n:5d}  ({pct:.1f}%)")
    print(f"  {'TOTAL':7s}          : {total:5d}")
    if args.dry_run:
        print("\n(dry-run: no files written)")


if __name__ == "__main__":
    main()
