# Evaluasi & Perbandingan Model — Chatbot RAG UPI

Folder ini berisi dataset, script, dan hasil evaluasi untuk mengukur kualitas
retrieval dan kualitas jawaban chatbot, termasuk **perbandingan head-to-head
antar model generasi** (mis. Llama 3.1 8B vs Qwen 3.5 4B) dengan LLM-as-a-Judge
(Claude) di bawah budget USD yang bisa diatur.

## Struktur

```
docs/evaluation/
├── README.md                    # Dokumentasi ini
├── THESIS_NOTES.md              # Draf metodologi BAB III + template tabel BAB IV
├── dataset.json                 # Dataset utama: 1.816 pertanyaan, ground truth chunk-level
├── dataset.smoke10.json         # Dataset kecil (10 soal) untuk smoke-test cepat/gratis
├── run_eval.py                  # Script evaluasi & perbandingan model (reusable)
├── import_legacy_dataset.py     # Importer dataset lama (D:\Project\RAG_UPI) -> dataset.json
├── generate_qa_candidates.py    # Generator draf pertanyaan baru (butuh verifikasi manual)
├── requirements.txt             # Dependensi Python (requests, PyYAML, anthropic)
├── results/                     # Folder output hasil evaluasi (auto-generated)
│   └── .gitkeep
└── config.yaml                  # Konfigurasi (model, budget, threshold, top_k, dll)
```

## Dataset

`dataset.json` berisi **1.816 pertanyaan** dengan ground truth **chunk-level**
(field `expected_chunk_ids`), diimpor dari proyek evaluasi sebelumnya
(`D:\Project\RAG_UPI\knowledge_layer\expected_answers.jsonl` +
`retrieval_eval.jsonl`) via `import_legacy_dataset.py` — setiap `chunk_id`
diverifikasi ulang terhadap `backend/app/data/chunks_meta.json` saat ini
(1.816/1.880 = 96,6% resolvable; sisanya dibuang, bukan disembunyikan —
lihat output importer). Ground truth chunk-level jauh lebih presisi dari
sekadar cocokkan judul dokumen, karena satu dokumen bisa punya banyak bagian
dan hanya satu chunk yang benar-benar relevan.

`dataset.smoke10.json` adalah dataset 10-soal (ground truth doc-level,
disusun manual dari dokumen Kalender Akademik & Pedoman Penyelenggaraan
Pendidikan UPI) untuk tes cepat tanpa perlu tunggu 1.816 panggilan retrieval
— pakai `--dataset dataset.smoke10.json`.

## Metrik yang Diukur

### Retrieval Quality (deterministik, gratis — dihitung sekali untuk seluruh 1.816 pertanyaan, sama untuk semua model)
| Metrik | Deskripsi |
|--------|-----------|
| **Hit Rate / Recall@K** | Apakah chunk yang benar (atau dokumen yang benar, untuk pertanyaan yang hanya punya ground truth level-dokumen) ada di top-K hasil retrieval? |
| **MRR (Mean Reciprocal Rank)** | Rata-rata 1/posisi chunk/dokumen benar pertama |
| **Precision@K** | Estimasi 1/K saat hit (asumsi satu chunk/dokumen relevan per pertanyaan — lihat catatan di bawah) |
| **Avg Score** | Rata-rata skor embedding dari chunk yang di-retrieve |
| **Keyword Coverage** | Persentase `expected_keywords` yang muncul di chunk hasil retrieval |

Hit dicek dengan **kecocokan `chunk_id` persis** bila `expected_chunk_ids`
tersedia (mayoritas dataset saat ini), dengan fallback ke kecocokan judul
dokumen untuk pertanyaan yang hanya punya `expected_doc_title`. Field
`match_level` per pertanyaan (`"chunk"` / `"doc_title"` / `"none"`) dan
ringkasan `n_with_chunk_level_ground_truth` di `retrieval_aggregate`
mencatat mana yang dipakai — penting untuk transparansi metodologis di BAB
III/IV.

