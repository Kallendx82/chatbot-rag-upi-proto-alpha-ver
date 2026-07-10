# Panduan Persiapan Sidang — Chatbot RAG UPI
Dokumen ini merangkum seluruh detail teknis yang perlu dikuasai untuk menjawab pertanyaan dosen pembimbing & penguji. Disusun dari kode dan konfigurasi sistem yang sebenarnya.

---

## A. ALUR BESAR SISTEM (kuasai ini dulu — kerangka semua jawaban)

Sistem punya **dua fase terpisah**:

1. **Fase OFFLINE (membangun basis pengetahuan)** — dilakukan sekali di awal, diulang kalau dokumen UPI berubah:
   `Scraping dokumen → Ekstraksi teks (+ OCR cadangan) → Pembersihan → Chunking → Embedding → Simpan ke FAISS`

2. **Fase ONLINE (menjawab pertanyaan)** — berjalan tiap pengguna bertanya:
   `Pertanyaan → Embedding pertanyaan → Retrieval (dense+BM25+RRF) → Dedupe → Susun prompt grounded → LLM generate → Jawaban + sitasi`

Kalimat kunci: **"Retrieval yang menentukan kualitas. LLM hanya sebaik dokumen yang berhasil diambil."**

---

## B. PENGUMPULAN DATA (dari mana, bagaimana)

**Sumber data (semua dokumen PUBLIK resmi UPI, tanpa autentikasi):**
- PPID (Pejabat Pengelola Informasi & Dokumentasi) — peraturan, laporan kinerja, kebijakan
- PMB (Penerimaan Mahasiswa Baru) — syarat, prosedur, biaya seleksi
- LPPM (Lembaga Penelitian & Pengabdian) — dokumen penelitian/pengabdian
- Direktorat Pendidikan — pedoman & kebijakan akademik
- 5 kampus daerah: Cibiru, Sumedang, Tasikmalaya, Purwakarta, Serang
- Dokumen kepegawaian & regulasi institusi

**Cara ambil: web scraping.** Tantangan nyata yang dihadapi (siap ceritakan — ini bukti kamu paham lapangan):
- Sebagian dokumen sudah dihapus/tidak bisa diakses
- Proteksi **Cloudflare** di beberapa laman → butuh pendekatan browser (CDP)
- Struktur tiap unit berbeda (PMB ≠ Direktorat) → scraper harus disesuaikan per sumber
- Sebagian PDF hasil **pindaian** (scan) tanpa lapisan teks → butuh OCR

**Format:** PDF, Word, Excel, HTML.

**Statistik akhir:** 5.726 dokumen → **61.883 potongan (chunk)** terindeks (Tabel 4.1 skripsi). *(Catatan: index untuk evaluasi retrieval memuat 56.833 chunk — perbedaan kecil karena penyaringan chunk low-content; kalau ditanya, sebut angka sesuai tabel yang kamu rujuk.)*

**Kenapa dokumen publik saja?** Etika & privasi — tidak menyentuh SIAK/data mahasiswa/gerbang pembayaran. Semua bisa diunduh tanpa login.

---

## C. PREPROCESSING (sebelum masuk vektor DB)

1. **Ekstraksi teks**: PyMuPDF untuk PDF. Kalau gagal (dokumen pindaian) → **OCR cadangan**: PaddleOCR utama, Tesseract cadangan.
   - Kenapa OCR cuma cadangan? Karena mayoritas PDF UPI dibuat digital (teksnya bisa langsung diekstrak); OCR hanya dipicu saat ekstraksi langsung gagal → hemat waktu & lebih akurat.

2. **Pembersihan (cleaning)**: buang header/footer berulang (derau paling sering, bukan karakter aneh), normalisasi format.

3. **Chunking**: `RecursiveCharacterTextSplitter`, **ukuran 1.000 karakter, overlap 200 karakter**.
   - Kenapa 1.000? Terlalu besar → satu chunk campur banyak topik, makna kabur, pencarian kehilangan fokus. Terlalu kecil → konteks terputus.
   - Kenapa overlap 200? Agar informasi di **perbatasan** antar-chunk tidak hilang terpotong.

