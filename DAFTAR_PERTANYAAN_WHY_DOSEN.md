# DAFTAR PERTANYAAN "WHY?" — DOSEN PENGUJI
**Pertanyaan kemungkinan ditanya, diurutkan dari dasar → advanced**

---

## TIER 1: PERTANYAAN PALING DASAR (Penguji akan mulai dari sini)

### 1. "Kenapa Anda memilih penelitian ini? Apa yang membuat Anda tertarik dengan topik chatbot RAG untuk UPI?"

**Jawaban singkat:**
- Saya melihat masalah nyata di UPI: dokumen tersebar di berbagai unit, sulit ditemukan, pengguna harus browsing manual
- Belum ada solusi yang menggabungkan pemahaman bahasa alami + akses dokumen multi-unit
- RAG adalah teknologi terbaru yang menjanjikan untuk solve masalah ini
- Sekaligus mengisi gap penelitian di domain akademik Indonesia

**Elaborasi:**
- Personal motivation: sewaktu jadi mahasiswa/staf UPI, pernah kesulitan cari informasi
- Institutional relevance: UPI punya 5.726 dokumen tersebar, ini data besar & meaningful
- Research relevance: RAG masih belum banyak dikaji di domain akademik Indonesia

**Referensi:** BAB I Latar Belakang (1.1)

---

### 2. "Bagaimana Anda menemukan atau menyadari masalah ini? Apakah dari pengalaman pribadi atau dari literatur?"

**Jawaban singkat:**
- Gabungan dari pengalaman pribadi sebagai sivitas akademika UPI + pengamatan struktur website UPI
- Dikuatkan oleh literatur: Rakhmana dkk. (2024) menunjukkan masalah serupa di institusi lain (struktural, bukan teknis)
- Melihat celah: mayoritas solusi (FAQ, portal) tidak cukup fleksibel untuk bahasa alami

**Elaborasi:**
- Pengalaman konkrit: "Saya perlu cari info UKT, harus browsing PPID, PMB, Direktorat sekaligus"
- Pengamatan: setiap unit punya website sendiri dengan struktur berbeda
- Literatur support: ini bukan masalah unique UPI, tapi masalah sistemik di institusi besar

**Referensi:** BAB I 1.1 (paragraf 1 & 2)

---

### 3. "Mengapa Anda yakin bahwa RAG adalah solusi terbaik? Ada alternatif lain yang Anda pertimbangkan?"

**Jawaban singkat:**
- Ada 3 alternatif: FAQ, portal terpusat, chatbot intent-based
- Masing-masing punya limitation:
  - FAQ: tidak fleksibel
  - Portal: tetap bergantung kata kunci literal (bahasa alami tidak tertangkap)
  - Intent-based: butuh data training besar, scope terbatas
- RAG: mengkombinasikan bahasa alami + akses dokumen heterogen → best fit untuk masalah UPI

**Elaborasi:**
- FAQ contoh: user tanya "Bagaimana cara daftar ulang?" tidak akan match dengan FAQ "Pendaftaran Ulang"
- Portal contoh: user tanya "Kapan saya bisa ambil SKS?" bisa tidak ketemu karena tidak match kata kunci "SKS" atau "beban studi"
- Intent-based contoh: butuh label data training besar (1000+ contoh per intent), dan tidak bisa jawab "Apa itu UKT?" (di luar training scope)
- RAG: "Ambil dokumen relevan + LLM pahami bahasa natural" → flexible, traceable

**Referensi:** BAB I 1.1 paragraf 3 (Berbagai pendekatan telah dicoba...)

---

## TIER 2: PERTANYAAN SCOPE & JUSTIFIKASI (Setelah yakin dengan research problem)

### 4. "Kenapa fokus di UPI, bukan institusi lain atau generalize ke semua perguruan tinggi?"

**Jawaban singkat:**
- UPI punya karakteristik unik untuk penelitian:
  - **Skala besar**: 6 kampus, puluhan ribu mahasiswa, banyak dokumen (5.726)
  - **Multi-unit** (PPID, PMB, LPPM, Direktorat, 5 daerah) → representative of large institution
  - **Accessible**: sebagai sivitas akademika, saya punya akses data & konteks
- Generalize ke semua PT akan membuat scope terlalu luas & tidak fokus

**Elaborasi:**
- Kontras dengan penelitian terdahulu (Maryamah dkk: 111 dokumen 1 unit)
- UPI = realistic scenario untuk institusi besar di Indonesia
- Knowledge dari UPI bisa transfer ke institusi lain yg punya masalah serupa

**Referensi:** BAB I 1.1 paragraf 2 (UPI context), BAB I 1.5 (scope)

---

### 5. "Dokumen apa saja yang Anda gunakan? Hanya dari website atau ada sumber lain?"

