# Evaluasi & Perbandingan Model — Chatbot RAG UPI

Folder ini berisi dataset, script, dan hasil evaluasi untuk mengukur kualitas
retrieval dan kualitas jawaban chatbot, termasuk **perbandingan head-to-head
antar model generasi** (mis. Llama 3.1 8B vs Qwen 3.5 4B) dengan LLM-as-a-Judge
(Claude) di bawah budget USD yang bisa diatur.

## Struktur

```
docs/evaluation/
├── README.md                  # Dokumentasi ini
├── dataset.json                # Dataset pertanyaan + ground truth
├── run_eval.py                 # Script evaluasi & perbandingan model (reusable)
├── requirements.txt             # Dependensi Python (requests, PyYAML, anthropic)
├── results/                     # Folder output hasil evaluasi (auto-generated)
│   └── .gitkeep
└── config.yaml                 # Konfigurasi (model, budget, threshold, top_k, dll)
```

## Metrik yang Diukur

### Retrieval Quality (deterministik, gratis — dihitung sekali, sama untuk semua model)
| Metrik | Deskripsi |
|--------|-----------|
| **Hit Rate / Recall@K** | Apakah dokumen yang benar ada di top-K hasil retrieval? |
| **MRR (Mean Reciprocal Rank)** | Rata-rata 1/posisi dokumen benar pertama |
| **Precision@K** | Estimasi 1/K saat hit (ground truth hanya berlevel dokumen, bukan chunk — lihat catatan di bawah) |
| **Avg Score** | Rata-rata skor embedding dari chunk yang di-retrieve |
| **Keyword Coverage** | Persentase `expected_keywords` yang muncul di chunk hasil retrieval |

> **Catatan Precision@K:** dataset hanya menandai satu dokumen relevan per
> pertanyaan (`expected_doc_title`), bukan chunk-level ground truth. Karena
> itu Precision@K dihitung sebagai batas atas (1/K bila hit), bukan hitungan
> sesungguhnya dari berapa banyak hasil top-K yang relevan. Untuk Precision@K
> yang presisi, tambahkan chunk-level relevance judgments ke dataset.

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

## Cara Pakai

### 0. Install dependensi

```bash
cd docs/evaluation
pip install -r requirements.txt
```

Judge (Claude) butuh kredensial Anthropic — set `ANTHROPIC_API_KEY`, atau
jalankan `ant auth login` sekali agar SDK memakai profil tersimpan.

### 1. Siapkan Dataset

Edit `dataset.json` — tambah pertanyaan, dokumen sumber yang diharapkan, dan
(opsional tapi disarankan untuk Context Recall) jawaban ground truth. Format:

```json
{
  "id": "KA-01",
  "question": "Kapan pembayaran UKT mahasiswa baru jalur SNBP?",
  "expected_doc_title": "Kalender Akademik UPI 2026/2027",
  "expected_keywords": ["UKT", "SNBP", "pembayaran"],
  "ground_truth": "Pembayaran UKT mahasiswa baru jalur SNBP dijadwalkan pada ...",
  "category": "kalender_akademik",
  "difficulty": "easy"
}
```

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
  ragas_sample_size: null      # null = semua pertanyaan; isi angka untuk subset
```

Kedua model harus sudah ter-`pull` di Ollama server yang dipakai backend
(`ollama pull llama3.1:8b-instruct-q4_K_M`, dst).

### 3. Jalankan Evaluasi

```bash
# Full run: retrieval + generation (2 model dari config) + judge Claude
python run_eval.py

# Override model/budget dari command line, tanpa ubah config.yaml
python run_eval.py --models llama3.1:8b-instruct-q4_K_M qwen3.5:4b-q4_K_M --budget 8.0

# Batasi jumlah pertanyaan yang di-judge Claude (mengunci biaya sebelum jalan)
python run_eval.py --ragas-sample 50

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
perbandingan ringkas di terminal.

## Kapan Perlu Evaluasi Ulang?

- Setelah menambah/mengubah dokumen di knowledge base
- Setelah mengubah parameter chunking (ukuran, overlap)
- Setelah mengubah embedding model atau retrieval logic
- Setelah mengubah prompt template
- Saat membandingkan model generasi baru (ganti `--models`, gunakan script
  yang sama — dirancang untuk dipakai berulang)
- Sebelum dan sesudah perubahan besar untuk perbandingan (A/B)