4. **Metadata per chunk**: judul, sumber, halaman, kategori, doc_id → untuk keterlacakan (sitasi) & filtering.

---

## D. VEKTOR DATABASE (apa yang terjadi di dalamnya)

**Embedding — mengubah teks jadi angka:**
- Model: **`intfloat/multilingual-e5-base`**, output **vektor 768 dimensi**.
- Kenapa multilingual? Dokumen UPI & pertanyaan didominasi Bahasa Indonesia; model ini paham bahasa Indonesia dengan baik.
- Aturan awalan E5: prefix `passage:` untuk dokumen, `query:` untuk pertanyaan → menempatkan keduanya di ruang makna yang sama supaya pencocokan lebih tepat.
- Semua vektor **dinormalisasi** (panjang = 1).

**Penyimpanan — FAISS:**
- Jenis indeks: **`IndexFlatIP`** (Inner Product, pencarian menyeluruh/exhaustive).
- Karena vektor dinormalisasi, **inner product = cosine similarity**. Ini kunci: kesamaan makna dihitung sebagai sudut antar-vektor.
- Kenapa Flat (menyeluruh), bukan aproksimasi (IVF/HNSW)? Jumlah vektor masih puluhan ribu (~60rb) → pencarian penuh tetap cepat DAN paling akurat. Indeks aproksimasi baru perlu kalau sudah jutaan vektor.

**Tiga berkas yang dijaga selalu selaras:**
1. berkas indeks FAISS (vektor)
2. berkas metadata (teks chunk + keterangan)
3. berkas info indeks (model embedding + jumlah vektor)
- Backend memeriksa kecocokan model embedding saat startup → kalau model saat membangun index ≠ model saat menjawab, langsung ketahuan (via `/health`), tidak "diam-diam salah".

**Cara mengelola:** pipeline offline bisa dijalankan ulang saat dokumen UPI diperbarui, tanpa membangun ulang seluruh sistem.

---

## E. KONSEP RETRIEVAL (bagaimana bekerja) — INI PALING SERING DITANYA

Sistem pakai **hybrid retrieval** = gabungan 2 pendekatan:

1. **Dense (semantik)**: pertanyaan → vektor → cari chunk dengan cosine similarity tertinggi. Kuat untuk makna/parafrase.
2. **BM25 (leksikal/kata kunci)**: skor berdasarkan frekuensi kata + kelangkaan kata + panjang dokumen. Kuat untuk istilah spesifik (nama prodi, nomor surat, angka biaya).

**Kenapa hybrid, bukan dense saja?** Kasus nyata: saat ditanya **UKT per semester**, dense murni mengambil chunk tentang **uang pangkal** — mirip secara vektor, tapi salah topik. BM25 menambal ini dengan pencocokan kata kunci persis.

**Penggabungan: Reciprocal Rank Fusion (RRF)**, konstanta k0=60.
- RRF menggabung **peringkat** (bukan skor mentah), rumus `RRF(d) = Σ 1/(k0 + rank_r(d))`. Chunk yang muncul di peringkat atas di salah satu/kedua metode dapat skor gabungan tinggi.
- Kenapa RRF? Tidak perlu menyetel bobot antar-metode yang rumit.

**Parameter operasional:**
- `top_k = 5` (dokumen yang ditampilkan sebagai konteks/sitasi).
- **Oversample 3×** (ambil ~15-50 kandidat) → **dedupe near-duplicate** (banyak PDF UPI berbagi paragraf boilerplate identik, mis. "Persyaratan Akademik" muncul di 50+ dokumen) → potong ke top_k. Efeknya: pengguna melihat 5 chunk BERBEDA, bukan 5 salinan paragraf sama.
- `candidates = 50` per retriever sebelum fusi.

**Kenapa top_k=5?** Hasil percobaan: <5 → konteks terlalu sempit, model kekurangan bahan → malah berhalusinasi. >10 → waktu respons lama + banyak dokumen tak relevan ("berisik") → jawaban melenceng. 5 = titik tengah kecukupan konteks vs kecepatan vs memori GPU.

