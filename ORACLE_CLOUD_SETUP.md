# Setup Oracle Cloud Free Tier — Chatbot RAG UPI

> **Kenapa Oracle Cloud?**
> Oracle memberi VM **4 OCPU ARM + 24 GB RAM gratis selamanya** (bukan trial 30 hari).
> Cukup untuk menjalankan Ollama + FastAPI backend + Next.js frontend 24/7 tanpa biaya.
> Perlu kartu kredit untuk verifikasi identitas, tapi tidak ditagih selama memakai
> layanan Free Tier.

---

## BAGIAN 1 — Daftar & Buat Akun Oracle Cloud

1. Buka https://www.oracle.com/cloud/free/ → klik **Start for free**

2. Isi form:
   - **Country:** Indonesia
   - **Email:** pakai email aktif (akan dapat verifikasi)
   - **Password:** buat password baru

3. Verifikasi email → masuk ke Oracle Cloud Console

4. Pilih **Home Region** → pilih `ap-singapore-1` (Singapore) — paling dekat ke Indonesia,
   latency rendah. **Tidak bisa diubah setelah dipilih.**

5. Masukkan data kartu kredit/debit untuk verifikasi. Oracle tidak menagih selama
   kamu hanya memakai Free Tier resources.

---

## BAGIAN 2 — Buat VM Instance (Server)

1. Di Oracle Cloud Console → **Compute** → **Instances** → **Create instance**

2. **Name:** `upi-rag-server` (bebas)

3. **Image & Shape:**
   - Klik **Change image** → pilih **Ubuntu** → pilih `Ubuntu 22.04 LTS`
   - Klik **Change shape** → pilih tab **Ampere** → pilih `VM.Standard.A1.Flex`
   - Set: **OCPUs = 4**, **Memory = 24 GB** ← ini Free Tier, tidak ditagih

4. **Networking:**
   - Biarkan default (VCN baru dibuat otomatis)
   - Centang **Assign a public IPv4 address** ✅

5. **SSH keys:**
   - Pilih **Generate a key pair for me**
   - Klik **Save private key** → simpan file `.key` di laptop kamu
     (contoh: `D:\Project\oracle_key.key`)

6. Klik **Create** → tunggu status berubah menjadi 🟢 **Running** (~2-3 menit)

7. Catat **Public IP address** dari halaman detail instance (contoh: `168.138.xxx.xxx`)

---

## BAGIAN 3 — Buka Port di Firewall Oracle

Oracle memblokir semua port secara default. Harus dibuka manual.

1. Di halaman instance → scroll bawah → klik nama **VCN** (Virtual Cloud Network)

2. Klik **Security Lists** → klik **Default Security List**

3. Klik **Add Ingress Rules** → tambahkan rules berikut satu per satu:

   | Source CIDR | Protocol | Port | Keterangan |
   |---|---|---|---|
   | `0.0.0.0/0` | TCP | `80` | HTTP |
   | `0.0.0.0/0` | TCP | `443` | HTTPS |
   | `0.0.0.0/0` | TCP | `3000` | Frontend Next.js |
   | `0.0.0.0/0` | TCP | `8000` | Backend FastAPI |

   > Port 22 (SSH) sudah terbuka otomatis. Port 11434 (Ollama) TIDAK perlu dibuka ke publik — hanya diakses antar container di dalam server.

---

## BAGIAN 4 — SSH ke Server & Install Docker

### Di laptop kamu (PowerShell/CMD):

```powershell
# Perbaiki permission key (Windows)
icacls "D:\Project\oracle_key.key" /inheritance:r /grant:r "$env:USERNAME:R"

# SSH ke server
ssh -i "D:\Project\oracle_key.key" ubuntu@168.138.xxx.xxx
```

### Di dalam server (setelah SSH berhasil):

```bash
# Update sistem
sudo apt update && sudo apt upgrade -y

# Install Docker (cara resmi)
curl -fsSL https://get.docker.com | sh

# Tambah user ubuntu ke grup docker (tidak perlu sudo tiap docker command)
sudo usermod -aG docker ubuntu

# Aktifkan grup baru (atau logout lalu login ulang)
newgrp docker

# Verifikasi Docker jalan
docker --version
docker compose version
```

---

## BAGIAN 5 — Upload Dataset & Clone Repo

### Di laptop kamu (PowerShell), bukan di server:

```powershell
# Clone repo ke server
ssh -i "D:\Project\oracle_key.key" ubuntu@168.138.xxx.xxx "git clone https://github.com/Kallendx82/Chatbot-RAG-UPI.git"

# Upload FAISS index (file besar ~1-2GB, tunggu beberapa menit)
scp -i "D:\Project\oracle_key.key" -r "D:\Project\RAG_UPI\Dataset\_pipeline\index" ubuntu@168.138.xxx.xxx:~/Chatbot-RAG-UPI/Dataset/_pipeline/

# Upload chunks metadata (diperlukan backend)
scp -i "D:\Project\oracle_key.key" "D:\Project\RAG_UPI\Dataset\_pipeline\chunked\chunks.jsonl" ubuntu@168.138.xxx.xxx:~/Chatbot-RAG-UPI/Dataset/_pipeline/chunked/
```

