# PROJECT KNOWLEDGE BASE — Chatbot RAG UPI

> **Tujuan dokumen ini:** menjadi satu sumber acuan tunggal tentang proyek ini,
> supaya kamu (dan asisten AI mana pun: Claude/Codex/GPT) **tidak perlu
> menjelaskan ulang dari awal**. Bila ada perubahan besar, perbarui file ini.
>
> Terakhir diperbarui: 2026-06-30. Repo: `Kallendx82/Chatbot-RAG-UPI`.
> Root proyek: `D:\Project\RAG_UPI`.

---

## 1. Identitas Proyek

- **Judul skripsi:** *Rancang Bangun Chatbot sebagai Sumber Informasi Sivitas
  Universitas Pendidikan Indonesia Berbasis Retrieval-Augmented Generation (RAG).*
- **Program studi:** S1 Teknik Komputer, UPI Kampus Cibiru.
- **Target pengguna:** sivitas akademika UPI dan calon mahasiswa.
- **Masalah yang diselesaikan:** informasi resmi UPI tersebar di banyak laman &
  dokumen (PDF/HTML), sulit ditemukan cepat. Chatbot RAG menjawab pertanyaan
  bahasa alami dengan jawaban **akurat + bersumber** dari dokumen resmi.
- **Sifat:** purwarupa (prototype) yang berjalan **lokal/on-premise**.

---

## 2. Arsitektur Sistem (ringkas)

```
Pengguna → Frontend (Next.js) → Backend (FastAPI, orchestrator)
                                   ├── Embedder e5-base (CPU)
                                   ├── Retriever hybrid: BM25 + FAISS + RRF
                                   │      └── Vector DB: FAISS IndexFlatIP + chunks_meta.json
                                   └── LLM lokal: Ollama (LLaMA 3.1 8B)
                                 → jawaban + rujukan sumber
```

- **Dua pipeline:** *offline* (bangun basis pengetahuan) & *online* (tanya-jawab).
- Semua komponen berjalan lokal; tidak ada layanan pihak ketiga saat query.
- Lokasi kode aktif: `Source code/backend`, `Source code/frontend`,
  launcher `Source code/start.ps1` / `start.bat`.

---

## 3. Pipeline Data (offline)

**Sumber data (resmi UPI):** PPID, PMB, LPPM, Direktorat Pendidikan, dokumen
kepegawaian/regulasi (Biro SDM, Statuta, Pedoman Pendidikan, Kalender Akademik),
serta laman resmi 5 kampus daerah: Cibiru, Sumedang, Tasikmalaya, Purwakarta,
Serang. (Kampus pusat Bumi Siliwangi terwakili lewat unit pusat.)

**Tahapan & alat:**
1. **Scraping** — `requests` (unduh) + `BeautifulSoup`/`lxml` (parse) +
   `trafilatura` (ekstraksi konten utama). Dibatasi ranah situs UPI, normalisasi
   URL, cegah duplikasi.
2. **Ekstraksi PDF** — `PyMuPDF (fitz)`. Bila teks kosong (PDF hasil scan) →
   **fallback OCR**: PaddleOCR (utama) → Tesseract (cadangan).
3. **Cleaning + metadata** — normalisasi, buang header/footer berulang; ekstraksi
   metadata: `doc_id, source, url, title, category, source_type, page, section`.
4. **Chunking** — `RecursiveCharacterTextSplitter` (LangChain), **1.000 karakter,
   overlap 200, minimum 50**. Hasil disimpan sebagai `chunks.jsonl`.

**Kenapa chunking, bukan simpan PDF utuh?** Model punya batas konteks; potongan
kecil membuat pencarian lebih **presisi** (menemukan bagian yang relevan, bukan
seluruh dokumen). Overlap menjaga informasi di perbatasan tidak hilang.

**Angka final (indeks bersih):** **5.726 dokumen → 61.883 potongan.** Sudah
dibuang **21.867 potongan noise nasional** (daftar pendanaan BIMA/Kosabangsa/RKI —
bukan info UPI) via filter `is_noise()` di `ingest_new_dataset.py --upi-only`.

---

## 4. Embedding & Vector Database

- **Model embedding:** `intfloat/multilingual-e5-base` (SentenceTransformers),
  **768 dimensi**. Dipilih karena **multibahasa** (dokumen & pertanyaan dominan
  Bahasa Indonesia), lokal, gratis, muat di perangkat.