**Keterbatasan yang jujur diakui (siap disebut):** karena top_k tetap, kadang ada chunk tak relevan ikut sebagai "pengisi kuota". Contoh: pertanyaan keberadaan seseorang dijawab dengan nama dari lampiran pendanaan institusi lain. Perbaikan lanjutan: re-ranking / ambang skor minimum.

---

## F. GENERASI JAWABAN OLEH LLM (bagaimana bisa menjawab)

**Model utama: LLaMA 3.1 8B-Instruct-q4_K_M**, dijalankan **lokal via Ollama**.

**Alur generasi:**
1. Ambil **3 chunk teratas** (bukan 5 penuh — sengaja lebih sedikit untuk generasi). Kenapa? Model 7-8B mudah **mencampur angka** dari banyak baris mirip (mis. tabel UKT banyak prodi); 3 teratas hampir selalu memuat jawaban tepat. Sitasi tetap tampilkan 5 di UI.
2. Susun **prompt grounded**: instruksi sistem (8 aturan) + langkah penalaran internal + contoh gaya (few-shot, hanya untuk gaya BUKAN fakta) + SUMBER bernomor + pertanyaan.
3. Model menyusun jawaban HANYA berdasarkan SUMBER, dengan sitasi `[1]`, `[2]`.

**8 aturan prompt penting** (lihat 3.3.8 skripsi). Yang paling krusial:
- Aturan #2: jangan mengarang angka/tanggal/kebijakan yang tak ada di SUMBER (anti-halusinasi).
- Aturan #8: untuk angka biaya/UKT, gunakan HANYA sumber yang nama prodinya PERSIS sama — jangan campur antar-prodi. (Ditambahkan setelah menemukan kasus nyata pencampuran angka.)
- Aturan #4: kalau tak ada info relevan → tolak sopan, sarankan hubungi unit UPI.

**Parameter inferensi:**
- `temperature = 0.1` (rendah) → jawaban fokus & tidak melebar. Semakin tinggi temperature, semakin lebar/kreatif; penelitian ini utamakan jawaban ringkas & akurat.
- `num_ctx = 4096` (jendela konteks), `max_tokens = 1024`.
- `keep_alive = 30m` → model tetap "hangat" di memori.

**"Grounding"** = mengikat jawaban pada dokumen. Kalau tak ada rujukan → model dirancang menolak, bukan memaksakan jawaban (yang berujung halusinasi).

**Mekanisme cadangan ekstraktif:** kalau LLM gagal merespons (mis. timeout) padahal dokumen sudah ada → sistem tetap sajikan dokumen paling relevan (belum diolah jadi kalimat) supaya layanan tak berhenti total.

**Jalan pintas cerdas (tanpa retrieval):**
- Sapaan/basa-basi ("halo", "terima kasih") → balasan perkenalan singkat.
- Pertanyaan tentang identitas chatbot ("kamu siapa", "bisa apa") → jawaban deskripsi diri tetap. Ini mencegah retrieval mengambil dokumen acak lalu menolak dengan bingung.

---

## G. TENTANG "TRAINING" — PENTING, sering disalahpahami penguji

**TIDAK ADA pelatihan/fine-tuning model.** Ini poin yang harus tegas:
- LLaMA & Qwen dipakai **apa adanya (pre-trained)**, TIDAK dilatih ulang.
- Pengetahuan domain UPI **TIDAK dimasukkan ke bobot model** — melainkan **disuplai saat inferensi** lewat mekanisme RAG (dokumen ditaruh di prompt sebagai konteks).
- Keunggulan pendekatan ini: (1) tak perlu GPU besar & dataset pelatihan; (2) update pengetahuan = cukup update dokumen di index, tanpa latih ulang; (3) jawaban terikat sumber → bisa dilacak & minim halusinasi.
- Jadi kalau ditanya "datasetnya untuk melatih apa?" → jawab: **dataset 1.880 pertanyaan itu untuk EVALUASI, bukan pelatihan.** Model tidak pernah "belajar" dari situ.

