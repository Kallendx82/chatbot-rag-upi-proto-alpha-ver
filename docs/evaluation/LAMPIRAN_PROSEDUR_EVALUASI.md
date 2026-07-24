# Lampiran — Prosedur Pelaksanaan Evaluasi Perbandingan Model Generasi

Dokumen ini adalah **prosedur eksekusi langkah demi langkah** yang dapat
disalin langsung (dengan penyesuaian seperlunya) ke bagian Lampiran
skripsi, mendokumentasikan bagaimana evaluasi perbandingan model
(Llama 3.1 8B Instruct vs Qwen 3.5 4B) dijalankan agar dapat direproduksi
oleh pembaca/penguji.

Untuk definisi metrik dan justifikasi metodologis (kenapa n=400/model,
kenapa `top_k=5`, kenapa budget $4,50), lihat `THESIS_NOTES.md` §1.1 —
dokumen ini fokus pada **prosedur eksekusi**, bukan justifikasi metodologis.

## Ringkasan Ruang Lingkup

| Item | Nilai |
|---|---|
| Model yang dibandingkan | Llama 3.1 8B Instruct (Q4_K_M) vs Qwen 3.5 4B (Q4_K_M) |
| Dataset | 1.816 pertanyaan (`dataset.json`), retrieval dievaluasi penuh |
| Sampel LLM-as-a-Judge | 400 pertanyaan per model (sama untuk kedua model), `seed=42` |
| Model penilai (judge) | Claude Haiku 4.5 (Anthropic) |
| `top_k` retrieval/generasi/konteks judge | 5 |
| Batas anggaran (hard stop) | USD 4,50 |
| Saldo Claude API riil saat evaluasi | **[ISI: nominal saldo Anda dan tanggal pengecekan]** |

## A. Prasyarat Lingkungan

Centang setiap item sebelum menjalankan evaluasi:

- [ ] Python 3.10+ terpasang, berada di direktori `docs/evaluation/`
- [ ] Dependensi terpasang: `pip install -r requirements.txt`
      (`requests`, `PyYAML`, `anthropic`)
- [ ] Ollama terpasang dan berjalan, dengan kedua model sudah di-*pull*:
      ```bash
      ollama pull llama3.1:8b-instruct-q4_K_M
      ollama pull qwen3.5:4b-q4_K_M
      ollama list   # verifikasi kedua model muncul
      ```
- [ ] Backend chatbot berjalan (`uvicorn app.main:app` dari folder
      `backend/`) dan dapat diakses di `http://localhost:8000`
- [ ] Kredensial Anthropic tersedia — salah satu dari:
      - Variabel lingkungan `ANTHROPIC_API_KEY` diset, **atau**
      - Sudah login sekali via `ant auth login`
- [ ] Saldo Claude API dicek di platform.claude.com/dashboard **sebelum**
      menjalankan evaluasi, dan `judge.budget_usd` di `config.yaml`
      dipastikan ≤ saldo tersebut (nilai saat ini: USD 4,50, untuk saldo
      USD 4,90 yang dicek pada 24 Juli 2026 — **update kalau saldo Anda
      sudah berbeda**)

## B. Prosedur Pelaksanaan

### Langkah 1 — Verifikasi backend aktif

```bash
curl http://localhost:8000/health
```
**Diharapkan:** respons JSON dengan status `"ok"` untuk komponen inti. Jika
gagal koneksi, jalankan backend dahulu sebelum lanjut.

### Langkah 2 — Verifikasi konfigurasi evaluasi

```bash
cat config.yaml
```
**Diharapkan:** `judge.budget_usd` ≤ saldo API riil Anda, `judge.model:
claude-haiku-4-5`, `judge.ragas_sample_size: 400`, `retrieval.top_k: 5`,
`models:` berisi kedua model yang dibandingkan.

### Langkah 3 — Jalankan evaluasi penuh

```bash
python run_eval.py
```

Tidak perlu argumen tambahan — semua parameter (model, budget, sampel,
top_k) sudah diset di `config.yaml` sesuai §A di atas. Proses berjalan
melalui tiga tahap yang tercetak berurutan di terminal:

```
[1/3] Evaluating retrieval (shared across models)...
  [1/1816] DITPEND_0001 (...ms, hit=True)
  ...
[budget] Sampling 400/1816 questions for LLM judging (seed=42) - judged for
EACH of the 2 model(s), i.e. 400 answer-quality judgments per model
(800 total).
[2/3] Judging retrieved context quality (Claude claude-haiku-4-5)...
  [.../1816] <id>: precision=... (spent=$.../$4.50)
[3/3] Generating & judging answers (400 question(s) x 2 model(s))...
  [1/400] <id> | llama3.1: ...ms, faith=0.XX | qwen3.5: ...ms, faith=0.XX
  ...
```

