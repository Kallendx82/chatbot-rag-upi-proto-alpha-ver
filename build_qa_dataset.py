"""build_qa_dataset.py
=============================================================================
Rebuild the evaluation Q&A set for the UPI RAG chatbot, grounded in the
already-chunked corpus (Dataset/_pipeline/index/chunks_meta.json).

Produces a drop-in replacement for the three files consumed by
evaluate_ragas.py and evaluate_retrieval_hybrid.py:

  - expected_answers.jsonl      (question_id, expected_answer_short/long, ...)
  - retrieval_eval.jsonl        (question_id, query, expected_chunk_ids, ...)
  - simulation_questions.jsonl  (question_id, persona, question, ...)

Target distribution (total 1,880):
  Direktorat Pendidikan .......... 300
  PMB ............................ 350
  PPID ........................... 200
  LPPM ........................... 300
  UPI Cibiru ..................... 200
  UPI Purwakarta ................. 100
  UPI Sumedang ................... 100
  UPI Serang ..................... 100
  UPI Tasikmalaya ................ 100
  Informasi Umum UPI + Kalender .. 130

Generation engine: local Ollama (default qwen2.5:7b-instruct). Free, keeps the
Claude judge budget intact. Resumable: each theme is checkpointed under
<out>/_work/<code>.jsonl, so a crash/restart continues where it left off.

USAGE
    python build_qa_dataset.py                      # full run -> knowledge_layer/_rebuild
    python build_qa_dataset.py --smoke 2            # 2 questions per theme (validate)
    python build_qa_dataset.py --model llama3.1:8b  # different Ollama model
    python build_qa_dataset.py --out D:/.../_rebuild
=============================================================================
"""
from __future__ import annotations

import argparse
import json
import random
import re
import time
import urllib.request
from pathlib import Path

import ijson

RAG_ROOT = Path(r"D:\Project\RAG_UPI")
META = RAG_ROOT / "Dataset" / "_pipeline" / "index" / "chunks_meta.json"
DEFAULT_OUT = RAG_ROOT / "knowledge_layer" / "_rebuild"
OLLAMA_BASE_URL = "http://localhost:11434"
PERSONAS = ["calon mahasiswa", "mahasiswa", "orang tua/wali", "masyarakat umum",
            "peneliti", "dosen"]


def log(m: str) -> None:
    print(f"[build-qa] {m}", flush=True)


# --------------------------------------------------------------------------- #
# Theme -> (output category label, question_id prefix, target, chunk matcher)
# The matcher receives (category, source_lower) and returns True if the chunk
# belongs to this theme.
# --------------------------------------------------------------------------- #
def _pmb(cat, src):
    return cat in {"Dataset_PMB_UPI", "PMB UPi", "PMB UPI"}


def _lppm(cat, src):
    return cat == "Dataset_root" and "lppm" in src


def _umum(cat, src):
    if cat in {"Kalender Akademik", "Referensi UPI"}:
        return True
    if cat == "Dataset_root" and "lppm" not in src and "pmb" not in src:
        return True
    return False


THEMES = [
    ("Direktorat Pendidikan",                   "DITPEND", 300,
     lambda c, s: c == "Dit-Pendidikan-UPI"),
    ("Penerimaan Mahasiswa Baru (PMB)",         "PMB",     350, _pmb),
    ("Informasi Publik (PPID)",                 "PPID",    200,
     lambda c, s: c == "PPID"),
    ("LPPM",                                    "LPPM",    300, _lppm),
    ("UPI Kampus Cibiru",                       "CIBIRU",  200,
     lambda c, s: c == "UPI_Cibiru_Web"),
    ("UPI Kampus Purwakarta",                   "PWK",     100,
     lambda c, s: c == "UPI_Purwakarta_Web"),
    ("UPI Kampus Sumedang",                     "SMD",     100,
     lambda c, s: c == "UPI_Sumedang_Web"),
    ("UPI Kampus Serang",                       "SRG",     100,
     lambda c, s: c == "UPI_Serang_Web"),
    ("UPI Kampus Tasikmalaya",                  "TSM",     100,
     lambda c, s: c == "UPI_Tasikmalaya_Web"),
    ("Informasi Umum UPI & Kalender Akademik",  "UMUM",    130, _umum),
]