**"Memasukkan data"** = proses INDEXING (fase offline di bagian C-D), bukan training.

---

## H. EVALUASI RAGAS (bagaimana caranya)

**Dua dimensi terpisah** (karena mode kegagalannya beda):

**1. Retrieval (GRATIS, tanpa LLM judge)** — dijalankan pada **seluruh 1.880 pertanyaan**:
- Metrik: Recall@K, Precision@K, Hit@K, MRR, nDCG@K.
- Dua tingkat: chunk-level (potongan tepat) & document-level (dokumen sumber benar).
- Bandingkan 3 strategi: dense, BM25, hybrid.

**2. Generasi (RAGAS, BERBAYAR via judge)** — pada **sampel 200 pertanyaan/model**:
- 4 metrik: **faithfulness** (kesetiaan ke konteks / anti-halusinasi), **answer relevancy** (kesesuaian jawaban ke pertanyaan), **context precision** (ketepatan urutan konteks), **context recall** (kelengkapan konteks vs jawaban acuan).
- Judge: **Claude Haiku 4.5** (via API).
- Sampel dipilih acak proporsional, **seed tetap (42)** → set soal IDENTIK untuk LLaMA & Qwen (perbandingan adil).

**Dataset evaluasi:** 1.880 pasangan Q&A grounded, dibangun dari korpus, per-departemen. Tiap pertanyaan punya jawaban acuan + daftar chunk acuan (expected chunk).

---

## I. HASIL & MENGAPA SEGITU (siapkan pembelaan angka)

**Retrieval (hybrid, tingkat dokumen):** R@1=0,402 · R@5=0,641 · R@10=0,713 · MRR=0,511.
**Retrieval (hybrid, tingkat chunk):** R@1=0,351 · R@5=0,594 · MRR=0,461.
Hybrid **konsisten menang** atas dense/BM25 di semua K. (Hybrid vs dense: Recall@5 chunk +14%, MRR +15%.)

**Generasi RAGAS (overall):**
| Metrik | LLaMA 3.1 8B | Qwen2.5 7B |
|---|---|---|
| Faithfulness | 0,715 | 0,722 |
| Answer Relevancy | 0,601 | **0,699** |
| Context Precision | **0,655** | 0,627 |
| Context Recall | **0,758** | 0,676 |

