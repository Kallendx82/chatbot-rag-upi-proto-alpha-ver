"""
Build an instruction-tuning dataset (ChatML JSONL) for fine-tuning the UPI RAG LLM.

For each question it:
  1. Retrieves real context from your FAISS index (same as production).
  2. Generates a CANDIDATE answer with a "teacher" model via Ollama.
  3. Writes a ChatML record: system + (context+question) -> answer.

Questions come from:
  - Dataset/evaluation.csv  (column `query`)
  - auto-generated simple questions seeded from chunk titles/sections

!!! IMPORTANT !!!
The generated answers are CANDIDATES. You MUST review and edit them before
training. Garbage answers -> garbage fine-tune. For a thesis, hand-curate at
least 200 examples; quality beats quantity.

USAGE
    python build_finetuning_dataset.py
    python build_finetuning_dataset.py --n-questions 300 --teacher qwen2.5:7b
    python build_finetuning_dataset.py --top-k 5 --out finetune_dataset.jsonl

Then open finetune_dataset.jsonl and curate before uploading to Colab.
"""
import argparse
import json
import os
import re
import time
from pathlib import Path

import numpy as np
import requests

# ---------------------------------------------------------------------------
# Config (matches notebooks 1-3 / backend)
# ---------------------------------------------------------------------------
DRIVE_BASE = Path(os.environ.get("RAG_UPI_BASE", r"D:/Project/RAG_UPI/Dataset"))
PIPE = DRIVE_BASE / "_pipeline"
INDEX_FILE = PIPE / "index" / "faiss.index"
META_FILE = PIPE / "index" / "chunks_meta.json"
CSV_PATH = DRIVE_BASE / "evaluation.csv"

EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
USE_E5_PREFIXES = True
OLLAMA_URL = "http://localhost:11434"

SYSTEM_PROMPT = (
    "Anda adalah asisten informasi resmi Universitas Pendidikan Indonesia "
    "(UPI). Jawab HANYA dari SUMBER bernomor di bawah. Setiap fakta wajib "
    "diikuti nomor sumber dalam kurung siku, mis. [1] atau [2]. Jangan "
    "mengarang fakta, tanggal, nama, atau angka. Jika SUMBER tidak memuat "
    "jawaban, balas: 'Maaf, informasi tersebut tidak tersedia dalam dokumen "
    "yang saya miliki saat ini.' Jawab ringkas dalam Bahasa Indonesia baku."
)


# ---------------------------------------------------------------------------
# Embedding + retrieval (lazy import so --help is fast)
# ---------------------------------------------------------------------------
_embedder = None
_index = None
_meta = None


def _load():
    global _embedder, _index, _meta
    if _index is not None:
        return
    import faiss
    from sentence_transformers import SentenceTransformer

    if not INDEX_FILE.exists():
        raise SystemExit(f"FAISS index not found at {INDEX_FILE}. Run notebook 3 first.")
    print(f"Loading FAISS index from {INDEX_FILE} ...")
    _index = faiss.read_index(str(INDEX_FILE))
    _meta = json.loads(META_FILE.read_text(encoding="utf-8"))
    print(f"  {_index.ntotal} vectors, {len(_meta)} meta rows")
    print(f"Loading embedder {EMBEDDING_MODEL} ...")
    _embedder = SentenceTransformer(EMBEDDING_MODEL)


def embed(texts, kind="passage"):
    if USE_E5_PREFIXES:
        tag = "query: " if kind == "query" else "passage: "
        texts = [tag + t for t in texts]
    return _embedder.encode(texts, convert_to_numpy=True,
                            normalize_embeddings=True).astype("float32")


def retrieve(query, top_k):
    qv = embed([query], kind="query")
    scores, idxs = _index.search(qv, top_k * 3)  # oversample for dedup
    hits, seen = [], set()
    for s, i in zip(scores[0], idxs[0]):
        if i < 0:
            continue
        c = _meta[i]
        text = (c.get("text") or "").strip()
        # dedup near-identical boilerplate (same as backend)
        fp = " ".join(text.lower().split())[:200]
        if not fp or fp in seen:
            continue
        # skip low-content (digit-soup table fragments)
        letters = sum(ch.isalpha() for ch in text)
        if len(text) < 60 or (letters / max(len(text), 1)) < 0.35:
            continue
        seen.add(fp)
        hits.append({**c, "score": float(s)})
        if len(hits) >= top_k:
            break
    return hits


# ---------------------------------------------------------------------------
# Teacher generation via Ollama
# ---------------------------------------------------------------------------
def teacher_answer(question, hits, model, temperature=0.2):
    context = "\n\n".join(
        f"[{i+1}] {h.get('title','Dokumen')} (hal. {h.get('page')})\n{h['text']}"
        for i, h in enumerate(hits)
    )
    prompt = (
        f"{SYSTEM_PROMPT}\n\n=== SUMBER ===\n{context}\n\n"
        f"=== PERTANYAAN ===\n{question}\n\n"
        f"=== JAWABAN (sertakan [1], [2] dst) ===\n"
    )
    r = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False,
              "options": {"temperature": temperature, "num_ctx": 8192,
                          "num_predict": 512}},
        timeout=240,
    )
    r.raise_for_status()
    return (r.json().get("response") or "").strip(), context