- **Konvensi E5:** awalan `passage:` untuk dokumen, `query:` untuk pertanyaan.
- **Normalisasi L2** → inner product = cosine similarity. Batch 32, `float32`.
- **Vector DB:** **FAISS `IndexFlatIP`** (pencarian *eksak*, bukan aproksimasi).
  Dipilih karena skala puluhan ribu vektor → pencarian penuh tetap cepat &
  paling akurat (indeks aproksimatif seperti IVF/HNSW baru perlu untuk jutaan).
- **Berkas indeks** (dibaca backend): `Dataset\_pipeline\index\`
  `faiss.index`, `chunks_meta.json` (selaras baris demi baris), `index_info.json`.

---

## 5. Retrieval

- **Hybrid** = gabungan **BM25 (leksikal)** + **dense (semantik e5)**, disatukan
  dengan **Reciprocal Rank Fusion (RRF, k0=60)**.
- **Kenapa hybrid:** dense murni kadang mengambil dokumen yang vektornya dekat
  tapi maknanya beda (contoh nyata: tanya **UKT** malah dijawab **uang pangkal**).
  BM25 menutup celah pada istilah spesifik (nama prodi, angka biaya); dense
  menutup celah pada parafrase.
- **top_k default = 5** (kandidat 50 per pencari sebelum fusi). *Catatan config:
  backend `.env` sempat diset `DEFAULT_TOP_K=3` oleh helper lain — lihat §11.*

---

## 6. Generasi Jawaban

- **Model utama:** **LLaMA 3.1 8B** via **Ollama** (lokal). **Pembanding:**
  `qwen2.5:7b-instruct`.
- **Kenapa LLaMA & lokal (bukan API GPT/Claude)?**
  - **Privasi** dokumen institusi (tidak dikirim ke pihak ketiga).
  - **Biaya**: gratis → bisa diuji berulang tanpa biaya API (penting untuk
    purwarupa + evaluasi ratusan pertanyaan).
  - **Kemandirian/on-premise**: bisa dijalankan di server kampus sendiri.
  - LLaMA multibahasa cukup baik & efisien untuk hardware terbatas.
- **Grounding ketat:** prompt menginstruksikan model menjawab **hanya** dari
  konteks; menolak bila info tak ada → menekan halusinasi.
- **Parameter:** `temperature = 0.1` (≤0.2 → faktual/deterministik, bukan
  kreatif), `num_ctx = 4096` (muat sistem prompt + ~5 potongan + pertanyaan),
  `keep_alive = 30m` (model tetap panas, hindari cold-load ~35 dtk penyebab 500).
- **Fallback ekstraktif:** bila Ollama gagal, sistem tetap menyajikan potongan
  paling relevan.
- **Short-circuit tanpa LLM:** sapaan (*smalltalk*) & pertanyaan **identitas
  chatbot (5W1H)** dijawab instan dari teks tetap.

**Bagaimana LLM menghasilkan jawaban?** Secara autoregresif — memprediksi token
berikutnya berdasarkan seluruh *prompt* (instruksi grounding + konteks dokumen +
pertanyaan), satu token demi satu, sampai jawaban lengkap.

---

## 7. Evaluasi

Dua tingkat, pada **786 pertanyaan uji bersih** (retrieval) & **50 sampel** (RAGAS),
judge lokal `qwen2.5:7b-instruct`. Skrip: `evaluate_rag.py`,
`evaluate_retrieval_hybrid.py`, `evaluate_ragas.py` (BUKAN notebook 05/06 lama).

**Retrieval** (metrik: Recall@K, Hit@K, Precision@K, MRR, nDCG@K; chunk & doc
level; ground-truth `expected_chunk_ids`). Hasil indeks bersih (doc-level R@5):
BM25 0.418 < Dense 0.458 < **Hybrid 0.477** (MRR: 0.394 < 0.426 < **0.441**).

**RAGAS** (faithfulness, answer relevancy, context precision, context recall).
LLaMA indeks bersih, dense→hybrid: Faithfulness 0.664→**0.697**, Answer Relevancy
0.619→0.617, Context Precision 0.513→**0.585**, Context Recall 0.545→**0.660**.

**Kesimpulan:** *hybrid > dense* konsisten; **retrieval adalah titik ungkit**
kualitas sistem; grounding sehat (tidak perlu fine-tuning).

> Rumus lengkap tiap metrik ada di skripsi BAB 3.6 (Metode Evaluasi).

---

## 8. Tanya-Jawab Sidang (jawaban ringkas untuk pertanyaan dosen)

- **Kenapa topik RAG?** Info UPI tersebar & statis; RAG memberi jawaban akurat,
  bersumber, dan menekan halusinasi (menggabungkan pencarian + LLM).
- **Kenapa lokal, padahal untuk umum?** Untuk privasi data institusi + biaya nol
  saat pengembangan/evaluasi. Untuk produksi, bisa di-*deploy* di **server kampus
  ber-GPU** (tetap on-premise) — itu tahap Saran (BAB V), bukan lingkup purwarupa.
- **Kenapa temperature ≤0.2 & top_k 5?** Temperature rendah → jawaban fokus &
  faktual. top_k 5 → titik tengah antara cukup konteks vs. terlalu banyak dokumen
  (yang menambah noise, memperlambat, & memicu halusinasi).
- **Retrieval "sukses" walau dari 5 dokumen hanya 2 dipakai?** Metrik retrieval
  (Recall/Precision/MRR/nDCG) mengukur relevansi secara objektif; hasil moderat &
  *hybrid memperbaiki dense*. **Keterbatasan yang diakui:** karena top_k tetap,
  sebagian dokumen ikut terbawa sebagai "pelengkap" walau tak dipakai — arah
  perbaikan selanjutnya (mis. ambang skor / top_k adaptif).
- **"Dokumen sudah dipindahkan"?** Path berkas sumber berubah setelah indeks
  dibangun ulang; kini ada endpoint `/api/source/{doc_id}` + tombol "Buka PDF".
- **Sudah diuji ke user asli (sivitas)?** **Belum.** Baru pengujian fungsional
  (black box) + evaluasi kuantitatif oleh peneliti. **Uji ke pengguna nyata
  (UAT/usability) = keterbatasan & future work.** (Jangan klaim sudah diuji user.)
- **Cara menyimpan sesi tanpa login?** Riwayat percakapan disimpan di
  **localStorage browser** (Zustand persist) — per-perangkat, bukan per-akun.
  Login Google + sesi per-akun = future work.
- **Versi mobile?** Sudah diperbaiki (2026-07-03): sidebar tidak lagi menutupi
  layar di HP, tombol navigasi responsif. Belum ada PWA/app native — future work.
- **Kenapa banyak kode tak terpakai?** Sisa iterasi/eksperimen & notebook lama.
  Sudah dipindah ke `D:\Project\RAG_UPI ALT` (2026-07-03). Folder aktif: hanya
  `Source code/backend`, `Source code/frontend`, skrip evaluate & ingest di root.
- **Kenapa di-deploy ke VPS, bukan cukup laptop?** Purwarupa ini berjalan di laptop
  pengembang — saat laptop mati, situs ikut mati. Untuk demo/aksesibilitas umum,
  sistem di-deploy ke **VPS cloud** (Oracle Cloud Free Tier: 4 OCPU ARM, 24 GB RAM,
  gratis permanen) menggunakan **Docker Compose** (Ollama + backend + frontend).
  Alasan pilih VPS: (1) *always-on* tanpa bergantung perangkat pengembang; (2) biaya
  nol (Free Tier); (3) RAM 24 GB cukup untuk model 3–7B parameter di CPU.
  **Catatan:** untuk sidang/demo lokal, tetap pakai laptop + GPU RTX-4050 agar
  respons cepat (~5–10 dtk). VPS dipakai untuk aksesibilitas umum jangka panjang.
- **Kenapa pakai model lebih kecil (qwen2.5:3b) di VPS?** Server VPS tidak punya
  GPU. LLaMA 3.1 8B di CPU = 3–5 menit/jawaban (tidak layak). Model 3B di CPU
  = 40–90 detik — lebih lambat dari GPU, tapi masih dapat digunakan. Trade-off
  kualitas vs. ketersediaan diterima karena VPS hanya untuk aksesibilitas umum,
  bukan demo utama sidang.

---

## 9. Status Terkini (2026-06-30)

- ✅ Skripsi **BAB 2 & BAB 3** sudah ditulis + dihumanisasi (lolos deteksi AI
  lebih baik). Draf: `D:\Documents\KULIAH\...\Draft 1 - Chatbot...docx`.
- ✅ **BAB 4** 4.1–4.3 terisi; **4.4/4.5** menunggu angka final (LLaMA bersih ✅,
  qwen bersih perlu di-run ulang).
- ✅ **Indeks bersih 61.883** aktif di `Dataset\_pipeline\index\`.
- ✅ Aplikasi (backend+frontend) sudah masuk git (branch
  `claude/rag-chatbot-app-and-ux-fixes`).

**Keterbatasan / known issues:**
- **Ollama GPU labil** (RTX-4050 6GB kadang balik ke CPU → LLaMA 8B ~100 dtk →
  timeout/500). Perbaikan: `Source code\fix_ollama_gpu.ps1` + restart Ollama;
  atau pakai model ringan `llama3.2:3b` untuk demo cepat.
- **Sesi = localStorage** (tanpa login).
- **Belum ada versi mobile**; belum ada UAT ke sivitas.
- **Retrieval recall moderat**; sebagian dokumen ter-retrieve tak terpakai.

---

## 10. Cara Menjalankan & Menambah Dataset

**Menjalankan aplikasi (Windows):**
```powershell
cd "D:\Project\RAG_UPI\Source code"
.\start.ps1              # Ollama + backend :8000 + frontend :3000
# cek: http://localhost:8000/health , http://localhost:3000
```
Backend Python: gunakan **Python 3.12**
(`C:\Users\Rajih Nibras M\AppData\Local\Programs\Python\Python312\python.exe`).

**Menambah dataset baru:**
1. Taruh dokumen di `Dataset\<Sumber Baru>\` (PDF/DOCX/XLSX) atau scrape laman baru.
2. Jalankan pipeline ingest: `python ingest_new_dataset.py --upi-only`
   (mengekstrak, chunk, embed, filter noise, rebuild indeks).
3. Pastikan indeks final ada di `Dataset\_pipeline\index\` → **restart backend**.

**Menjalankan evaluasi:** lihat `evaluate_rag.py`, `evaluate_retrieval_hybrid.py`,
`evaluate_ragas.py` (RAGAS butuh Ollama + judge lokal).

---

## 11. Catatan Konfigurasi & Kolaborasi (PENTING)

- **Divergensi config** (perlu diselaraskan sebelum finalisasi skripsi):
  helper lain (Codex, lihat `PROGRESS_FOR_CLAUDE.md`) menyetel backend `.env`
  ke `DEFAULT_TOP_K=3`, `OLLAMA_NUM_CTX=2048`, `LLM_MAX_TOKENS=512`. Skripsi &
  evaluasi bersih memakai **top_k=5, num_ctx=4096**. **Pastikan angka di
  skripsi = angka yang benar-benar dipakai saat run final.**
- **Model tag:** `PROGRESS_FOR_CLAUDE.md` menyebut `llama3.1:8b-instruct-q4_K_M`
  & `qwen3.5:4b-q4_K_M`; sesi lain memakai `llama3.1:8b` & `qwen2.5:7b-instruct`.
  Samakan penyebutan.
- **File handoff antar-AI:** `CODEX_TO_CLAUDE_RAG_UPI_HANDOFF_2026-06-29.md`
  (berisi pembagian tugas frontend: i18n penuh & indikator GPU/CPU didelegasikan
  ke Codex; login Google = future work).
- **Kode tak terpakai** yang perlu dirapikan: notebook lama (`05/06`), folder
  `Claude/` (duplikat, tinggal dihapus), skrip patch/`_build_*`/`_nb*` di root.

---

## 12. Peta File Penting

| Area | Lokasi |
|---|---|
| Backend app | `Source code/backend/app/` (`api/rag_routes.py`, `rag/llm.py`, `rag/vectorstore.py`, `services/rag_service.py`, `core/config.py`) |
| Frontend app | `Source code/frontend/` (`hooks/useChat.ts`, `components/chat/`, `components/settings/SettingsModal.tsx`, `components/citations/SourceInspector.tsx`, `store/`) |
| Launcher | `Source code/start.ps1`, `start.bat`, `fix_ollama_gpu.ps1` |
| Indeks (dibaca backend) | `Dataset/_pipeline/index/{faiss.index,chunks_meta.json,index_info.json}` |
| Korpus & chunk | `Dataset/`, `Dataset/_pipeline/chunked/chunks.jsonl` |
| Ingest/rebuild | `ingest_new_dataset.py` (root) |
| Evaluasi | `evaluate_rag.py`, `evaluate_retrieval_hybrid.py`, `evaluate_ragas.py` + hasil di `knowledge_layer/eval/` |
| Draf skripsi | `D:\Documents\KULIAH\...\Draft 1 - Chatbot...docx` |
| Bahan skripsi tambahan | `D:\Project\RAG_UPI\Skripsi\*.md` |