> **Catatan Precision@K:** meski ground truth sekarang chunk-level, dataset
> masih menandai (biasanya) satu chunk relevan per pertanyaan, bukan daftar
> lengkap semua chunk relevan. Karena itu Precision@K dihitung sebagai batas
> atas (1/K bila hit), bukan hitungan sesungguhnya dari berapa banyak hasil
> top-K yang relevan.

### Answer Quality — LLM-as-a-Judge (RAGAS-inspired, pakai Claude, per model)
| Metrik | Deskripsi | Butuh ground truth? |
|--------|-----------|---|
| **Faithfulness** | Apakah jawaban hanya berdasarkan konteks yang di-retrieve (tidak ada halusinasi)? (0.0–1.0) | Tidak |
| **Answer Relevancy** | Apakah jawaban benar-benar menjawab pertanyaan? (0.0–1.0) | Tidak |
| **Context Precision** | Apakah chunk yang di-retrieve relevan untuk menjawab pertanyaan? (0.0–1.0) | Tidak |
| **Context Recall** | Apakah informasi ground truth tercakup dalam konteks yang di-retrieve? (0.0–1.0, `-1` jika ground truth kosong) | Ya |

Context Precision/Recall dihitung **sekali per pertanyaan** (konteksnya sama
untuk semua model dibandingkan). Faithfulness/Answer Relevancy dihitung
**per pertanyaan × per model** karena jawabannya berbeda.

