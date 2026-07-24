# Catatan untuk Penulisan Skripsi — Evaluasi & Perbandingan Model

Dokumen ini menjembatani `run_eval.py` dengan BAB III (Metodologi) dan
BAB IV (Hasil & Pembahasan) skripsi. Ditulis supaya bisa dipakai ulang oleh
sesi Claude manapun di masa depan — termasuk Claude gratis — tanpa perlu
menelusuri ulang seluruh riwayat percakapan ini.

> **Status saat ini (2026-07-24): evaluasi BELUM dijalankan.** Semua angka di
> bagian "Hasil" bawah ini adalah *placeholder* yang harus diisi setelah
> menjalankan `python run_eval.py`. Jangan salin angka bohong ke skripsi.

## 0. Yang harus dilakukan sebelum menjalankan evaluasi

1. **Dataset sudah siap** — `dataset.json` sekarang berisi **1.816 pertanyaan**
   dengan ground truth **chunk-level** (bukan lagi 10 pertanyaan manual).
   Diimpor dari proyek evaluasi sebelumnya (`D:\Project\RAG_UPI\knowledge_layer\
   expected_answers.jsonl` + `retrieval_eval.jsonl`) via
   `docs/evaluation/import_legacy_dataset.py`, dengan setiap `chunk_id`
   diverifikasi ulang terhadap index backend saat ini (`chunks_meta.json`) —
   1.816 dari 1.880 pertanyaan asli (96,6%) berhasil diverifikasi; 64 sisanya
   dibuang karena mereferensikan baris sintetis (mis. tabel UKT tambahan)
   yang tidak benar-benar ter-*ingest* di corpus saat ini. Lihat § 1.1 di
   bawah untuk detail justifikasi metodologis bagian ini.
2. **Pastikan kedua model sudah di-`pull` di Ollama:**
   ```bash
   ollama pull llama3.1:8b-instruct-q4_K_M
   ollama pull qwen3.5:4b-q4_K_M
   ```
3. **Jalankan backend** (`uvicorn app.main:app` dari folder `backend/`).
4. **Set kredensial Anthropic** untuk judge: `ANTHROPIC_API_KEY` env var, atau
   `ant auth login` sekali di mesin ini.
5. **Jangan jalankan generation+judge untuk 1.816 pertanyaan mentah-mentah.**
   Retrieval (gratis, deterministik) dihitung untuk **seluruh 1.816**
   pertanyaan secara default. Untuk LLM-as-a-Judge, `config.yaml` sudah
   diset `ragas_sample_size: 500` — script otomatis mengambil sampel acak
   500 pertanyaan (seed tetap = 42, jadi hasil sampel sama tiap re-run) agar
   biaya tetap di bawah budget $8. Jangan ubah ini ke `null` kecuali paham
   konsekuensi biayanya (lihat § 1.1).
6. (Opsional) Perbesar dataset lebih lanjut dengan `generate_qa_candidates.py`
   (lihat § 4) untuk kategori dokumen yang belum tercakup 1.816 pertanyaan
   ini — **wajib verifikasi manual** sebelum ground truth-nya dipakai.

## 1. Teks Metodologi (draf untuk BAB III)

Adaptasi paragraf berikut sesuai gaya penulisan skripsi Anda. Metodologi ini
mengikuti pendekatan *Design and Development Research* (Richey & Klein, 2014)
yang sudah dipakai pada evaluasi sebelumnya.

> Evaluasi perbandingan model dilakukan secara *end-to-end* terhadap dua
> komponen sistem RAG: (1) kualitas retrieval, dan (2) kualitas jawaban yang
> dihasilkan oleh model generasi. Kedua komponen dievaluasi menggunakan
> dataset pertanyaan uji berjumlah **1.816 pertanyaan** yang mencakup
> sepuluh kategori (Direktorat Pendidikan, LPPM, Penerimaan Mahasiswa Baru,
> Informasi Publik/PPID, lima kampus daerah UPI, dan Informasi Umum/Kalender
> Akademik), masing-masing dilengkapi jawaban rujukan (*ground truth*) dan
> **ground truth pada level *chunk*** — yaitu potongan teks spesifik dari
> dokumen sumber yang seharusnya di-*retrieve* untuk menjawab pertanyaan
> tersebut, bukan sekadar judul dokumen. Ground truth chunk-level ini
> diverifikasi ulang terhadap indeks vektor yang aktif digunakan sistem pada
> saat evaluasi dilakukan, untuk memastikan validitasnya tidak basi akibat
> perubahan korpus dokumen dari waktu ke waktu.

