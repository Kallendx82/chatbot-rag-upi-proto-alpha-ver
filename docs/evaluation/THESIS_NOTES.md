# Catatan untuk Penulisan Skripsi — Evaluasi & Perbandingan Model

Dokumen ini menjembatani `run_eval.py` dengan BAB III (Metodologi) dan
BAB IV (Hasil & Pembahasan) skripsi. Ditulis supaya bisa dipakai ulang oleh
sesi Claude manapun di masa depan — termasuk Claude gratis — tanpa perlu
menelusuri ulang seluruh riwayat percakapan ini.

> **Status saat ini (2026-07-24): evaluasi BELUM dijalankan.** Semua angka di
> bagian "Hasil" bawah ini adalah *placeholder* yang harus diisi setelah
> menjalankan `python run_eval.py`. Jangan salin angka bohong ke skripsi.

## 0. Yang harus dilakukan sebelum menjalankan evaluasi

1. **Isi `ground_truth` di `dataset.json`.** Saat ini ke-10 pertanyaan
   (`KA-01`…`AKD-02`) punya `ground_truth: ""` kosong — cek isinya dengan:
   ```bash
   python -c "import json; d=json.load(open('dataset.json',encoding='utf-8')); print([x['id'] for x in d if not x['ground_truth'].strip()])"
   ```
   Tanpa ground truth, metrik **Context Recall** tidak bisa dihitung (akan
   selalu `-1`/n-a) — Faithfulness, Answer Relevancy, dan Context Precision
   tetap bisa dihitung tanpa ground truth.
2. **Pastikan kedua model sudah di-`pull` di Ollama:**
   ```bash
   ollama pull llama3.1:8b-instruct-q4_K_M
   ollama pull qwen3.5:4b-q4_K_M
   ```
3. **Jalankan backend** (`uvicorn app.main:app` dari folder `backend/`).
4. **Set kredensial Anthropic** untuk judge: `ANTHROPIC_API_KEY` env var, atau
   `ant auth login` sekali di mesin ini.
5. (Opsional, disarankan) **Perbesar dataset.** 10 pertanyaan cukup untuk uji
   coba script, tapi terlalu kecil untuk klaim ilmiah yang kuat di BAB IV.
   Evaluasi sebelumnya (didokumentasikan di `Latihan Pertanyaan Penguji.md`)
   memakai 1.880 pertanyaan retrieval + 200 sampel RAGAS — pertimbangkan
   menambah pertanyaan ke `dataset.json` sebelum run final, atau jelaskan di
   BAB III bahwa evaluasi kali ini memakai subset lebih kecil sebagai
   *pilot/spot-check* dan bukan replikasi penuh.

## 1. Teks Metodologi (draf untuk BAB III)

Adaptasi paragraf berikut sesuai gaya penulisan skripsi Anda. Metodologi ini
mengikuti pendekatan *Design and Development Research* (Richey & Klein, 2014)
yang sudah dipakai pada evaluasi sebelumnya.

> Evaluasi perbandingan model dilakukan secara *end-to-end* terhadap dua
> komponen sistem RAG: (1) kualitas retrieval, dan (2) kualitas jawaban yang
> dihasilkan oleh model generasi. Kedua komponen dievaluasi menggunakan
> dataset pertanyaan uji yang mencakup kategori kalender akademik, PMB, PPID,
> dan akademik umum, masing-masing dilengkapi dokumen sumber yang diharapkan
> (*expected_doc_title*), kata kunci yang diharapkan (*expected_keywords*),
> dan jawaban rujukan (*ground truth*) untuk sebagian pertanyaan.
>
> **Evaluasi retrieval** bersifat deterministik dan dihitung sekali untuk
> seluruh pertanyaan, karena hasil retrieval tidak bergantung pada model
> generasi yang digunakan. Metrik yang diukur adalah *Hit Rate* (Recall@K),
> *Mean Reciprocal Rank* (MRR), dan cakupan kata kunci (*keyword coverage*)
> pada K = {1, 3, 5, 8}.
>
> **Evaluasi kualitas jawaban** membandingkan dua model generasi yang
> dijalankan secara lokal melalui Ollama: **Llama 3.1 8B Instruct (Q4_K_M)**
> dan **Qwen 3.5 4B (Q4_K_M)**. Kedua model menerima konteks retrieval yang
> identik untuk setiap pertanyaan (variabel terkontrol), sehingga perbedaan
> kualitas jawaban dapat diatribusikan langsung ke kapabilitas model, bukan
> ke perbedaan retrieval.
>
> Kualitas jawaban dinilai menggunakan pendekatan **LLM-as-a-Judge** yang
> terinspirasi dari kerangka kerja RAGAS, dengan model penilai (*judge*)
> Claude Haiku 4.5 dari Anthropic — model yang independen dari kedua model
> yang dievaluasi untuk menghindari *self-preference bias*. Empat metrik
> dinilai: *faithfulness* (sejauh mana jawaban hanya berdasarkan konteks yang
> di-retrieve, tanpa halusinasi), *answer relevancy* (sejauh mana jawaban
> menjawab pertanyaan secara langsung), *context precision* (sejauh mana
> chunk yang di-retrieve relevan terhadap pertanyaan), dan *context recall*
> (sejauh mana informasi pada jawaban rujukan tercakup dalam konteks yang
> di-retrieve, dihitung hanya untuk pertanyaan dengan ground truth tersedia).
> Setiap metrik menghasilkan skor 0,0–1,0 beserta alasan tekstual dari model
> penilai, diperoleh melalui *structured output* (skema JSON) untuk menjamin
> keluaran yang dapat diproses secara konsisten.
>
> Karena evaluasi LLM-as-a-Judge menggunakan API berbayar, proses evaluasi
> dibatasi oleh anggaran biaya sebesar USD 8,00 yang dilacak secara *real-time*
> selama proses berjalan; apabila proyeksi biaya panggilan berikutnya akan
> melampaui batas tersebut, proses penilaian dihentikan untuk sisa pertanyaan
> sementara proses pembangkitan jawaban tetap dilanjutkan, sehingga hasil
> parsial tetap dapat dianalisis dan dilaporkan secara transparan.