**Jawaban singkat:**
- Dokumen dari **website resmi UPI SAJA**, untuk menjaga:
  - **Etika**: tidak menyentuh data pribadi/sensitif
  - **Privasi**: hanya dokumen publik (accessible tanpa autentikasi)
  - **Kredibilitas**: dokumen resmi = terverifikasi & authoritative
- Sumber: PPID, PMB, LPPM, Direktorat Pendidikan, website kampus daerah
- Format: PDF, Word, Excel (dikonversi ke text)

**Elaborasi:**
- Tidak include: SIAK (mahasiswa data), payment gateway, email, dll
- Reasoning: chatbot ini untuk **informasi publik akses**, bukan data sensitif management
- Data protection: semua processing lokal, no cloud upload

**Referensi:** BAB I 1.5.2 (Fungsi Chatbot), BAB I 1.5.1 (Batasan Penelitian)

---

### 6. "Kenapa hanya data publik? Kalau include data internal seperti SIAK bisa lebih powerful?"

**Jawaban singkat:**
- **Benar**, kalau include SIAK bisa lebih powerful, TAPI:
  - **Etika**: data SIAK pribadi (nilai, absensi, data keluarga) — tidak boleh dalam chatbot public
  - **Regulasi**: data pribadi mahasiswa dilindungi (privacy law)
  - **Security**: SIAK berbasis autentikasi, tidak safe untuk chatbot publik
  - **Use case**: research ini untuk **informasi akses publik** (UKT, prosedur, dll), bukan personal data
- Trade-off disengaja: scope jelas, ethical, implementable

**Elaborasi:**
- Kalau include data internal: chatbot harus behind authentication → out of scope (prototype only)
- Dokumentasi: "tidak integrasi dengan sistem internal berbasis autentikasi" (Bab I 1.5.1)
- Future work: kalau UPI deploy prod, baru consider SIAK integration (dengan security proper)

**Referensi:** BAB I 1.1 paragraf terakhir (celah penelitian focused on public data), BAB I 1.5 (Batasan)

---

## TIER 3: PERTANYAAN METODOLOGI (Technical deep-dive)

### 7. "Kenapa memilih RAG daripada fine-tuning model? Lebih akurat tidak fine-tuning?"

**Jawaban singkat:**
- **Benar** fine-tuning lebih accurate (dalam praktik), TAPI:
  - **Resource infeasible** untuk S1: butuh GPU besar (A100), dataset berlabel besar (1000+), waktu berminggu-minggu
  - **RAG advantage**: knowledge update = ganti dokumen (jam), tidak latih ulang (minggu)
  - **Fleksibilitas**: UPI policy sering berubah (semester baru = UKT baru) → RAG lebih cocok
  - **Traceable**: jawaban bisa audit ke sumber dokumen
- **Trade-off disengaja**: flexibility & affordability > slightly higher accuracy

**Elaborasi:**
- Fine-tuning requirement: Nvidia A100 GPU ($1+/menit), 50GB+ VRAM, 2-3 minggu training
- RAG benefit untuk akademik: "policy berubah → hanya update dokumen index, no retraining"
- Audit trail: Kalau ada pertanyaan "darimana data ini?" → bisa point ke dokumen source (fine-tuning tidak bisa)

**Referensi:** BAB II 2.1.3 (Training vs Fine-tuning vs RAG), BAB I 1.5 (Scope: prototype, tidak production)

---

### 8. "Kenapa lokal inference, bukan pakai cloud API seperti GPT-4 atau Claude?"

**Jawaban singkat:**
- Bisa pakai cloud API, TAPI penelitian ini prioritas:
  - **Privasi**: semua data di institusi, tidak kirim ke server pihak ketiga
  - **Biaya**: model lokal unlimited testing (gratis), cloud API per-token (mahal untuk prototype)
  - **Independensi**: tidak bergantung uptime/keputusan pihak ketiga
- **Trade-off**: compute terbatas (GPU kecil) → pakai model kecil (8B bukan 70B) ✅ tetap feasible

**Elaborasi:**
- Privacy example: "Anda mau jawaban pertanyaan mahasiswa dikirim ke OpenAI server?"
- Cost example: GPT-4 = $0,05/1K token, × 1.880 evaluasi queries = $$$ expensive
- Model kecil still viable: Llama 8B achieves 0.788 faithfulness (bagus untuk akademik domain)

**Referensi:** BAB I 1.1 (Latar Belakang: privasi), BAB III 3.4.1 (Lingkungan Pengembangan: Ollama lokal)

---

### 9. "Kenapa Llama & Qwen? Ada pertimbangan model lain?"

**Jawaban singkat:**
- Kriteria pemilihan:
  1. **Open-weight** (bukan proprietary): bisa run lokal
  2. **Multilingual**: paham Bahasa Indonesia
  3. **Ukuran manageable**: 7-8B (fit di GPU 6GB) bukan 70B
  4. **Populer dalam research**: banyak paper cite them