### 1.1 Justifikasi Ukuran Sampel LLM-as-a-Judge (n = 500 dari N = 1.816)

> **Evaluasi retrieval dilakukan terhadap seluruh populasi dataset (N = 1.816
> pertanyaan)**, karena metrik retrieval (Hit Rate, Recall@K, MRR, keyword
> coverage) bersifat deterministik dan tidak berbiaya — tidak ada kendala
> praktis untuk mengevaluasi seluruh dataset.
>
> **Evaluasi kualitas jawaban (LLM-as-a-Judge) dilakukan terhadap sampel
> acak sebanyak n = 500 pertanyaan** dari populasi N = 1.816, dipilih
> menggunakan *simple random sampling* dengan *seed* tetap (42) agar hasil
> sampel dapat direproduksi persis pada evaluasi ulang. Pembatasan ini
> **diperlukan karena setiap penilaian melalui LLM-as-a-Judge menggunakan
> Claude API berbayar**, sehingga mengevaluasi seluruh populasi untuk dua
> model generasi sekaligus (± 1.816 × 2 × 2 = 7.264 panggilan API) berada
> jauh di luar anggaran penelitian yang ditetapkan sebesar USD 8,00.
>
> Ukuran sampel n = 500 dipilih dengan pertimbangan sebagai berikut:
> 1. **Jauh lebih besar dibanding evaluasi RAGAS sebelumnya** pada proyek
>    yang sama, yang menggunakan n = 200 sampel dari populasi yang lebih
>    kecil — sehingga tingkat kepercayaan statistik hasil kali ini lebih
>    tinggi (proporsi sampel terhadap populasi naik dari ~10,6% menjadi
>    ~27,5%).
> 2. **Berada nyaman di dalam batas anggaran**: total panggilan judge untuk
>    n = 500 adalah 500 (penilaian konteks, dibagi bersama kedua model) +
>    500 × 2 (penilaian jawaban per model) = 1.500 panggilan. Dengan model
>    penilai Claude Haiku 4.5 (USD 1,00/1M token input, USD 5,00/1M token
>    output), estimasi biaya berada pada kisaran USD 3–5, menyisakan ruang
>    aman terhadap batas USD 8,00 sehingga mekanisme *hard budget stop* pada
>    script tidak diperkirakan akan terpicu di tengah proses.
> 3. **Menggunakan *seed* acak tetap**, bukan pemilihan manual, untuk
>    menghindari bias seleksi peneliti terhadap pertanyaan yang
>    "menguntungkan" salah satu model.
>
> **Keterbatasan yang perlu diakui secara eksplisit:** sampling yang
> digunakan adalah *simple random sampling* atas keseluruhan populasi, bukan
> *stratified sampling* per kategori — sehingga proporsi kategori pada
> sampel n = 500 dapat sedikit berbeda dari proporsi populasi N = 1.816.
> Nilai `n_judged` per kategori pada hasil JSON (`results/eval_*.json`)
> perlu dilaporkan di BAB IV untuk transparansi mengenai representativitas
> sampel per kategori.

> **Evaluasi retrieval** bersifat deterministik dan dihitung sekali untuk
> seluruh 1.816 pertanyaan, karena hasil retrieval tidak bergantung pada
> model generasi yang digunakan. Metrik yang diukur adalah *Hit Rate*
> (berbasis kecocokan *chunk_id* persis dengan ground truth, dengan fallback
> ke kecocokan judul dokumen untuk sebagian kecil pertanyaan yang hanya
> memiliki ground truth di level dokumen), *Recall@K* dan *Mean Reciprocal
> Rank* (MRR), serta cakupan kata kunci (*keyword coverage*) pada
> K = {1, 3, 5, 8}.
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
> di-retrieve). Setiap metrik menghasilkan skor 0,0–1,0 beserta alasan
> tekstual dari model penilai, diperoleh melalui *structured output* (skema
> JSON) untuk menjamin keluaran yang dapat diproses secara konsisten.
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

### Tabel 4.x — Hasil Evaluasi Retrieval (N = 1.816 pertanyaan, populasi penuh)

| Metrik | Nilai |
|---|---|
| Jumlah pertanyaan (total / dengan ground truth) | `retrieval_aggregate.n_questions` / `retrieval_aggregate.n_with_ground_truth` |
| — dari itu, ground truth chunk-level | `retrieval_aggregate.n_with_chunk_level_ground_truth` |
| Hit Rate | `retrieval_aggregate.hit_rate` |
| MRR | `retrieval_aggregate.mrr` |
| Recall@1 / @3 / @5 / @8 | `retrieval_aggregate.recall_at_k` |
| Avg Keyword Coverage | `retrieval_aggregate.avg_keyword_coverage` |
| Avg Score (embedding) | `retrieval_aggregate.avg_score_mean` |

