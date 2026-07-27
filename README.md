# UPI Chatbot — RAG-Based Information System

**Chatbot untuk Universitas Pendidikan Indonesia (UPI)**

Sistem chatbot berbasis Retrieval-Augmented Generation (RAG) untuk menjawab pertanyaan seputar UPI dengan akurat menggunakan dokumen resmi universitas.

---

## 🎯 Fitur Utama

- **RAG Pipeline**: Retrieval dari 63.700+ vector chunks database dengan Hybrid Search (FAISS Dense + BM25 RRF Fusion)
- **Multi-language**: Support Bahasa Indonesia & English dengan dynamic switching
- **Chat Management**: Sesi percakapan tersimpan, penamaan otomatis, navigasi riwayat jawaban multi-generasi (`< 1/N >`), dan tombol retry instan pada kesalahan server
- **Admin Document Management**: Halaman `/admin` lengkap dengan pengunggahan PDF, kustomisasi judul, **Kategori Utama**, **Sub-kategori**, penyesuaian chunk size/overlap, serta **penghapusan instant dokumen & chunk** dari FAISS vectorstore
- **Document Viewer**: Akses dokumen sumber (PDF & Web/Markdown) dengan deep-linking dan penampil internal berbasis `pdf.js`
- **Retrieval Explainability**: Panel *Retrieval Debug* transparan untuk melihat latensi, skor kemiripan, dan pratinjau prompt grounded
- **Evaluasi & Benchmarking**: Evaluasi RAGAS (Faithfulness, Answer Relevancy, Context Precision, Context Recall) dengan dataset sampel substantif (`dataset.substantive.json`) dan LLM-as-a-Judge
- **Security**: User authentication berbasis SQLite dengan scrypt password hashing & role-based access control (RBAC Admin)

---

## 📁 Struktur Project

```
chatbot-rag-upi-alpha/
├── backend/
│   ├── app/
│   │   ├── api/              # API routes (chat, ingest, documents, auth, debug, statistics)
│   │   ├── rag/              # RAG pipeline (vectorstore, embedder, llm, prompt)
│   │   ├── services/         # Business logic & authentication
│   │   └── data/             # SQLite, FAISS index, metadata, sources
│   ├── scripts/ingestion/    # Offline ingestion pipeline (extract, clean, chunk, embed)
│   ├── requirements.txt
│   └── .env                  # Configuration
│
├── frontend/
│   ├── app/                  # Next.js app (chat, admin, stats, viewer)
│   ├── components/           # React components (chat, citations, debug, ui)
│   ├── locales/              # Translations (id, en)
│   └── public/               # Static assets & dynamic background images
│
└── docs/
    ├── evaluation/           # RAGAS evaluation scripts & benchmark datasets
    └── thesis/               # Dokumentasi Bab IV & panduan skripsi
```

---

## 🚀 Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### One-Click Launcher (Windows)

`UPI-Chatbot-Launcher.exe` di root project menjalankan backend dan frontend sekaligus, lalu membuka browser otomatis di `http://localhost:3000`.

---

## 🔌 API Endpoints Utama

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/register` | Register user / admin |
| POST | `/api/auth/login` | Login |
| POST | `/api/chat` | Chat dengan RAG & model override |
| POST | `/api/retrieve` | Retrieval dokumen saja |
| GET | `/api/retrieve/debug` | Debug panel: latensi & pratinjau prompt |
| POST | `/api/ingest` | Upload & ingest PDF baru (Admin) |
| GET | `/api/documents` | List seluruh dokumen di FAISS index |
| DELETE | `/api/documents` | Hapus dokumen & chunk dari index (Admin) |
| GET | `/api/source/{doc_id}` | Serve dokumen sumber (PDF / MD / TXT) |
| GET | `/api/backgrounds` | List gambar background dinamis admin |
| GET | `/health` | Health check |

---

## 📊 Tech Stack

- **Vector DB**: FAISS (local index)
- **Embeddings**: `intfloat/multilingual-e5-base` (768-dim)
- **LLM**: Ollama (`llama3.1:8b-instruct-q4_K_M` default, `qwen3.5:4b-q4_K_M` optional)
- **Backend**: FastAPI, Pydantic, SQLite, PyMuPDF, Tesseract OCR
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Zustand, Framer Motion, PDF.js

---

## 📝 Evaluasi RAGAS (LLM-as-a-Judge)

Skrip evaluasi otomatis RAGAS dapat dijalankan di folder `docs/evaluation/`:

```powershell
cd docs/evaluation

# Evaluasi retrieval & generation dengan dataset substantif
python run_eval.py --models llama3.1:8b-instruct-q4_K_M qwen3.5:4b-q4_K_M --dataset dataset.substantive.json --top-k 8 --skip-judge
```

---

## 📄 License

Private development. Not for public distribution.

---

**Latest Update**: July 27, 2026 (Sub-kategori ingest, admin document deletion, error retry button, response history sync, and substantive RAGAS benchmark)