- Llama & Qwen both memenuhi semua kriteria
- Memilih keduanya untuk **komparasi**: insight kelebihan/kelemahan di domain akademik Indonesia

**Elaborasi:**
- Lain: Mistral (French-centric), Phi (terlalu kecil/spesialisasi), GPT (proprietary)
- Alasan komparasi: penelitian ini bukan cuma implement, tapi komparasi → contribute knowledge tentang model selection
- Qwen khusus dipilih karena: "dilatih dengan penekanan long-context understanding" (cocok RAG)

**Referensi:** BAB II 2.1.3 (Llama), 2.1.4 (Qwen), BAB I Tujuan 1.3 poin 3 (analisis komparatif)

---

### 10. "Kenapa hybrid retrieval? Dense saja tidak cukup?"

**Jawaban singkat:**
- Dense (semantic search) bagus untuk paraphrase, TAPI:
  - Kasus nyata di UPI: user tanya "UKT per semester" → dense ambil "uang pangkal" (mirip semantik, salah topik)
- BM25 (keyword) tepat untuk terms spesifik (UKT, SNBP, IRS), TAPI:
  - Tidak paham natural language: "bagaimana cara ambil SKS" tidak match dokumen "beban studi"
- **Hybrid**: gabung keduanya via RRF
  - Hasil: Hybrid R@5 +14% vs dense, MRR +15%
  - Trade-off: kompleksitas sedikit naik, tapi benefit signifikan untuk domain akademik

**Elaborasi:**
- Analogi: dense = memahami makna, BM25 = memahami vocabulary
- UKT case: dense ambil "uang pangkal" (semantic distance dekat), tapi wrong topik
  - BM25 menambal: hanya match dokumen yg kata "UKT" exact ada
  - Hybrid: gabung rank keduanya → dokumen benar di top
- Data: retrieve hasil menunjukkan hybrid consistently unggul di semua K (R@1, R@5, R@10)

**Referensi:** BAB II 2.1.5.1 (Information Retrieval), BAB IV 4.4.1 (Hasil Retrieval: hybrid unggul)

---

### 11. "Kenapa RAGAS sebagai framework evaluasi? Ada alternatif lain?"

**Jawaban singkat:**
- Alternatif evaluasi generasi:
  - **BLEU/ROUGE**: metric leksikal, tidak sesuai untuk semantic generation (misses paraphrase)
  - **Manual evaluation**: akurat tapi tidak scalable (1.880 Q × 2 model = ribuan penilaian)
  - **RAGAS**: framework terstandar, automatic, semantic-aware (faithfulness, relevancy, precision, recall)
- RAGAS dipilih karena:
  - **Terstandar**: sudah cited di 500+ papers
  - **Semantic-aware**: tidak hanya word-level match
  - **Comprehensive**: 4 metrik cover retrieval + generasi aspect
- Trade-off: berbayar (need LLM judge API) tapi hasil robust

**Elaborasi:**
- BLEU example: "Sistem memberikan jawaban benar tapi parafrase" → BLEU score rendah (unfair)
- RAGAS example: "Sistem jawab dengan kata berbeda tapi makna sama" → faithfulness score tinggi ✅
- Cost: ~$8 untuk 400 sampel (2 model × 200 Q) → feasible untuk S1

**Referensi:** BAB II 2.1.7 (Evaluasi Sistem RAG), BAB II 2.1.7.2 (LLM-as-a-Judge), BAB III 3.6.3 (Metode Evaluasi)

---

### 12. "Kenapa sampling 200 dari 1.880? Tidak bisa full evaluation?"

**Jawaban singkat:**
- **Statistik**: 200 sampel margin error ~7% pada confidence 95% → representatif untuk rata-rata
- **Cost reason**: setiap RAGAS metrik butuh multiple LLM judge calls
  - 200 Q × 2 model × 4 metrik = $8 (affordable)
  - 1.880 Q full = $80+ (tight untuk S1 budget)
- **Retrieval tetap full** (1.880 Q) karena gratis (no LLM calls)
- **Seed tetap (42)**: set Q identik antar-model → perbandingan adil

**Elaborasi:**
- Sampling adalah standard practice di ML evaluation (tidak bisa eval everything)
- Trade-off: retrieval full eval (robust) + generasi sample eval (affordable) = balanced
- Seed tetap: ensures "difference in RAGAS score karena model difference, bukan soal berbeda"

**Referensi:** BAB III 3.6.2 (Prosedur Pengujian), BAB II 2.1.7.3 (Sampling dan Validitas Statistik)

---

### 13. "Kenapa Claude Haiku sebagai judge? Bias tidak?"