**Estimasi durasi:** tahap [1/3] (retrieval, 1.816 panggilan HTTP ke
backend) biasanya berjalan beberapa menit tergantung kecepatan mesin.
Tahap [2/3]+[3/3] (generasi lokal via Ollama + panggilan Claude API)
tergantung kecepatan hardware untuk inferensi lokal — catat waktu mulai
dan selesai aktual Anda di sini: **[ISI: waktu mulai — waktu selesai]**.

### Langkah 4 — Pantau kondisi anggaran selama proses (opsional tapi disarankan)

Perhatikan angka `spent=$.../$4.50` yang tercetak setiap panggilan judge.
Jika anggaran habis sebelum ke-400 pertanyaan selesai dinilai, script akan
mencetak `budget exhausted, skipping` dan **tetap melanjutkan** proses
generasi jawaban (tanpa penilaian tambahan) untuk pertanyaan yang tersisa —
ini bukan kegagalan, melainkan perilaku yang disengaja dan tercatat
transparan di ringkasan akhir (lihat Langkah 5).

### Langkah 5 — Baca ringkasan di akhir proses

Setelah selesai, terminal mencetak tabel perbandingan dan ringkasan
anggaran, contoh bentuknya:

```
==============================================================================
PERBANDINGAN MODEL - CHATBOT RAG UPI
==============================================================================

[Retrieval - identik untuk semua model, dihitung sekali]
  Questions w/ ground truth: .../1816 (... chunk-level)
  Hit Rate: ...
  ...

[Answer Quality - per model]
Metric                      Llama 3.1 8B Instruct...   Qwen 3.5 4B...
Faithfulness                 ...                        ...
...

[Judge Budget]
  limit_usd: 4.5
  spent_usd: ...
  remaining_usd: ...
  judge_calls_made: ...
  judge_calls_skipped_over_budget: ...
```

**Salin/screenshot blok ini persis** — ini adalah bukti pelaksanaan yang
dilampirkan (lihat §D).

### Langkah 6 — Simpan dan verifikasi file hasil

```bash
ls -la results/
```
**Diharapkan:** file baru `eval_<timestamp>.json` muncul di folder
`results/`. Verifikasi isinya dapat dibaca:
```bash
python -c "import json; d=json.load(open('results/eval_<timestamp>.json', encoding='utf-8')); print(d['budget']); print(d['retrieval_aggregate']['hit_rate'])"
```
File JSON ini adalah **sumber kebenaran** untuk mengisi tabel BAB IV
(`THESIS_NOTES.md` §2) — jangan salin angka dari layar terminal untuk
tabel skripsi, selalu ambil dari file JSON supaya presisi digit tidak
hilang karena pembulatan tampilan terminal.

## C. Reproduksibilitas

Evaluasi ini dapat diulang dengan hasil sampel yang identik (karena
`sample_seed: 42` tetap) menggunakan perintah yang sama persis:
```bash
python run_eval.py
```
Untuk mengulang dengan parameter berbeda (mis. anggaran baru setelah top
up saldo), gunakan flag CLI tanpa mengubah `config.yaml`:
```bash
python run_eval.py --budget <nominal_baru> --ragas-sample <n_baru>
```

## D. Bukti yang Dilampirkan

Isi/tempelkan pada skripsi fisik:

1. **Screenshot saldo Claude API** dari platform.claude.com/dashboard,
   diambil sebelum menjalankan evaluasi (menunjukkan saldo yang menjadi
   dasar perhitungan `budget_usd`).
2. **Cuplikan log terminal** dari awal (`[1/3] Evaluating retrieval...`)
   sampai ringkasan akhir (`[Judge Budget]`) — boleh dipotong bagian
   tengah yang berulang (baris per-pertanyaan), tapi header setiap tahap
   dan blok ringkasan akhir harus utuh.
3. **File `results/eval_<timestamp>.json`** — lampirkan sebagai lampiran
   digital/softcopy (terlalu besar untuk dicetak penuh; opsional cetak
   ringkasan `retrieval_aggregate` + `per_model_aggregate` + `budget` saja
   menggunakan perintah di Langkah 6).
4. **Tanggal dan waktu pelaksanaan**, versi commit git repo saat evaluasi
   dijalankan (`git rev-parse HEAD`), dicatat untuk keterlacakan.

---

**Catatan bagi Claude session di masa depan (termasuk Claude gratis) yang
melanjutkan dokumen ini:** jangan jalankan `run_eval.py` atas nama
pengguna kecuali diminta eksplisit — dokumen ini sengaja disusun untuk
pengguna jalankan sendiri agar mereka punya kendali penuh atas kapan
anggaran Claude API mereka terpakai. Tugas sesi lanjutan adalah membantu
mengisi §2 `THESIS_NOTES.md` dan bukti di §D dokumen ini setelah pengguna
melaporkan hasil aktualnya.
