# UPI Chatbot — RAG-Based Information System

**Chatbot untuk Universitas Pendidikan Indonesia (UPI)**

Sistem chatbot berbasis Retrieval-Augmented Generation (RAG) untuk menjawab pertanyaan seputar UPI dengan akurat menggunakan dokumen resmi universitas.

---

## 🎯 Fitur Utama

- **RAG Pipeline**: Retrieval dari 60,000+ vectors database dengan hybrid search
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

### Add New PDFs (Windows)

`Add-New-PDF.exe` di root project menambahkan dokumen PDF baru ke basis
pengetahuan chatbot tanpa command line: double-click, isi folder PDF +
nama kategori, tunggu proses selesai. Di baliknya menjalankan pipeline
extract → clean (OCR untuk halaman scan) → chunk → embed, lalu menggabungkan
hasilnya ke index yang sama dipakai backend. Restart backend setelah selesai
agar dokumen baru bisa ditemukan. Detail teknis tiap tahap ada di
[`backend/scripts/ingestion/README.md`](backend/scripts/ingestion/README.md).

Membutuhkan `backend/.venv` sudah pernah dibuat (otomatis oleh
`UPI-Chatbot-Launcher.exe` saat pertama kali dijalankan).

---

## ⚙️ Configuration

### Backend `.env`

```env
# LLM
OLLAMA_MODEL=qwen2.5:3b
LLM_REQUEST_TIMEOUT=90
OLLAMA_NUM_CTX=4096

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

## 🛠️ Troubleshooting

### Ollama not using the GPU

If chat answers are slow or time out, check whether Ollama is actually
using the GPU:

```powershell
ollama ps
```

The `PROCESSOR` column should show `100% GPU` (or close to it). If it shows
`100% CPU`, Windows hasn't assigned Ollama to the discrete GPU — common on
laptops with hybrid graphics (NVIDIA Optimus), where the dGPU stays asleep
until an app is explicitly assigned to it:

1. Open **Settings → System → Display → Graphics**
2. Find (or add) **`ollama.exe`** and **`ollama app.exe`**
   (usually in `%LOCALAPPDATA%\Programs\Ollama\`)
3. Set **GPU preference** to **High performance** (your NVIDIA GPU) for both
4. Leave **"Optimizations for windowed games"** off — Ollama has no
   window/game rendering loop, so this setting is a no-op for it
5. Restart Ollama (see below) for the change to take effect

### Restarting Ollama manually

Windows GPU preference changes only apply to a *new* Ollama process, so
quitting and relaunching is required after step 3 above (or whenever Ollama
seems stuck/misbehaving):

**Via the system tray:** right-click the Ollama icon → **Quit**, then
relaunch it from the Start Menu.

**Via PowerShell:**
```powershell
Get-Process -Name "ollama*" | Stop-Process -Force
Start-Process "$env:LOCALAPPDATA\Programs\Ollama\ollama app.exe"
```

Verify with `ollama ps` after a chat request — `PROCESSOR` should now show
GPU usage.

### Why llama3.1:8b-instruct-q4_K_M is the default model

Accuracy over speed: `llama3.1:8b-instruct-q4_K_M` is the intended default.
`qwen2.5:3b` was only used as a comparison baseline while testing GPU
offload and isn't meant to ship as the default, even though it's faster and
lighter on VRAM.

On this 6 GB VRAM card, `llama3.1:8b-instruct-q4_K_M` reaches ~75% GPU
(~5.6 GB VRAM, `num_ctx=4096`) and takes ~55s per RAG-grounded answer.
That leaves only ~0.3 GB of VRAM free while the model is resident (30 min
`keep_alive` after each use) — tight enough to visibly corrupt rendering in
other GPU-accelerated apps running at the same time (observed in Claude
Code itself). `qwen2.5:3b` (100% GPU, ~2.1 GB, ~10-15s) remains selectable
per-request from the Settings model dropdown when speed or multitasking
matters more than accuracy. See the comments in `backend/.env`
(`OLLAMA_MODEL`, `LLM_REQUEST_TIMEOUT`, `OLLAMA_NUM_CTX`) for the full
measurements.

If you notice rendering glitches in other apps while chatting, free the
VRAM with `ollama stop llama3.1:8b-instruct-q4_K_M` (see
[Restarting Ollama manually](#restarting-ollama-manually) above for more).

### Incomplete or wrong-sounding answers to "list all X" questions

RAG answers are only as complete as the chunks retrieved. Three fixes went
into `backend/app/rag/vectorstore.py` and `rag_service.py` after "ada
fakultas apa saja di UPI?" only listed 2 of UPI's 8 faculties:

1. **Noise filtering** — hybrid retrieval (dense + BM25 fused via
   Reciprocal Rank Fusion) could previously rank a chunk highly on pure
   keyword coincidence with zero semantic relevance to the query (e.g. an
   unrelated article surfacing because it happened to share a word).
   Chunks with no dense/semantic score are now dropped outright: BM25 only
   re-ranks candidates dense search already found plausible.
2. **Wider context window** — a real grounded prompt (system rules +
   retrieved chunks + few-shot examples + question) measured ~2650 tokens,
   already over the old `OLLAMA_NUM_CTX=2048`, silently truncating context
   the model never got to see. Raised to 4096.
3. **Neighbor-chunk expansion** — long enumerated lists in source documents
   (like UPI's 8-faculty list) are sometimes split across sequential
   chunks. Only the chunk with the framing sentence ("berikut adalah...")
   scores well against a generic query; its continuation reads as a bare
   list and scores too low to be retrieved on its own. `FaissVectorStore.
   expand_with_next_neighbor()` now pulls in each retrieved chunk's
   immediate next chunk from the same source document (same `doc_id`,
   `chunk_index + 1`) when one exists, so continuations aren't silently
   dropped. This runs *after* the final top-k selection in
   `RagService.retrieve()`, not inside `vectorstore.search()` - expanding
   earlier just means the oversampled-pool truncation discards it again.

If you hit another incomplete-list answer, check `GET /api/retrieve/debug`
first: it returns the actual retrieved chunks and the exact `prompt_preview`
sent to the model, which tells you whether the gap is retrieval (wrong/
missing chunks) or generation (right chunks, model didn't use them).

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

**Latest Update**: July 17, 2026 (retrieval quality fixes: noise filtering, wider context window, neighbor-chunk expansion)