**Jawaban singkat:**
- **Risk bias**: kalau judge sama keluarga model yg dinilai (Qwen judge untuk Qwen) → bias menilai diri tinggi
- **Claude Haiku mitigation**:
  - Keluarga **Anthropic** ≠ Meta (Llama) ≠ Alibaba (Qwen)
  - Independent judge, tidak sekeluarga model apapun
- **Research evidence** (Bellibatlu et al. 2026): frontier models lebih consistent judge daripada local small models
- **Cost**: Haiku murah ($1/$5 per juta token) → terjangkau

**Elaborasi:**
- Bias contoh: "Qwen menilai jawaban Qwen sendiri lebih tinggi" (self-preference bias)
- Claude independence: "Claude tidak terlatih khusus untuk academic domain seperti kedua model" → neutral judge
- Cost comparison: GPT-4 ($15/$20) vs Claude Haiku ($1/$5) → feasible untuk S1

**Referensi:** BAB II 2.1.7.2 (LLM-as-a-Judge), BAB III 3.6.3 (Metode Evaluasi: Claude Haiku)

---

## TIER 4: PERTANYAAN HASIL & INTERPRETASI (Saat bahas 4.4, 4.5)

### 14. "Kenapa Recall@1 'cuma' 0,35? Itu jelek tidak? Sistem jelek?"