Selain itu dicatat juga metrik gratis per model: **latency**, **panjang
jawaban**, dan **refusal rate** (deteksi kata kunci "maaf/tidak
tersedia/tidak ditemukan").

**Karena LLM-as-a-Judge berbayar dan populasi dataset besar (1.816),**
evaluasi jawaban dijalankan pada **sampel acak** (default n=500, lihat
`config.yaml` → `judge.ragas_sample_size`, dan justifikasi lengkapnya di
`THESIS_NOTES.md` § 1.1) — bukan seluruh populasi. Retrieval tetap dihitung
untuk seluruh 1.816 pertanyaan karena gratis.

## Cara Pakai

### 0. Install dependensi

```bash
cd docs/evaluation
pip install -r requirements.txt
```

Judge (Claude) butuh kredensial Anthropic — set `ANTHROPIC_API_KEY`, atau
jalankan `ant auth login` sekali agar SDK memakai profil tersimpan.

### 1. Dataset sudah siap — tidak perlu diedit untuk run pertama

`dataset.json` (1.816 soal) sudah lengkap dengan ground truth. Untuk
menambah cakupan kategori/dokumen baru, lihat bagian **Menambah Pertanyaan
Uji Baru** di bawah — jangan tulis manual dari ingatan, selalu telusuri
sumber asli dulu.

Format satu entri dataset (kalau mau edit manual):

```json
{
  "id": "KA-01",
  "question": "Kapan pembayaran UKT mahasiswa baru jalur SNBP?",
  "expected_doc_title": "Kalender Akademik UPI 2026/2027",
  "expected_chunk_ids": ["376afb68e033e2e4::23"],
  "expected_keywords": ["UKT", "SNBP", "pembayaran"],
  "ground_truth": "Pembayaran UKT mahasiswa baru jalur SNBP dijadwalkan pada ...",
  "category": "kalender_akademik",
  "difficulty": "easy"
}
```

`expected_chunk_ids` opsional tapi sangat disarankan (retrieval metrics jauh
lebih presisi). `expected_doc_title` dipakai sebagai fallback bila
`expected_chunk_ids` kosong.

### 2. Atur Model & Budget di `config.yaml`

```yaml
models:
  - name: "llama3.1:8b-instruct-q4_K_M"
    label: "Llama 3.1 8B Instruct (Q4_K_M)"
  - name: "qwen3.5:4b-q4_K_M"
    label: "Qwen 3.5 4B (Q4_K_M)"

judge:
  model: "claude-haiku-4-5"   # judge murah — cocok untuk budget kecil
  budget_usd: 8.0              # batas keras, script berhenti judge saat tercapai
  ragas_sample_size: 500       # sampel RAGAS dari populasi 1.816 (lihat THESIS_NOTES.md § 1.1)
```

Kedua model harus sudah ter-`pull` di Ollama server yang dipakai backend
(`ollama pull llama3.1:8b-instruct-q4_K_M`, dst).

### 3. Jalankan Evaluasi

```bash
# Full run: retrieval (1.816 soal) + generation (2 model) + judge Claude (sampel 500)
python run_eval.py

# Override model/budget dari command line, tanpa ubah config.yaml
python run_eval.py --models llama3.1:8b-instruct-q4_K_M qwen3.5:4b-q4_K_M --budget 8.0

# Override ukuran sampel RAGAS (mengunci biaya sebelum jalan)
python run_eval.py --ragas-sample 200

# Smoke test cepat (10 soal, dataset kecil)
python run_eval.py --dataset dataset.smoke10.json

# Hanya evaluasi retrieval (gratis, tanpa LLM apapun)
python run_eval.py --retrieval-only

# Generate jawaban di kedua model tapi skip judge (gratis, tanpa Claude)
python run_eval.py --skip-judge

# Custom top_k / output path
python run_eval.py --top-k 5 --output results/eval_2026-07-24.json
```

Script berhenti mengirim panggilan judge begitu proyeksi biaya berikutnya
akan melewati `budget_usd` — sisa pertanyaan tetap di-generate (jawabannya
tersimpan) tapi ditandai `judge: null`, dan ringkasan `budget` di JSON output
mencatat berapa panggilan judge yang dilewati.

### 4. Baca Hasil

Hasil disimpan di `results/eval_<timestamp>.json` (retrieval aggregate,
per-model answer aggregate, budget summary, raw per-question hasil) + tabel
perbandingan ringkas di terminal. Isi tabel BAB IV di `THESIS_NOTES.md` §2
langsung dari file JSON ini.

## Menambah Pertanyaan Uji Baru

**Opsi A — impor ulang dari sumber lain** dengan format serupa
`expected_answers.jsonl`/`retrieval_eval.jsonl` (question, ground truth,
chunk_id pendukung): sesuaikan `import_legacy_dataset.py` atau tulis
importer baru dengan pola yang sama (resolusi ulang `chunk_id` terhadap
index terkini — jangan skip langkah verifikasi ini).

**Opsi B — generate draf dari dokumen yang belum tercakup**, lalu verifikasi
manual satu per satu:

```bash
python generate_qa_candidates.py --title-contains "Kalender Akademik" --limit 20 --output candidates.json
```

Script ini men-scan `chunks_meta.json`, mencari kalimat berpola fakta
("X dijadwalkan pada tanggal Y", "X adalah Y", dst.), dan menghasilkan draf
pertanyaan + fragmen ground truth. **Setiap entri ditandai
`needs_verification: true`** — baca `source_text_full`-nya, perbaiki
fraseologi pertanyaan/jawaban seperlunya, lalu baru pindahkan ke
`dataset.json` secara manual. Jangan salin `suggested_ground_truth_fragment`
mentah-mentah tanpa dibaca — ini draf, bukan jawaban final.

## Kapan Perlu Evaluasi Ulang?

- Setelah menambah/mengubah dokumen di knowledge base
- Setelah mengubah parameter chunking (ukuran, overlap)
- Setelah mengubah embedding model atau retrieval logic
- Setelah mengubah prompt template
- Saat membandingkan model generasi baru (ganti `--models`, gunakan script
  yang sama — dirancang untuk dipakai berulang)
- Sebelum dan sesudah perubahan besar untuk perbandingan (A/B)