## 2. Template Tabel Hasil (draf untuk BAB IV)

Isi setelah menjalankan `python run_eval.py` dan membaca
`results/eval_<timestamp>.json`.

### Tabel 4.x — Hasil Evaluasi Retrieval

| Metrik | Nilai |
|---|---|
| Jumlah pertanyaan | `retrieval_aggregate.n_questions` |
| Hit Rate | `retrieval_aggregate.hit_rate` |
| MRR | `retrieval_aggregate.mrr` |
| Recall@1 / @3 / @5 / @8 | `retrieval_aggregate.recall_at_k` |
| Avg Keyword Coverage | `retrieval_aggregate.avg_keyword_coverage` |
| Avg Score (embedding) | `retrieval_aggregate.avg_score_mean` |

### Tabel 4.y — Perbandingan Kualitas Jawaban: Llama 3.1 8B vs Qwen 3.5 4B

| Metrik | Llama 3.1 8B Instruct (Q4_K_M) | Qwen 3.5 4B (Q4_K_M) |
|---|---|---|
| Faithfulness | `per_model_aggregate["llama3.1:8b-instruct-q4_K_M"].faithfulness` | `per_model_aggregate["qwen3.5:4b-q4_K_M"].faithfulness` |
| Answer Relevancy | … | … |
| Refusal Rate | … | … |
| Avg Latency (ms) | … | … |
| Avg Panjang Jawaban (chars) | … | … |
| Jumlah Pertanyaan Dinilai (judge) | … | … |

### Tabel 4.z — Ringkasan Anggaran Evaluasi (Transparansi Biaya)

| Item | Nilai |
|---|---|
| Model judge | `config.judge_model` |
| Batas anggaran | `budget.limit_usd` |
| Biaya terpakai | `budget.spent_usd` |
| Panggilan judge selesai | `budget.judge_calls_made` |
| Panggilan judge dilewati (anggaran habis) | `budget.judge_calls_skipped_over_budget` |

Ambil nilai-nilai di atas langsung dari file JSON hasil — jangan hitung
manual ulang, supaya konsisten dengan artefak yang bisa dilampirkan sebagai
bukti (`results/eval_<timestamp>.json`) di lampiran skripsi.

## 3. Cara pakai bagian ini di sesi Claude selanjutnya (termasuk Claude gratis)

Prompt singkat yang bisa dipakai untuk melanjutkan pekerjaan ini tanpa perlu
membaca ulang seluruh riwayat sesi:

> "Baca `docs/evaluation/THESIS_NOTES.md` di project ini. Jalankan
> `python run_eval.py` sesuai instruksi di sana, lalu isi Tabel 4.x/4.y/4.z
> di bagian 2 dengan angka hasil sebenarnya, dan bantu saya menulis narasi
> pembahasan BAB IV berdasarkan angka tersebut."

Karena semua konteks metodologis (definisi metrik, alasan pemilihan model
judge, desain kontrol variabel, dan mekanisme budget) sudah tertulis di
dokumen ini, model manapun — termasuk model gratis dengan konteks terbatas —
cukup membaca file ini untuk melanjutkan tanpa kehilangan nuansa keputusan
yang sudah diambil.