# --------------------------------------------------------------------------- #
# Chunk quality filter: skip forms/templates/number-tables that yield bad Qs.
# --------------------------------------------------------------------------- #
# Strong markers: a single hit means the chunk is a form/template -> skip.
_BAD_STRONG = [
    "yang bertanda tangan", "materai", "pas foto", "coret yang tidak",
    "surat pernyataan", "menyanggupi pembiayaan", "( ................",
]
# Weak markers: need two hits to reject.
_BAD_WEAK = [
    "..........", "nama lengkap :", "nim :", "tanda tangan", "nomor telepon/hp",
    "nama :", "alamat :",
]


def good_chunk(text: str) -> bool:
    t = (text or "").strip()
    if len(t) < 220 or len(t) > 2600:
        return False
    letters = sum(c.isalpha() for c in t)
    if letters / max(len(t), 1) < 0.55:
        return False
    low = t.lower()
    if any(m in low for m in _BAD_STRONG):
        return False
    if sum(m in low for m in _BAD_WEAK) >= 2:
        return False
    # need at least a few sentences / real words
    if len(low.split()) < 40:
        return False
    return True


# --------------------------------------------------------------------------- #
# Pool building (single streaming pass over the big meta file)
# --------------------------------------------------------------------------- #
def build_pools(target_codes: set[str]) -> dict[str, list[dict]]:
    pools: dict[str, list[dict]] = {code: [] for _, code, _, _ in THEMES}
    matchers = [(code, m) for _, code, _, m in THEMES]
    seen = 0
    kept = 0
    with open(META, "rb") as f:
        for obj in ijson.items(f, "item"):
            seen += 1
            cat = obj.get("category") or ""
            src = (obj.get("source") or "").replace("\\", "/").lower()
            text = obj.get("text") or ""
            if not good_chunk(text):
                continue
            for code, m in matchers:
                if code not in target_codes:
                    continue
                if m(cat, src):
                    pools[code].append({
                        "chunk_id": obj.get("chunk_id"),
                        "doc_id": obj.get("doc_id"),
                        "title": obj.get("title"),
                        "text": text.strip(),
                        "keywords": obj.get("keywords") or [],
                    })
                    kept += 1
                    break
            if seen % 10000 == 0:
                log(f"  scanned {seen} chunks, kept {kept} so far ...")
    log(f"scan complete: {seen} chunks seen, {kept} usable chunks pooled")
    for _, code, _, _ in THEMES:
        if code in target_codes:
            log(f"  pool[{code}] = {len(pools[code])} usable chunks")
    return pools


def spread_sample(pool: list[dict], n_needed: int, rng: random.Random) -> list[dict]:
    """Pick chunks spread across distinct documents first, then fill."""
    by_doc: dict[str, list[dict]] = {}
    for c in pool:
        by_doc.setdefault(c["doc_id"], []).append(c)
    docs = list(by_doc.keys())
    rng.shuffle(docs)
    for d in docs:
        rng.shuffle(by_doc[d])
    ordered: list[dict] = []
    # round-robin across docs so coverage is broad
    idx = 0
    while len(ordered) < len(pool):
        progressed = False
        for d in docs:
            if idx < len(by_doc[d]):
                ordered.append(by_doc[d][idx])
                progressed = True
        idx += 1
        if not progressed:
            break
    # oversample generously so we can skip chunks that fail generation
    return ordered[: max(n_needed * 3, n_needed + 30)]


# --------------------------------------------------------------------------- #
# Ollama generation
# --------------------------------------------------------------------------- #
GEN_PROMPT = """Anda adalah pembuat soal evaluasi untuk chatbot informasi resmi \
Universitas Pendidikan Indonesia (UPI).

Berdasarkan KONTEKS di bawah, buat SATU pertanyaan faktual dalam Bahasa Indonesia \
yang jawabannya tersedia SECARA EKSPLISIT di dalam konteks.

Aturan wajib:
- Pertanyaan harus spesifik, natural, dan bisa berdiri sendiri (jangan menyebut \
"berdasarkan teks di atas" atau "menurut dokumen").
- Jangan membuat pertanyaan yang jawabannya tidak ada di konteks.
- "answer_short": satu kalimat padat yang menjawab langsung.
- "answer_long": 2-4 kalimat, tetap HANYA berdasarkan konteks, tanpa menambah fakta luar.
- "difficulty": "easy" (fakta langsung), "medium" (perlu sedikit penggabungan), \
atau "hard" (perlu beberapa detail dari konteks).

KONTEKS:
\"\"\"
{context}
\"\"\"

Balas HANYA dengan satu objek JSON valid, tanpa teks lain, tanpa ```:
{{"question": "...", "answer_short": "...", "answer_long": "...", "difficulty": "easy"}}"""


