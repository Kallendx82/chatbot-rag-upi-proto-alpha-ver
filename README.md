# UPI Chatbot — RAG-Based Information System (Alpha v0.1)

**Chatbot untuk Universitas Pendidikan Indonesia (UPI)**  
Sistem informasi berbasis Retrieval-Augmented Generation (RAG) untuk menjawab pertanyaan seputar UPI dengan akurat dan berbasis dokumen resmi.

---

## 🎯 Fitur Alpha

✅ **Retrieval-Augmented Generation (RAG)**
- Pengambilan informasi otomatis dari 56,833+ vectors database
- Hybrid retrieval (semantic + keyword matching)
- Akurasi tinggi dengan BM25 + dense vector search

✅ **Chat Interface Responsif**
- Real-time conversation dengan chatbot
- Sidebar management untuk riwayat percakapan
- Split view untuk chat + document viewer

✅ **Internationalization (i18n)**
- Support Bahasa Indonesia & English
- Dynamic language switching dengan auto-refresh
- Persistent language preferences

✅ **Authentication & Security**
- User registration + login dengan SQLite database
- Password validation (min 8 chars, uppercase, lowercase, special char)
- Admin account untuk alpha testing
- Secure password storage dengan scrypt hashing

✅ **Document Sourcing**
- View original source documents dalam browser
- Deep-link ke page tertentu (e.g., page 30)
- Fallback text display jika PDF tidak tersedia

✅ **Settings & Customization**
- Theme selector (Light/Dark/System)
- Model selection (Llama 3.1, Qwen 2.5, Llama 3.2)
- Retrieval parameters (Top-K, Temperature)
- Debug mode untuk technical users

✅ **Performance Optimization**
- Qwen 2.5:3B default model (~5x faster inference)
- 60-second request timeout
- Optimized vector indexing dengan FAISS
- Minimal CSS + optimized bundle

---

## 🚀 Quick Start

### Prasyarat
- Python 3.10+
- Node.js 18+
- Ollama (untuk LLM lokal)
- SQLite3

### Setup Backend

```bash
cd "Source code/backend"

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Edit .env dengan settings model, dll

# Start backend
python -m uvicorn app.main:app --reload --port 8000
```

### Setup Frontend

```bash
cd "Source code/frontend"

# Install dependencies
npm install

# Start dev server
npm run dev
```

Browser: **http://localhost:3000**

---

## 👤 Admin Credentials (Alpha)

```
Username: admin
Password: Admin@123456
Email:    admin@upi.rag
```

---

## 📋 Project Structure

```
RAG_UPI/
├── Source code/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/          # API routes
│   │   │   ├── rag/          # RAG pipeline
│   │   │   ├── services/     # Auth, logging
│   │   │   └── data/         # SQLite, FAISS index
│   │   ├── .env              # Configuration
│   │   └── manage_users.py    # User management CLI
│   │
│   └── frontend/
│       ├── app/              # Next.js app
│       ├── components/       # React components
│       ├── contexts/         # I18n context
│       ├── locales/          # Translation files
│       └── public/           # Static assets
│
└── Dataset/                   # RAG document corpus
    └── _pipeline/            # FAISS index + metadata
```

---

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register` — Register user
- `POST /api/auth/login` — Login & get token
- `POST /api/auth/change-password` — Change password
- `POST /api/auth/logout` — Logout

### Chat & Retrieval
- `POST /api/chat` — Full RAG turn (retrieve + generate)
- `POST /api/retrieve` — Retrieve only (no generation)
- `GET /api/retrieve/debug` — Detailed retrieval debug info

### Sources
- `GET /api/source/{doc_id}` — Serve source PDF/text

### Sessions
- `GET /api/sessions` — List user's chat sessions
- `GET /api/sessions/{id}` — Get session with messages
- `POST /api/sessions` — Create new session
- `PUT /api/sessions/{id}` — Rename session
- `DELETE /api/sessions/{id}` — Delete session

### Health
- `GET /health` — Health check (components status)

---

## ⚙️ Configuration

### `.env` (Backend)

```env
# LLM Model
OLLAMA_MODEL=qwen2.5:3b
LLM_REQUEST_TIMEOUT=60

# Database
FAISS_INDEX_PATH=./app/data/faiss.index
CHUNKS_META_PATH=./app/data/chunks_meta.json

# Retrieval
DEFAULT_TOP_K=3
RETRIEVAL_SCORE_THRESHOLD=0.0
HYBRID_RETRIEVAL=true
```

---

## 🛠️ Development Tools

### User Management
```bash
# List all users
python manage_users.py list

# Delete user
python manage_users.py delete <username> --force
```

### Database
- Location: `app/data/users.db` (SQLite)
- Schema: users, auth_tokens, password_resets, chat_sessions, chat_messages

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Vector DB Size | 56,833 vectors (768-dim) |
| BM25 Index | ~6.2s build time |
| Avg Chat Response | 15-30s (Qwen 2.5:3B) |
| Request Timeout | 60s |
| Theme Load | <100ms |

---

## 🔐 Security Notes

- Passwords hashed dengan scrypt (n=2^14, r=8, p=1)
- API tokens: opaque strings, SHA-256 di database
- First registered user = admin (automatic)
- Input validation pada semua endpoints
- CORS configured untuk localhost:3000

---

## 📝 Known Limitations (Alpha)

⚠️ **Email Service**
- Forgot password disabled (TODO)
- Reset password disabled (TODO)
- Contact admin if password reset needed

⚠️ **PDF Linking**
- Some documents fallback to text/plain display
- Deep-linking by page number supported

⚠️ **Performance**
- First load (embeddings + FAISS): ~1 minute
- Vector store lazy-loaded at startup

---

## 🗓️ Roadmap

### v0.2 (Next)
- [ ] Email service integration
- [ ] Forgot password flow
- [ ] User profile management
- [ ] Chat export (PDF/JSON)

### v0.3
- [ ] Advanced search filters
- [ ] Feedback mechanism
- [ ] Admin dashboard
- [ ] Usage analytics

### v1.0 (Production)
- [ ] Performance optimization
- [ ] Multi-user concurrent load testing
- [ ] Deployment guide (Docker/K8s)

---

## 💡 Tips for Testing

**Best demo questions:**
- "Berapa jumlah mahasiswa di UPI?"
- "Apa program studi di FIP?"
- "Bagaimana prosedur pendaftaran?"
- "Sebutkan fasilitas olahraga di UPI"

**Test language switching:**
- Open Settings → Change "Bahasa Antarmuka" → Save
- Page auto-refreshes dengan bahasa baru
- All UI text updates instantly

**Test document viewer:**
- Ask a question, click citation
- Document opens in /viewer with page number
- Close viewer, back to chat

---

## 📧 Support

**For alpha testing issues:**
- Contact: admin@upi.rag
- Known issues documented in GitHub Issues

---

## 📄 License

Alpha version untuk testing internal. Distribution restricted.

---

**Version:** Alpha v0.1  
**Status:** Active Development  
**Last Updated:** July 15, 2026
