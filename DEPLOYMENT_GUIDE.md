# Panduan Deployment — Chatbot RAG UPI

## Masalah: Web mati saat laptop dimatikan

Situs `upi.ragupi.my.id` berjalan di laptop kamu. Saat laptop mati → server mati.
Solusi: pindahkan ke server yang selalu nyala (VPS cloud).

---

## Opsi 1: Oracle Cloud Free Tier (GRATIS selamanya, direkomendasikan)

Oracle memberi VM **4 OCPU ARM + 24GB RAM** gratis permanen — cukup untuk Ollama +
backend + frontend.

### Langkah-langkah

1. **Daftar Oracle Cloud** → https://www.oracle.com/cloud/free/
   - Pakai email, verifikasi kartu kredit (tidak ditagih selama Free Tier)

2. **Buat VM:**
   - Shape: `VM.Standard.A1.Flex` (ARM) — 4 OCPU, 24 GB RAM
   - OS: Ubuntu 22.04 LTS
   - Tambah SSH key publik kamu

3. **Buka port di Security List Oracle:**
   - Port 22 (SSH), 80 (HTTP), 443 (HTTPS), 3000 (frontend), 8000 (backend), 11434 (Ollama)

4. **Di server, install Docker:**
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker ubuntu
   ```

5. **Clone repo & copy dataset:**
   ```bash
   git clone https://github.com/Kallendx82/Chatbot-RAG-UPI.git
   cd Chatbot-RAG-UPI
   # Copy dataset dari laptop via scp (hanya sekali, ~2GB):
   scp -r "D:\Project\RAG_UPI\Dataset\_pipeline\index" ubuntu@<IP>:~/Chatbot-RAG-UPI/Dataset/_pipeline/
   ```

6. **Pull model Ollama (lebih ringan untuk server CPU):**
   ```bash
   docker compose -f "Source code/docker-compose.yml" up ollama -d
   docker exec -it <ollama_container> ollama pull qwen2.5:3b
   # atau llama3.2:3b (lebih ringan dari llama3.1:8b)
   ```

7. **Jalankan semua service:**
   ```bash
   cd "Source code"
   docker compose up -d
   ```

8. **Arahkan domain kamu** (upi.ragupi.my.id) ke IP server Oracle di Cloudflare DNS.

### Catatan model untuk server CPU:
- `llama3.1:8b` di CPU → ~3-5 menit/jawaban (terlalu lambat)
- `qwen2.5:3b` di CPU → ~40-90 detik (lebih layak untuk demo)
- Untuk sidang: gunakan laptop dengan GPU RTX-4050 supaya cepat

---

## Opsi 2: Tetap di Laptop (paling simpel untuk demo/sidang)

Cocok kalau hanya butuh online saat presentasi.

1. **Cegah sleep saat tutup lid:**
   ```powershell
   powercfg -change -standby-timeout-ac 0   # tidak tidur saat colok charger
   powercfg -change -monitor-timeout-ac 60  # layar mati ok, tapi sistem tetap jalan
   ```

2. **Gunakan Cloudflare Tunnel** (tidak perlu IP publik/port forward):
   ```powershell
   winget install Cloudflare.cloudflared
   cloudflared tunnel login
   cloudflared tunnel create upi-rag
   cloudflared tunnel route dns upi-rag upi.ragupi.my.id
   cloudflared tunnel run --url http://localhost:3000 upi-rag
   ```
   Tunnel Cloudflare = laptop bisa di balik NAT/ISP biasa, tetap dapat domain stabil.

---

## Cara update web setelah ada perubahan kode

### Jika pakai Docker di VPS:
```bash
# Di server VPS
git pull origin main
cd "Source code"
docker compose build --no-cache backend frontend
docker compose up -d
```

### Jika pakai laptop (mode development):
```powershell
# Pull perubahan terbaru
git pull origin main
# Restart backend
Stop-Process -Name "uvicorn" -Force -ErrorAction SilentlyContinue
cd "D:\Project\RAG_UPI\Source code"
.\start.ps1
```

### Workflow singkat (setiap ada perubahan kode):
```
Edit kode → git commit → git push → (di server) git pull + docker compose up -d
```

---

## Struktur file Docker yang dibuat

```
Source code/
├── docker-compose.yml    ← orchestrator semua service
├── backend/
│   └── Dockerfile        ← image FastAPI
└── frontend/
    └── Dockerfile        ← image Next.js (standalone)
```

## Variabel environment penting di docker-compose.yml

| Variabel | Nilai default | Keterangan |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Koneksi antar container |
| `LLM_MODEL` | `llama3.1:8b-instruct-q4_K_M` | Ganti ke `qwen2.5:3b` untuk server CPU |
| `DEFAULT_TOP_K` | `5` | Harus sama dengan yang dipakai di skripsi |
| `OLLAMA_NUM_CTX` | `4096` | Harus sama dengan yang dipakai di skripsi |
