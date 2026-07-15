# UPI Chatbot — RAG-Based Information System

**Chatbot untuk Universitas Pendidikan Indonesia (UPI)**

Sistem chatbot berbasis Retrieval-Augmented Generation (RAG) untuk menjawab pertanyaan seputar UPI dengan akurat menggunakan dokumen resmi universitas.

---

## 🎯 Fitur Utama

- **RAG Pipeline**: Retrieval dari 56,833+ vectors database dengan hybrid search
- **Multi-language**: Support Bahasa Indonesia & English dengan dynamic switching
- **Chat Management**: Riwayat percakapan tersimpan per user
- **Document Viewer**: Akses dokumen sumber dengan deep-linking
- **Customization**: Theme selector, model selection, retrieval tuning
- **Security**: User authentication dengan password hashing

---

## 📁 Struktur Project

```
chatbot-rag-upi-alpha/
├── backend/
│   ├── app/
│   │   ├── api/              # API routes
│   │   ├── rag/              # RAG pipeline
│   │   ├── services/         # Business logic
│   │   └── data/             # SQLite, FAISS index
│   ├── requirements.txt
│   ├── .env                  # Configuration
│   └── manage_users.py        # CLI tools
│
├── frontend/
│   ├── app/                  # Next.js app
│   ├── components/           # React components
│   ├── contexts/             # Global state (i18n)
│   ├── locales/              # Translations
│   └── public/               # Static assets
│
└── docs/
    └── setup.md              # Setup guide
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

`UPI-Chatbot-Launcher.exe` di root project menjalankan backend dan frontend
sekaligus, lalu membuka browser otomatis. Cukup double-click — pada
menjalankan pertama kali, launcher otomatis mendeteksi dan menginstall
dependencies yang belum ada (`pip install`, `npm install`), jadi tidak perlu
setup manual. Prasyarat: Python 3.10+ dan Node.js sudah terpasang dan ada
di PATH.

Browser: `http://localhost:3000`

---

## ⚙️ Configuration

### Backend `.env`

```env
# LLM
OLLAMA_MODEL=qwen2.5:3b
LLM_REQUEST_TIMEOUT=60

# Database
FAISS_INDEX_PATH=./app/data/faiss.index
CHUNKS_META_PATH=./app/data/chunks_meta.json

# Retrieval
DEFAULT_TOP_K=3
HYBRID_RETRIEVAL=true
```

---

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login |
| POST | `/api/chat` | Chat with RAG |
| POST | `/api/retrieve` | Retrieve documents only |
| GET | `/api/source/{doc_id}` | Get source document |
| GET | `/api/sessions` | List chat sessions |
| GET | `/health` | Health check |

---

## 📊 Tech Stack

- **Vector DB**: FAISS (local)
- **Embeddings**: intfloat/multilingual-e5-base (768-dim)
- **LLM**: Ollama (Qwen 2.5:3B default)
- **Backend**: FastAPI, Pydantic, SQLite
- **Frontend**: Next.js 14, TypeScript, Tailwind, Zustand

---

## 🔐 Security

- Passwords: scrypt hashing (n=2^14)
- API tokens: SHA-256 digest in database
- CORS: localhost:3000
- SQL injection prevention: Parameterized queries

---

## 📝 Development

### User Management (Backend)

```bash
python manage_users.py list
python manage_users.py delete <username> --force
```

### i18n Translations (Frontend)

- Indonesian: `frontend/locales/id.json`
- English: `frontend/locales/en.json`
- Add keys, restart frontend

---

## 🗓️ Roadmap

- **v0.1**: Core RAG + auth + i18n ✅
- **v0.2**: Email service, advanced search
- **v0.3**: Admin dashboard, analytics
- **v1.0**: Production deployment

---

## 📄 License

Private development. Not for public distribution.

---

**Latest Update**: July 15, 2026