> ⏱️ Upload ~1-2GB ke Singapore dari Indonesia: estimasi 5-15 menit tergantung koneksi.

---

## BAGIAN 6 — Konfigurasi & Jalankan Aplikasi

### Di server:

```bash
cd ~/Chatbot-RAG-UPI

# Buka file docker-compose.yml untuk edit model
nano "Source code/docker-compose.yml"
```

Ubah baris ini:
```yaml
- LLM_MODEL=llama3.1:8b-instruct-q4_K_M
```
Menjadi (model lebih ringan untuk CPU server):
```yaml
- LLM_MODEL=qwen2.5:3b
```

Simpan: `Ctrl+O` → `Enter` → `Ctrl+X`

```bash
# Jalankan Ollama dulu, lalu pull model
cd "Source code"
docker compose up ollama -d

# Tunggu Ollama siap (~30 detik), lalu pull model
sleep 30
docker compose exec ollama ollama pull qwen2.5:3b

# Setelah model selesai di-pull (~1-2GB), jalankan semua
docker compose up -d

# Cek semua container jalan
docker compose ps

# Cek backend sehat
curl http://localhost:8000/health
```

Output yang diharapkan:
```
NAME        STATUS    PORTS
backend     running   0.0.0.0:8000->8000/tcp
frontend    running   0.0.0.0:3000->3000/tcp
ollama      running   0.0.0.0:11434->11434/tcp
```

---

## BAGIAN 7 — Arahkan Domain ke VPS

Domain `upi.ragupi.my.id` sudah di Cloudflare. Ubah DNS record:

1. Login ke Cloudflare → pilih domain `ragupi.my.id`

2. Klik **DNS** → **Records**

3. Cari record `upi` yang ada (mungkin menunjuk ke IP laptop lama) → klik **Edit**

4. Ubah:
   - **Type:** A
   - **Name:** upi
   - **IPv4 address:** `168.138.xxx.xxx` ← IP server Oracle kamu
   - **Proxy status:** DNS only (abu-abu) untuk test awal; bisa aktifkan Proxy setelah berhasil

5. Save → tunggu propagasi DNS ~1-5 menit

6. Test di browser: `http://upi.ragupi.my.id:3000`

> **Catatan:** jika ingin akses tanpa port (http://upi.ragupi.my.id), pasang Nginx sebagai
> reverse proxy (lihat Bagian 8 opsional).

---

## BAGIAN 8 (Opsional) — Nginx Reverse Proxy (tanpa port di URL)

```bash
# Install Nginx
sudo apt install nginx -y

# Buat konfigurasi
sudo nano /etc/nginx/sites-available/upi-rag
```

Isi dengan:
```nginx
server {
    listen 80;
    server_name upi.ragupi.my.id;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /backend-api/ {
        rewrite ^/backend-api/(.*) /$1 break;
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_read_timeout 180s;
    }
}
```

```bash
# Aktifkan konfigurasi
sudo ln -s /etc/nginx/sites-available/upi-rag /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Sekarang akses: `http://upi.ragupi.my.id` (tanpa port)

---

## Cara Update Kode Setelah Ada Perubahan

```bash
# Di server
cd ~/Chatbot-RAG-UPI
git pull origin main
cd "Source code"
docker compose build --no-cache backend frontend
docker compose up -d
```

---

## Troubleshooting Umum

| Masalah | Solusi |
|---|---|
| Container tidak jalan | `docker compose logs backend` atau `docker compose logs frontend` |
| Backend 500 | `docker compose logs backend` → cek apakah FAISS index terbaca |
| Ollama lambat | Normal di CPU; `qwen2.5:3b` lebih cepat dari `llama3.1:8b` |
| Domain tidak terbuka | Cek DNS propagation di https://dnschecker.org → ketik `upi.ragupi.my.id` |
| SSH timeout | Cek Security List Oracle → pastikan port 22 terbuka |
| `Permission denied` saat SCP | `icacls oracle_key.key /inheritance:r /grant:r "%USERNAME%:R"` |

---

## Ringkasan Spesifikasi Deployment

| Komponen | Nilai |
|---|---|
| Provider | Oracle Cloud Free Tier |
| Region | ap-singapore-1 |
| Shape | VM.Standard.A1.Flex (ARM) |
| CPU | 4 OCPU |
| RAM | 24 GB |
| Storage | 50 GB boot (free) |
| Biaya | **Rp 0 / bulan** |
| Model di server | `qwen2.5:3b` (CPU-friendly) |
| Model untuk sidang | `llama3.1:8b` di laptop (GPU RTX-4050) |