**Kenapa Recall@1 "cuma" 0,3-0,4 (di bawah 0,5)?** — INI PASTI DITANYA.
- Baseline acak menemukan 1 chunk benar dari 56.833 = 0,0000176 (0,00176%). Sistem 0,30-0,40 = **~17.000× lebih baik dari acak**. Wajar untuk skala korpus besar.
- Metrik R@1 sangat ketat (harus tepat di peringkat #1 dari puluhan ribu). Sistem produksi pakai top_k=5, jadi performa nyata lebih dekat ke R@5 (0,59-0,64).
- Nilai naik tajam ke R@10 → sistem sering menemukan dokumen benar, hanya tidak selalu di posisi #1.

**Kenapa answer relevancy ~0,60-0,70 (ada ruang perbaikan)?** Keterbatasan top_k tetap → konteks tak relevan kadang ikut → memengaruhi fokus jawaban.

---

## J. KENAPA BEDA DENGAN PENELITIAN TERDAHULU

Penelitian terdahulu di kajian pustaka (Maryamah dkk. Recall 86%, Aliphadji dkk. Recall 95%) angkanya lebih tinggi KARENA:
1. **Korpus jauh lebih kecil** — mereka pakai ratusan-ribuan chunk (mis. dari 1 booklet PMB), penelitian ini **~60.000 chunk** dari puluhan sumber. Makin besar korpus, makin sulit R@1 tinggi.
2. **Metrik lebih longgar** — sebagian pakai topic-level match, penelitian ini pakai exact chunk-id match yang lebih ketat.
3. **Model berbayar** — mereka pakai GPT-3.5/OpenAI embeddings; penelitian ini **100% lokal & open-weight**.
Jadi bukan "lebih buruk" — beda skala & kondisi eksperimen. Ini justru **kontribusi**: benchmark pada korpus besar & realistis.

---

## K. MASALAH TEKNIS YANG PERNAH TERJADI (jujur = kredibel)

**Kenapa sering Error 500 padahal sebelumnya bisa?**
- Penyebab: **cold-load model** (~35 detik) saat model belum di memori → request timeout → HTTP 500.
- Penyebab kedua: `num_ctx` sempat diset 8192 → model 7B **tumpah dari VRAM 6GB ke CPU** → sangat lambat → timeout → 500.
- **Solusi:** `num_ctx=4096` (muat 7B di 6GB VRAM + prompt + 5 chunk), + `keep_alive=30m` (model tetap hangat), + frontend auto-retry transient error dengan pesan ramah (bukan "HTTP 500" mentah).

**Kenapa sering tidak bisa menjawab pertanyaan?**
- Akar masalah biasanya di **retrieval**, bukan LLM — kalau chunk yang tepat tidak terambil, LLM tak punya bahan.
- Juga: aturan grounding ketat → model memilih menolak daripada mengarang (trade-off yang disengaja demi akurasi).
- Perbaikan yang sudah dilakukan: hybrid retrieval + dedupe + jalan pintas sapaan/identitas + prompt UKT per-prodi.

---

## L. KEPUTUSAN DESAIN (kenapa begini, bukan begitu)

**Kenapa LOKAL, bukan CLOUD?**
1. **Privasi data** institusi — semua pemrosesan di lingkungan sendiri, tak kirim data keluar.
2. **Biaya** — model lokal bisa diuji berulang kali tanpa biaya API (penting untuk purwarupa yang di-test terus).
3. **Kemandirian operasional** — tak bergantung layanan pihak ketiga.

**Kenapa sekarang malah pakai API Claude, padahal awalnya mau lokal semua?**
- Claude **BUKAN** komponen sistem chatbot. Sistem tetap 100% lokal (LLaMA/Qwen via Ollama).
- Claude Haiku 4.5 dipakai **hanya sebagai JUDGE evaluasi RAGAS** — pihak ketiga independen untuk menilai, bukan bagian produk.
- Awalnya evaluasi direncanakan pakai judge lokal (qwen2.5), tapi diganti ke Claude karena alasan di bawah.

**Kenapa Claude sebagai judge?**
1. **Menghindari self-preference bias** — judge harus BEDA dari model yang dinilai. Kalau qwen2.5 jadi judge sekaligus model yang dievaluasi → bias menilai diri sendiri lebih tinggi.
2. Kualitas penilaian **lebih konsisten** dari model lokal kecil.
3. **Terjangkau** — Haiku 4.5 murah ($1/$5 per juta token), total evaluasi ~$8 untuk 400 sampel.

**Kenapa LLaMA sebagai model utama, bukan Qwen (yang answer relevancy-nya lebih baik)?**
1. Hasilnya **hampir seri** — Qwen menang 2 metrik, LLaMA menang 2 metrik. Tidak ada pemenang mutlak.
2. LLaMA unggul di **context recall (0,758 vs 0,676)** — aspek yang **lebih krusial secara arsitektural** untuk RAG: recall rendah = informasi hilang SEBELUM sempat dijawab (masalah lebih fundamental daripada relevansi).
3. **Konsistensi framing skripsi** — Bab I/III dibangun di sekitar LLaMA (privasi, lokal). Mengganti model utama = menulis ulang justifikasi teoritis, risiko > manfaat.
4. Qwen tetap berperan sebagaimana dirancang: **model pembanding**, bukan pengganti.
- (Saran untuk penelitian lanjutan: uji dengan sampel lebih besar sebelum memutuskan ganti model.)

**Kenapa tidak diujicobakan ke pihak UPI pusat?**
1. **Ruang lingkup purwarupa (prototype)** — penelitian dibatasi pada pembangunan & evaluasi purwarupa, BUKAN deployment produksi (tertulis di batasan penelitian Bab I).
2. **Etika & keamanan data** — tidak integrasi ke sistem internal berautentikasi (SIAK, dll.).
3. **Keterbatasan sumber daya & waktu** — evaluasi jangka panjang kepuasan pengguna pasca-produksi di luar cakupan.
4. Evaluasi dilakukan **kuantitatif & objektif** (retrieval + RAGAS) yang lebih terukur & reproducible daripada uji subjektif terbatas.
- Ini **bukan kelemahan**, tapi batasan lingkup yang wajar & disengaja untuk skripsi S1.

---

## M. SPESIFIKASI TEKNIS RINGKAS (hafalkan angka-angka ini)

| Komponen | Detail |
|---|---|
| Sumber data | PPID, PMB, LPPM, Direktorat Pendidikan, 5 kampus daerah + kepegawaian |
| Dokumen / chunk | 5.726 dokumen → 61.883 chunk (index eval: 56.833) |
| Chunking | 1.000 karakter, overlap 200, RecursiveCharacterTextSplitter |
| Embedding | multilingual-e5-base, 768 dimensi, prefix passage/query, dinormalisasi |
| Vector DB | FAISS IndexFlatIP (= cosine similarity) |
| Retrieval | Hybrid dense+BM25, RRF (k0=60), top_k=5, candidates=50, oversample 3× + dedupe |
| LLM utama | LLaMA 3.1 8B-Instruct-q4_K_M via Ollama |
| LLM pembanding | Qwen2.5 7B-Instruct |
| Parameter LLM | temperature=0,1, num_ctx=4096, max_tokens=1024, keep_alive=30m |
| Generasi | 3 chunk teratas ke LLM (sitasi tampilkan 5) |
| Backend | FastAPI (Python 3.12), Uvicorn, Pydantic |
| Frontend | Next.js 14, React 18, TypeScript, Zustand, Tailwind, Radix UI |
| Eval retrieval | 1.880 soal, Recall@K/Precision@K/MRR/nDCG@K |
| Eval generasi | RAGAS 4 metrik, 200 sampel/model, judge Claude Haiku 4.5 |
| Deployment | Docker Compose (backend + frontend + Ollama) |
| Perangkat | Laptop GPU RTX 4050, Windows 11 |

---

## N. ANTISIPASI PERTANYAAN JEBAKAN

- **"Ini AI-nya belajar dari dokumen UPI?"** → Tidak. Tidak ada training. Dokumen disuplai saat inferensi via RAG (di prompt). Bobot model tidak berubah.
- **"Kenapa jawabannya kadang salah/menolak?"** → Umumnya retrieval tidak mengambil chunk tepat, atau grounding ketat memilih menolak daripada mengarang. Trade-off disengaja demi akurasi.
- **"Kok pakai Claude, katanya lokal?"** → Claude hanya juri evaluasi eksternal, bukan bagian sistem. Chatbot tetap 100% lokal.
- **"Kenapa nilai retrieval di bawah 0,5?"** → Metrik ketat pada korpus 56rb chunk; ~17.000× lebih baik dari acak; produksi pakai top_k=5 (R@5 ~0,6).
- **"Kenapa tidak fine-tuning biar lebih akurat?"** → Fine-tuning butuh GPU besar + dataset besar, dan membekukan pengetahuan (susah update). RAG lebih tepat untuk domain yang dokumennya sering berubah + bisa dilacak sumbernya.
- **"Kenapa multilingual-e5-base, bukan model lain?"** → Dukungan Bahasa Indonesia baik, ukuran efisien (768-dim), mendukung prefix query/passage E5.
- **"Validitas 200 sampel dari 1.880?"** → Sampling acak dengan seed tetap; margin error kecil untuk rata-rata; set identik antar-model menjamin perbandingan adil. Retrieval tetap dievaluasi penuh 1.880.

---

*Kuasai bagian A (alur besar) + E (retrieval) + F (generasi) + G (bukan training) + L (keputusan desain) lebih dulu — itu inti yang paling sering digali penguji.*