# ---------------------------------------------------------------------------
# Question sourcing
# ---------------------------------------------------------------------------
def questions_from_csv():
    qs = []
    if CSV_PATH.exists():
        import csv as _csv
        with CSV_PATH.open(encoding="utf-8", errors="replace") as f:
            for row in _csv.DictReader(f):
                q = (row.get("query") or row.get("question") or "").strip()
                if q:
                    qs.append(q)
    return qs


# Simple templates to auto-generate more questions from chunk sections/titles.
_QUESTION_TEMPLATES = [
    "Apa isi {topic}?",
    "Jelaskan tentang {topic}.",
    "Bagaimana ketentuan {topic}?",
    "Apa saja yang diatur dalam {topic}?",
]


def questions_from_chunks(n):
    """Seed extra questions from distinctive section headings in the corpus."""
    _load()
    seen, topics = set(), []
    for c in _meta:
        sec = (c.get("section") or "").strip()
        if not sec or len(sec) < 6 or len(sec) > 60:
            continue
        key = sec.lower()
        if key in seen:
            continue
        # skip pure-number / code-like sections
        if not re.search(r"[A-Za-z]{4,}", sec):
            continue
        seen.add(key)
        topics.append(sec)
        if len(topics) >= n:
            break
    qs = []
    for i, t in enumerate(topics):
        tmpl = _QUESTION_TEMPLATES[i % len(_QUESTION_TEMPLATES)]
        qs.append(tmpl.format(topic=t.lower()))
    return qs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-questions", type=int, default=200,
                    help="Total questions to build examples for")
    ap.add_argument("--teacher", default="qwen2.5:7b",
                    help="Ollama model used to draft candidate answers")
    ap.add_argument("--top-k", type=int, default=5,
                    help="Chunks retrieved per question")
    ap.add_argument("--out", default="finetune_dataset.jsonl")
    ap.add_argument("--skip-refusals", action="store_true",
                    help="Drop examples where the teacher refused (no usable answer)")
    args = ap.parse_args()

    _load()

    # Gather questions: CSV first, then auto-generated to reach n.
    csv_qs = questions_from_csv()
    print(f"Questions from CSV: {len(csv_qs)}")
    need = max(0, args.n_questions - len(csv_qs))
    auto_qs = questions_from_chunks(need) if need else []
    print(f"Auto-generated questions: {len(auto_qs)}")
    all_qs = (csv_qs + auto_qs)[: args.n_questions]
    print(f"Total questions to process: {len(all_qs)}\n")

    out_path = Path(args.out)
    n_written, n_refusal = 0, 0
    with out_path.open("w", encoding="utf-8") as fout:
        for i, q in enumerate(all_qs, 1):
            try:
                hits = retrieve(q, args.top_k)
                if not hits:
                    print(f"[{i}/{len(all_qs)}] (no context) {q[:60]}")
                    continue
                ans, context = teacher_answer(q, hits, args.teacher)
                is_refusal = "tidak tersedia" in ans.lower()
                if is_refusal:
                    n_refusal += 1
                    if args.skip_refusals:
                        print(f"[{i}/{len(all_qs)}] (refusal skipped) {q[:60]}")
                        continue
                record = {"messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",
                     "content": f"SUMBER:\n{context}\n\nPERTANYAAN: {q}"},
                    {"role": "assistant", "content": ans},
                ]}
                fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                n_written += 1
                flag = " [REFUSAL]" if is_refusal else ""
                print(f"[{i}/{len(all_qs)}] ok{flag}  {q[:60]}")
            except requests.RequestException as e:
                print(f"[{i}/{len(all_qs)}] OLLAMA ERROR ({e}); is '{args.teacher}' pulled?")
                time.sleep(1)
            except Exception as e:  # noqa: BLE001
                print(f"[{i}/{len(all_qs)}] error: {e}")

    print(f"\nWrote {n_written} examples to {out_path.resolve()}")
    print(f"  (of which {n_refusal} were teacher refusals)")
    print("\nNEXT STEPS:")
    print("  1. OPEN the JSONL and CURATE — fix/improve the assistant answers.")
    print("     Quality of these answers = quality of your fine-tune.")
    print("  2. Keep a healthy mix of normal answers AND polite refusals so the")
    print("     model learns when to say 'tidak tersedia'.")
    print("  3. Upload to Google Colab and follow PANDUAN_FINE_TUNING.md.")


if __name__ == "__main__":
    main()