### Tabel 4.y — Perbandingan Kualitas Jawaban: Llama 3.1 8B vs Qwen 3.5 4B (n = 500 sampel)

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
| Populasi (N) / Sampel RAGAS (n) | 1.816 / `config.judge` sample size terpakai |
| Batas anggaran | `budget.limit_usd` |
| Biaya terpakai | `budget.spent_usd` |
| Panggilan judge selesai | `budget.judge_calls_made` |
| Panggilan judge dilewati (anggaran habis) | `budget.judge_calls_skipped_over_budget` |

Ambil nilai-nilai di atas langsung dari file JSON hasil — jangan hitung
manual ulang, supaya konsisten dengan artefak yang bisa dilampirkan sebagai
bukti (`results/eval_<timestamp>.json`) di lampiran skripsi.

## 3. Sumber Data (untuk BAB III — kejujuran metodologis)

Tegaskan di BAB III bahwa dataset pertanyaan uji **bukan dibuat khusus untuk
evaluasi perbandingan model ini**, melainkan diwariskan dari fase
pengembangan sistem sebelumnya di proyek yang sama (`RAG_UPI`), dengan
proses re-verifikasi sebagai berikut:

1. Dataset asli (`expected_answers.jsonl`, `retrieval_eval.jsonl`) memuat
   1.880 pertanyaan dengan ground truth level-chunk, disusun berdasarkan
   korpus dokumen UPI yang telah di-*ingest* pada tahap pengembangan awal.
2. Karena korpus dokumen dan indeks vektor sistem berubah dari waktu ke
   waktu (dokumen baru ditambahkan, dokumen lama di-*re-chunk*), setiap
   `chunk_id` pada dataset diverifikasi ulang terhadap indeks yang aktif
   digunakan pada saat evaluasi ini dilakukan (`import_legacy_dataset.py`).
3. 1.816 dari 1.880 pertanyaan (96,6%) berhasil diverifikasi penuh dan
   dipakai; 64 pertanyaan sisanya dibuang karena `chunk_id` rujukannya tidak
   lagi ditemukan pada indeks saat ini (mayoritas mereferensikan baris data
   sintetis tambahan yang tidak benar-benar melalui proses *ingestion*
   dokumen).

## 4. Menambah pertanyaan uji baru (opsional, untuk ekspansi cakupan)

Gunakan `generate_qa_candidates.py` untuk men-scan `chunks_meta.json` dan
menghasilkan draf pertanyaan template dari dokumen yang belum tercakup
1.816 pertanyaan yang ada. **Output dari script ini WAJIB diverifikasi
manual satu per satu sebelum ground truth-nya dipakai untuk klaim di BAB
IV** — script hanya membantu menemukan kandidat pertanyaan + memotong teks
sumber yang relevan, bukan menjamin kebenaran jawabannya.

```bash
python generate_qa_candidates.py --category "Kalender Akademik" --limit 20 --output candidates.json
```

Lihat docstring script tersebut untuk opsi lengkap. Setelah diverifikasi,
gabungkan pertanyaan yang lolos verifikasi ke `dataset.json` secara manual
(format sudah dijelaskan di README.md § Cara Pakai).

## 5. Cara pakai bagian ini di sesi Claude selanjutnya (termasuk Claude gratis)

Prompt singkat yang bisa dipakai untuk melanjutkan pekerjaan ini tanpa perlu
membaca ulang seluruh riwayat sesi:

> "Baca `docs/evaluation/THESIS_NOTES.md` di project ini. Jalankan
> `python run_eval.py` sesuai instruksi di sana, lalu isi Tabel 4.x/4.y/4.z
> di bagian 2 dengan angka hasil sebenarnya, dan bantu saya menulis narasi
> pembahasan BAB IV berdasarkan angka tersebut."

Karena semua konteks metodologis (definisi metrik, alasan pemilihan model
judge, desain kontrol variabel, justifikasi ukuran sampel, dan mekanisme
budget) sudah tertulis di dokumen ini, model manapun — termasuk model gratis
dengan konteks terbatas — cukup membaca file ini untuk melanjutkan tanpa
kehilangan nuansa keputusan yang sudah diambil.