def ollama_generate(model: str, prompt: str, temperature: float,
                    num_ctx: int, num_predict: int, timeout: int) -> str:
    payload = {
        "model": model, "prompt": prompt, "stream": False,
        "options": {"temperature": temperature, "num_predict": num_predict,
                    "num_ctx": num_ctx},
    }
    data = json.dumps(payload).encode("utf-8")
    last = None
    for attempt in range(5):
        try:
            req = urllib.request.Request(
                f"{OLLAMA_BASE_URL}/api/generate", data=data,
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return (json.loads(r.read().decode("utf-8")).get("response") or "").strip()
        except Exception as e:  # noqa: BLE001
            last = e
            log(f"  ! Ollama gagal (attempt {attempt+1}/5): {e} -> retry")
            time.sleep(min(20, 5 * (attempt + 1)))
    log(f"  !! Ollama gagal permanen: {last}")
    return ""


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)

# Referential phrases: a standalone eval question must not point back at the
# hidden context ("tersebut", "di atas", ...) because the retriever has no referent.
_REFERENTIAL = [
    "tersebut", "di atas", "diatas", "berikut ini", "dalam daftar",
    "dalam pernyataan", "pada tabel", "pada teks", "dalam teks",
    "dalam konteks", "menurut dokumen", "berdasarkan teks", "paragraf",
    "kutipan", "bacaan di", "dalam dokumen ini", "pada bagian ini",
]


def parse_qa(raw: str) -> dict | None:
    if not raw:
        return None
    m = _JSON_RE.search(raw)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except Exception:  # noqa: BLE001
        return None
    q = (d.get("question") or "").strip()
    a_s = (d.get("answer_short") or "").strip()
    a_l = (d.get("answer_long") or "").strip() or a_s
    if len(q) < 12 or "?" not in q or len(a_s) < 3:
        return None
    # reject mojibake (bad decode) leaking from the source chunk
    if "�" in q or "�" in a_s:
        return None
    ql = q.lower()
    if any(p in ql for p in _REFERENTIAL):
        return None
    # reject answers that admit the fact is not in the context
    al = (a_s + " " + a_l).lower()
    if any(p in al for p in ("tidak disebutkan", "tidak ada informasi",
                             "tidak dijelaskan", "tidak tercantum",
                             "tidak disebut", "tidak diketahui",
                             "tidak dinyatakan")):
        return None
    diff = (d.get("difficulty") or "medium").strip().lower()
    if diff not in {"easy", "medium", "hard"}:
        diff = "medium"
    return {"question": q, "answer_short": a_s, "answer_long": a_l, "difficulty": diff}