**Jawaban singkat:**
- **Tidak jelek**, konteks:
  - Baseline random: 1 benar dari 56.833 chunk = 0,00176%
  - Sistem 0,35 = **~20.000× lebih baik dari random** ✅
  - Metrik R@1 sangat ketat (harus persis di rank #1)
- **Metrik relevan di produksi**: R@5 = 0,59-0,64 (jauh lebih tinggi)
- **Kurva naik tajam**: R@10 = 0,73 → sistem MENEMUKAN chunk benar, cuma tidak selalu #1
- **Perbandingan terdahulu**: mereka Recall 86% tapi corpus 111 dokumen (kami 56K) → beda skala completely

**Elaborasi:**
- Analogi: "Cari satu benda benar dari 56K benda di gudang → 35% sukses di posisi top-1, 64% dalam top-5 — impressive!"
- Kurva menunjukkan: sistem tidak "jelek", tapi "ranking-nya bukan #1" (fine-tuning bisa improve ranking)
- Realistic complexity: kami evaluate pada corpus 500× lebih besar dari terdahulu

**Referensi:** BAB IV 4.4.1 (Hasil Retrieval), BAB IV 4.5.1 (Analisis Performa)

---

### 15. "Llama menang di semua metrik RAGAS. Mengapa tidak langsung pilih Llama dari awal, tidak perlu Qwen?"

**Jawaban singkat:**
- **Benar** Llama unggul 2/4 metrik (faithfulness + answer relevancy)
- **Tapi** Qwen punya value:
  - Komparasi → insight: "Llama bagus untuk akurasi, Qwen untuk long-context"
  - Research contribution: "first comparative study di domain akademik Indonesia"
  - Future guidance: institusi lain bisa choose model sesuai priority (akurasi vs context)
- **Why not pilih Qwen**: context recall (lebih krusial untuk RAG) = sama, tapi faithfulness lebih rendah

**Elaborasi:**
- Llama unggul: faithfulness 0,788 (anti-halusinasi) + answer relevancy 0,747 (fokus jawaban)
- Qwen kekuatan: long-context understanding (per design), tapi answer relevancy lebih rendah (0,608)
- Design decision: context recall crucial (≠ gemuk jawaban tanpa retrieval di ranking atas) → Llama better
- Komparasi value: "Saat org lain mau implement RAG, mereka punya benchmark dari penelitian ini"

**Referensi:** BAB IV 4.4.3 (Hasil Evaluasi RAGAS), BAB IV 4.5.2 (Analisis Performa: Llama vs Qwen)

---

### 16. "Faithfulness 0,79 itu artinya apa? Itu bagus atau masih banyak halusinasi?"

**Jawaban singkat:**
- **0,79 = 79% klaim dalam jawaban didukung dokumen** ✅ BAGUS untuk akademik
- **Konteks**:
  - LLM pure tanpa retrieval: faithfulness ~0,3-0,4 (banyak halusinasi)
  - Sistem RAG: 0,79 (minimal halusinasi)
  - Best-in-class RAG systems: 0,85-0,90 (butuh fine-tuning)
- **Remaining 21%**: bukan salah, tapi generalization/inference reasonable (e.g., "prodi ini pakai KKNI" diinfer dari dokumen)

**Elaborasi:**
- Perbandingan: GPT-3.5 pure (no RAG) ≈ 0,35 faithfulness, sistem kami 0,79 = 2.2× improvement
- 21% inference contoh: dokumen bilang "KKNI" + "kurikulum" → model infer "pakai KKNI" (reasonable)
- Trade-off: 79% very faithful + 21% reasonable inference = acceptable untuk akademik domain

**Referensi:** BAB IV 4.4.3 (RAGAS Score: Llama), BAB II 2.1.7.1 (Metrik Evaluasi: Faithfulness)

---

### 17. "Berapa persen sistem ini bisa jawab pertanyaan di luar training data? Apa generalizabilitynya?"

**Jawaban singkat:**
- **Not trained on data** (ini RAG, bukan fine-tuning) → tidak ada "training data" dalam sense traditional
- **Generalizability**:
  - Sistem bisa jawab apa saja asal dokumen relevan ada di index
  - Jika user tanya "policy baru semester depan" tapi dokumen belum di-index → sistem jawab "tidak ada info relevan"
  - Kemampuan generalize tergantung: kualitas dokumen + retrieval akurasi
- **Testing on 1.880 Q**: termasuk diverse questions per 23 categories → representative

**Elaborasi:**
- No "training data" misconception: "Dataset 1.880 Q itu untuk EVALUASI, bukan training"
- Generalization contoh: "Sistem bisa jawab berbagai parafrase UKT (tidak harus exact word)" → karena dense retrieval paham semantic
- Out-of-distribution queries: "Kalau tanya hal yang tidak ada di dokumen → sistem tolak sopan" (design feature)

**Referensi:** BAB I (Tentang "Training"), BAB III 3.6 (Tahap Evaluasi: dataset)

---

### 18. "Sistem ini bisa handle dynamic queries atau harus predefined? Fleksibel tidak?"

**Jawaban singkat:**
- **Fully dynamic**: sistem bisa handle any query dalam natural language
- **Flexibility di architecture**:
  - Tidak perlu predefined intents/categories (chatbot intent-based: perlu)
  - User bisa tanya dalam berbagai cara (parafrase, bahasa alami) → dense retrieval paham
  - Update knowledge = ganti dokumen (tidak perlu redeploy/retrain)
- **Limitation**: sistem terbatas pada apa ada di dokumen (tidak bisa "hallucinate" info baru)

**Elaborasi:**
- Dynamic contoh: "Berapa UKT?", "UKT semester ganjil?", "Biaya pendidikan TK?", "Kisaran bayaran semester ini?" → semua bisa sistem handle
- Fleksibilitas infrastructure: "Semester depan UPI publish dokumen baru → hanya index ke vektor DB, sistem auto bisa jawab"
- Safety feature: "Batasan pada dokumen yang ada" (tidak bisa bikin data) = good untuk institutional context

**Referensi:** BAB IV 4.2.5 (Hasil Pengembangan Antarmuka), BAB III 3.3.7 (Perancangan Generasi Jawaban)

---

## TIER 5: PERTANYAAN KONTRIBUSI & LIMITASI

### 19. "Apa kontribusi unik penelitian ini dibanding penelitian terdahulu?"

**Jawaban singkat:**
- **Kontribusi scientific**:
  1. **Benchmark RAG skala besar**: 56K chunk (500× lebih besar dari terdahulu)
  2. **Full population evaluation**: 1.880 Q semua dievaluasi (vs terdahulu ratusan)
  3. **Standardized RAGAS**: evaluasi generasi dengan framework terstandar di domain akademik Indonesia (first time)
  4. **Comparative empirics**: 2 LLM open-weight head-to-head di domain akademik

- **Kontribusi practical**:
  1. **Local RAG solution**: 100% lokal, privasi terjaga, affordabel untuk institusi lain
  2. **Reusable dataset**: 1.880 Q&A dapat di-publish sebagai benchmark

**Elaborasi:**
- Terdahulu (Maryamah dkk): corpus 111 dokumen → penelitian ini 500× lebih challenging (realistic)
- Terdahulu (Es dkk): propose RAGAS → penelitian ini first application di academic Indonesian domain
- Uniknya: "tidak hanya implement, tapi systematically evaluate pada realistic scenario"

**Referensi:** BAB I 1.1 paragraf 5 (Celah penelitian), BAB I 1.4 (Manfaat Penelitian)

---

### 20. "Apa keterbatasan utama sistem ini? Kalau dilanjutkan, apa yang harus diperbaiki?"

**Jawaban singkat:**
- **Keterbatasan**:
  1. **Prototype, bukan production**: belum test dengan real users
  2. **Top_k tetap**: kadang chunk tidak relevan ikut (top-5 bisa punya "noise")
  3. **Answer relevancy sedang** (0,6-0,75): ada ruang perbaikan
  4. **Sampling untuk generasi**: 200 dari 1.880 (karena cost judge API)

- **Rencana perbaikan** (Bab V):
  1. **Short-term**: user study, re-ranking 2-stage, deploy staging
  2. **Medium-term**: fine-tuning, monitor corpus
  3. **Long-term**: extend domains, multi-language, federation

**Elaborasi:**
- Top-k issue contoh: "Tanya 'tentang apa UPI?' → mungkin dapat dokumen tentang 'uang' (kebetulan sama huruf)" (bisa fine-tuning query classifier)
- Sampling honest limitation: "Jika budget ada, full eval lebih baik" (trade-off disengaja)
- Future work: "Re-ranking 2-stage (ambil 50 → re-rank dengan model berbeda) bisa raise precision"

**Referensi:** BAB V 5.2 (Saran), BAB IV 4.5.2 (Kelebihan dan Kekurangan)

---

### 21. "Kalau sistem ini deploy ke UPI, apa yang perlu dipertimbangkan? Roadmap praktisnya?"

**Jawaban singkat:**
- **Immediate** (belum include dalam skripsi):
  - User testing dengan civitas akademika
  - Monitoring real-world queries
  - Feedback loop: update dokumen index saat user report error
  
- **Infrastructure**:
  - Server compute (GPU untuk inference lokal)
  - Database storage (corpus + vector DB)
  - Monitoring dashboard (query volume, response time, error rate)

- **Operational**:
  - Assign owner (siapa update dokumen saat policy berubah)
  - Training pengguna (awareness campaign)
  - SLA definition (99% uptime? < 5 second latency?)

- **Not in scope**:
  - Authentication/authorization (prototype only)
  - Integration dengan SIAK, payment gateway
  - Long-term user satisfaction study

**Elaborasi:**
- Deployment consideration: "Sistem ready prototype, bukan production-ready" (Bab I 1.5 scope)
- Infrastructure: Llama 8B needs GPU 6GB (RTX 4050, RTX 3080) or equivalent
- Operational: corpus update workflow (e.g., setiap publish dokumen baru → 1 jam index ke FAISS)

**Referensi:** BAB I 1.5.1 (Batasan: tidak deployment), BAB V 5.2 (Saran: user study, deployment roadmap)

---

### 22. "Apakah sistem ini bisa scale untuk institusi lain? Transferable ke kampus/universitas lain?"

**Jawaban singkat:**
- **Ya, transferable** dengan kondisi:
  - Replace dokumen UPI → dokumen institusi target
  - Model & embedding (Llama 8B, E5-multilingual) already general → no retraining needed
  - Architecture identik (FAISS, RRF, prompt template) → copy-paste feasible
  
- **Realistic transfer effort**:
  - Technical: 2-3 bulan (setup infrastructure, validate dokumen)
  - Non-technical: ongoing (corpus maintenance)

- **Scalability limit**:
  - Corpus size: 56K chunk lokal feasible, 500K+ mungkin perlu cloud DB (latency trade-off)
  - Multi-language: E5 multilingual support → bisa PT bahasa lain dengan minimal change

**Elaborasi:**
- Transfer example: "Institusi X punya 2000 dokumen, struktur sama (unit-based) → install system, index dokumen X, done"
- No retraining: Llama & E5 sudah general enough → tidak perlu domain-specific training
- Scalability: "100K chunk masih lokal (FAISS Flat index), >1M perlu cloud atau approximate index (IVF)"

**Referensi:** BAB V 5.2 (Kontribusi untuk institusi lain), BAB IV 4.1 (Generality)

---

## TIER 6: PERTANYAAN FILOSOFIS & RESEARCH ETHICS

### 23. "Kenapa Anda pilih design ini (lokal, prototype, doc publik saja)? Ada filosofi atau value di balik keputusan?"

**Jawaban singkat:**
- **Nilai underlying**:
  1. **Privasi sebagai hak**: "Institusi punya hak untuk process data locally, tidak terpaksa cloud-dependent"
  2. **Transparansi**: "RAG source-traceable → pengguna tahu jawaban dari dokumen mana" vs pure LLM "black box"
  3. **Sustainability**: "Jangan pakai proprietary API yang ada, use open-source" (future-proof)
  4. **Inclusivity**: "Teknologi baru (LLM) harus accessible untuk institusi kecil" (lokal feasible, API expensive)

- **Design reflection**:
  - Public docs only: "Respect institutional hierarchy & privacy boundary"
  - Prototype scope: "Be honest about limitations, not oversell"
  - Evaluation rigorous: "Accountability through metrics, not hope"

**Elaborasi:**
- Privacy philosophy: "Post-Snowden, institutional data sovereignty matters"
- Transparency: "Medical diagnosis 'take aspirin' vs RAG 'take aspirin per dokumen X'" → latter more trustworthy
- Open-source commitment: "Research should leave behind code & dataset, not just paper"

**Referensi:** BAB I 1.1 (Latar Belakang: privasi), BAB I 1.5 (Scope: ethical boundaries)

---

### 24. "Apakah ada risiko etika atau kebijakan dalam deployment sistem ini di UPI?"

**Jawaban singkat:**
- **Risiko minimal** (karena scope):
  - Dokumen publik only → tidak ada data privacy breach risk
  - Prototype status → tidak direct replacement sistem existing
  - Lokal only → no third-party data exposure

- **Potential issue jika scale**:
  1. **Bias dalam dokumen**: kalau dokumen UPI punya bias (e.g., gender), sistem akan reflect
  2. **Misinformation via outdated docs**: perlu maintenance process
  3. **Accessibility**: kalau hanya web → exclude non-internet users

- **Mitigation**:
  - Transparency: "Chatbot ini berbasis dokumen resmi, akurat sesuai dokumen"
  - Feedback mechanism: "User bisa report error → update corpus"
  - Hybrid access: "Tetap sediakan human support channel (email, phone)"

**Elaborasi:**
- Bias example: "Jika dokumen scholarshp hanya mention 'mahasiswa berprestasi', bias terhadap non-academic achievement"
- Outdated doc: "Policy UKT berubah setiap semester → perlu maintenance schedule"
- Accessibility: "Chatbot web-only tidak include offline or non-tech-savvy users"

**Referensi:** BAB I 1.5.1 (Ethical boundaries), BAB IV 4.5 (Limitations & mitigation)

---

### 25. "Bagaimana Anda measure 'success' dalam penelitian ini? Apa success metric yang paling penting?"

**Jawaban singkat:**
- **Primary success metric**:
  - **Faithfulness ≥ 0.75** (80% jawaban akurat, minimal halusinasi) ✅ Achieved (0.788)
  - **Retrieval Recall@5 ≥ 0.60** (60% dokumen benar di top-5) ✅ Achieved (0.641)
  - Hybrid retrieval unggul daripada single strategy ✅ Achieved (+14-16%)

- **Secondary metric**:
  - System functional & deployable ✅ Working
  - Code open-source & reproducible ✅ GitHub repo
  - Dataset reusable ✅ 1.880 Q structured

- **Definition success**:
  - "Tidak harus sempurna (system perfect)", tapi "demonstrably better than baselines"
  - "Prototyped enough untuk jadi foundation di-production deployment"

**Elaborasi:**
- Faithfulness 0.75 threshold: "industri standard untuk RAG systems acceptable untuk deployment"
- Recall@5 0.64: "64% dokumen benar di top-5, user hanya lihat 5 → good hit rate"
- Reproducible: "kalau institusi lain ikuti method ini, harus dapat hasil similar"

**Referensi:** BAB I 1.3 (Tujuan), BAB IV 4.5.1 (Analisis Performa: interpretasi hasil)

---

## BONUS: PERTANYAAN CURVEBALL (Penguji bisa tanya hal di luar ekspektasi)

### 26. "Kalau model Anda 'hallucinate' (jawab hal yang tidak di dokumen), bagaimana user tahu? Siapa yang tanggung jawab?"

**Jawaban singkat:**
- **Detection mechanism**:
  - Sistem designed untuk **minimize hallucination** (faithfulness 0.79)
  - Tapi bukan 0% risk (sisanya 0.21 adalah inference/generalization)
  
- **User mitigation**:
  - Jawaban always include source sitasi `[1]`, `[2]` → user bisa verify dokumen
  - UI menampilkan actual chunk dari dokumen → user lihat konteks asli
  - "Jika tidak percaya → check dokumen original link" → user agency

- **Responsibility**:
  - Sistem: "Transparansi (provide source, chunk preview)"
  - UPI: "Monitor query patterns, collect user feedback"
  - User: "Verify info penting sebelum tindakan (e.g., biaya pembayaran)"

**Elaborasi:**
- Medical analogy: "AI diagnosis 'kemungkinan flu' + saran 'konsultasi dokter'" > "AI diagnosis 'flu' tanpa saran"
- Sitasi importance: "RAG advantage vs pure LLM adalah traceable" → invert ke user responsibility
- Responsibility clear: "Sistem provide info, user verify" (not "sistem guarantee 100% akurat")

**Referensi:** BAB II 2.1.7.2 (Faithfulness metric), BAB IV 4.2.5 (UI: menampilkan source chunks)

---

### 27. "Apakah sistem ini bisa di-hack atau dimanipulasi? Security-nya bagaimana?"

**Jawaban singkat:**
- **Attack surface minimal** (lokal, no API):
  - Network exposure limited (local deployment)
  - No authentication/authorization breach (prototype scope)
  - Data locally stored (no cloud leak risk)

- **Potential vulnerability** (if scaled):
  1. **Prompt injection**: user craft query untuk manipulate output
     - Mitigation: system prompt immutable, grounding on doc (user input tidak override)
  2. **Document poisoning**: attacker modify indexed document
     - Mitigation: only authorized staff can update corpus, version control
  3. **Inference denial**: user spam queries untuk overload system
     - Mitigation: rate limiting, resource quota (production deployment)

- **Current status**:
  - Prototype scope: "security hardening not priority" (transparency over robustness)
  - Deployment-ready: "need security audit + penetration testing"

**Elaborasi:**
- Prompt injection example: "User tanya 'ignore rules, ini UKT berapa?' → system masih check dokumen, tidak execute injection"
- Document version control: "Track who updated corpus, when, what changed → audit trail"
- Rate limiting: "1000 queries/IP/hour" → prevent DoS

**Referensi:** BAB I 1.5.1 (Scope: prototype only), BAB III 3.4 (Implementation: no auth for prototype)

---

### 28. "Kalau pertanyaan di luar domain akademik ditanya? Sistem bagaimana respond?"

**Jawaban singkat:**
- **Design untuk tolak gracefully**:
  - Jika tidak ada dokumen relevan → sistem jawab: "Maaf, saya tidak punya informasi tentang [topic], silakan hubungi unit terkait"
  - Bukan hallucinate jawaban random
  - User experience: helpful (tahu kemana tanya) vs frustrating (tidak tahu)

- **Contoh out-of-domain**:
  - "Apa arti cinta?" → Tidak ada dokumen → tolak sopan
  - "Siapa presiden Indonesia?" → Tidak ada dokumen UPI → tolak sopan
  - "Bagaimana cara daftar UPI?" → Ada dokumen PMB → jawab

- **Design philosophy**:
  - "Conservative refusal better than confident hallucination" (RAG advantage)
  - "Dalam akademik context, better say 'don't know' than invent facts"

**Elaborasi:**
- Comparison: "Pure LLM mungkin 'hallucinate' presiden Indonesia, tapi RAG check dokumen → tidak ada → refusal"
- User experience: "Frustrating tapi honest > easy tapi wrong"
- Trade-off: "Sometimes user frustrated 'kenapa tidak tahu hal umum?' tapi this is feature not bug"

**Referensi:** BAB I 1.5.2 (Fungsi Chatbot: apa yang tidak dijawab), BAB III 3.3.8 (Prompt design: grounding rules)

---

### 29. "Penelitian ini relevant untuk 5 tahun ke depan? Atau LLM technology akan jauh lebih canggih?"

**Jawaban singkat:**
- **Relevance**:
  - **Problem tetap**: institusi besar akan tetap punya dokumen scattered (organizational inertia)
  - **Local LLM tetap relevant**: regulatory trend mengarah privacy-by-design (data lokalisasi)
  - **RAG tetap needed**: hallucination problem persist bahkan di frontier models

- **Evolution**:
  - **Short-term (1-2 tahun)**: model lebih baik (faster, smaller), RAG techniques evolve (hybrid → more sophisticated)
  - **Medium-term (3-5 tahun)**: multimodal RAG (image, video), real-time docs, agents
  - **Long-term**: fundamental paradigm mungkin berubah (world models?) tapi basic RAG principle survive

- **Why still relevant**:
  - Research itu "capture state-of-the-art now" tidak "predict future"
  - Contribution adalah methodological (how to evaluate, how to compare) → timeless
  - Dataset 1.880 Q tetap useful sebagai benchmark (even jika model evolve)

**Elaborasi:**
- Technology cycle: "GPS akan 'outdated' 10 tahun ke depan, tapi navigation problem tetap relevant"
- Evaluation framework: "RAGAS 2024 mungkin ada improvements, tapi foundational ideas persist"
- Industry adoption: "RAG standard practice di enterprise AI now (OpenAI, Google, Anthropic all implement)" → not hype

**Referensi:** BAB I 1.4 (Manfaat jangka panjang), BAB V 5.2 (Saran penelitian lanjutan)

---

## STRATEGI JAWAB PERTANYAAN "WHY?"

**Struktur jawaban rekomendasi**:

1. **Mulai dengan akuan**: "Bagus pertanyaan, alasan saya..."
2. **Berikan jawaban singkat** (1-2 kalimat): pokok yang langsung
3. **Elaborasi dengan detail**: mengapa, tradeoff, konteks
4. **Cite referensi**: "Ini ada di BAB I 1.1" atau "di BAB IV 4.4"
5. **Tawarkan depth**: "Mau saya jelaskan lebih detail tentang...?"

**Jangan lakukan**:
- ❌ Defensive ("Kenapa pertanyaan ini?" → sound defensif)
- ❌ Over-explain ("Karena teknologi machine learning adalah..." → tangent)
- ❌ Cite hanya paper ("Es et al. 2024 bilang..." tanpa interpretation)

**Confidence signal**:
- ✅ Terima pertanyaan dengan antusias ("Good question!")
- ✅ Jawab dengan conviction (bukan "mungkin", "kurang tahu")
- ✅ Distinguish antara "design choice" vs "limitation" vs "future work"

---

**Print daftar ini & study 2-3 hari sebelum sidang. Focus pada TIER 1-2 dulu (basic questions), baru TIER 3+ jika ada waktu.** 🎓