# --------------------------------------------------------------------------- #
# Per-theme generation with checkpointing
# --------------------------------------------------------------------------- #
def generate_theme(cat_label: str, code: str, target: int, pool: list[dict],
                   model: str, work_dir: Path, rng: random.Random,
                   temperature: float, timeout: int) -> list[dict]:
    ckpt = work_dir / f"{code}.jsonl"
    done: list[dict] = []
    seen_q: set[str] = set()
    if ckpt.exists():
        for line in ckpt.open(encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                done.append(r)
                seen_q.add(r["question"].strip().lower())
        if len(done) >= target:
            log(f"[{code}] checkpoint already has {len(done)}/{target} -> skip")
            return done[:target]
        log(f"[{code}] resuming from checkpoint: {len(done)}/{target}")

    candidates = spread_sample(pool, target, rng)
    ci = 0
    fout = ckpt.open("a", encoding="utf-8")
    t0 = time.time()
    while len(done) < target and ci < len(candidates):
        chunk = candidates[ci]
        ci += 1
        prompt = GEN_PROMPT.format(context=chunk["text"][:2400])
        raw = ollama_generate(model, prompt, temperature=temperature,
                              num_ctx=4096, num_predict=400, timeout=timeout)
        qa = parse_qa(raw)
        if not qa:
            continue
        key = qa["question"].strip().lower()
        if key in seen_q:
            continue
        seen_q.add(key)
        idx = len(done) + 1
        rec = {
            "question_id": f"{code}_{idx:04d}",
            "category": cat_label,
            "topic_id": chunk["doc_id"],
            "persona": rng.choice(PERSONAS),
            "question": qa["question"],
            "answer_short": qa["answer_short"],
            "answer_long": qa["answer_long"],
            "difficulty": qa["difficulty"],
            "supporting_chunks": [chunk["chunk_id"]],
            "supporting_documents": [chunk["doc_id"]],
        }
        done.append(rec)
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fout.flush()
        if len(done) % 20 == 0 or len(done) == target:
            rate = (time.time() - t0) / max(len(done), 1)
            eta = rate * (target - len(done))
            log(f"[{code}] {len(done)}/{target}  (~{rate:.1f}s/q, ETA {eta/60:.1f}m)")
    fout.close()
    if len(done) < target:
        log(f"[{code}] WARNING: only {len(done)}/{target} generated "
            f"(pool exhausted: {len(candidates)} candidates tried)")
    return done[:target]


# --------------------------------------------------------------------------- #
# Write the three drop-in files
# --------------------------------------------------------------------------- #
def write_outputs(all_rows: list[dict], out: Path) -> None:
    exp = out / "expected_answers.jsonl"
    ret = out / "retrieval_eval.jsonl"
    sim = out / "simulation_questions.jsonl"
    with exp.open("w", encoding="utf-8") as fe, \
         ret.open("w", encoding="utf-8") as fr, \
         sim.open("w", encoding="utf-8") as fs:
        for r in all_rows:
            fe.write(json.dumps({
                "question_id": r["question_id"],
                "question": r["question"],
                "expected_answer_short": r["answer_short"],
                "expected_answer_long": r["answer_long"],
                "coverage": "in_corpus",
                "supporting_chunks": r["supporting_chunks"],
                "supporting_documents": r["supporting_documents"],
            }, ensure_ascii=False) + "\n")
            fr.write(json.dumps({
                "query": r["question"],
                "question_id": r["question_id"],
                "expected_chunk_ids": r["supporting_chunks"],
                "expected_doc_ids": r["supporting_documents"],
                "difficulty": r["difficulty"],
                "category": r["category"],
            }, ensure_ascii=False) + "\n")
            fs.write(json.dumps({
                "question_id": r["question_id"],
                "topic_id": r["topic_id"],
                "category": r["category"],
                "persona": r["persona"],
                "question": r["question"],
                "grounding": "llm",
                "supporting_chunks": r["supporting_chunks"],
            }, ensure_ascii=False) + "\n")
    log(f"wrote {len(all_rows)} rows to:")
    log(f"  {exp}")
    log(f"  {ret}")
    log(f"  {sim}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen2.5:7b-instruct")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--smoke", type=int, default=0,
                    help="if >0, generate this many questions per theme (test)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--temperature", type=float, default=0.6)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--only", default="", help="comma-separated theme codes to run")
    args = ap.parse_args()

    out = Path(args.out)
    work = out / "_work"
    out.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)

    only = {c.strip().upper() for c in args.only.split(",") if c.strip()}
    active = [(lbl, code, tgt, m) for (lbl, code, tgt, m) in THEMES
              if not only or code in only]
    target_codes = {code for _, code, _, _ in active}

    log(f"model={args.model}  out={out}  smoke={args.smoke or 'off'}")
    log(f"themes: {', '.join(code for _, code, _, _ in active)}")

    pools = build_pools(target_codes)

    rng = random.Random(args.seed)
    all_rows: list[dict] = []
    for lbl, code, tgt, _ in active:
        target = args.smoke if args.smoke else tgt
        log(f"=== {lbl} [{code}] target={target} ===")
        rows = generate_theme(lbl, code, target, pools[code], args.model,
                              work, random.Random(args.seed ^ hash(code) & 0xFFFF),
                              args.temperature, args.timeout)
        all_rows.extend(rows)

    write_outputs(all_rows, out)

    # summary
    from collections import Counter
    by_cat = Counter(r["category"] for r in all_rows)
    log("=== SUMMARY ===")
    for cat, n in by_cat.items():
        log(f"  {n:5d}  {cat}")
    log(f"  TOTAL {len(all_rows)}")


if __name__ == "__main__":
    main()
