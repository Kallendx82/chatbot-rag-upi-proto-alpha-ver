# UPI Chatbot — RAG-Based Information System

Sistem chatbot cerdas berbasis AI untuk menjawab pertanyaan seputar Universitas Pendidikan Indonesia (UPI) dengan akurat berdasarkan dokumen resmi universitas.

---

## 📋 Prasyarat (Persiapan Sebelum Instalasi)

Sebelum menggunakan aplikasi ini, pastikan komputermu (Windows) sudah terinstall software berikut:

1. **Python 3.10+**: [Download di sini](https://www.python.org/downloads/). Pastikan kamu mencentang opsi **"Add Python to PATH"** saat instalasi.
2. **Node.js**: [Download di sini](https://nodejs.org/). Dibutuhkan untuk menjalankan tampilan antarmuka (frontend).
3. **Ollama**: [Download di sini](https://ollama.com/). Dibutuhkan sebagai mesin utama AI (LLM) yang berjalan secara lokal di komputermu.

Setelah menginstall Ollama, buka **Command Prompt (CMD)** atau **PowerShell** dan jalankan perintah ini untuk mengunduh model AI (pastikan internet lancar):
```bash
ollama run qwen2.5:3b
```
*(Catatan: Aplikasi ini secara default dikonfigurasi untuk menggunakan model di atas. Kamu bisa menutup CMD setelah download selesai).*

---

## 🚀 Cara Pemasangan & Penggunaan Aplikasi

Aplikasi ini sudah dilengkapi dengan *Launcher* (sistem otomatis), jadi kamu tidak perlu mengetik perintah coding apa pun untuk menjalankannya.

### 1. Memulai Chatbot (Aplikasi Utama)
Untuk menjalankan chatbot dan mulai bertanya:
- Cari file **`UPI-Chatbot-Launcher.exe`** di dalam folder utama project ini.
- **Klik ganda (Double-click)** file tersebut.
- *Hanya pada saat pertama kali dijalankan*, aplikasi akan mengunduh dan menginstall semua kebutuhan sistem secara otomatis di latar belakang (mungkin butuh beberapa menit tergantung koneksi internet).
- Setelah selesai, browser akan otomatis terbuka di `http://localhost:3000` yang menampilkan antarmuka chatbot.

### 2. Menambah Data Dokumen Baru (PDF)
Aplikasi ini membaca data dari dokumen. Jika kamu ingin menambahkan dokumen PDF baru agar AI menjadi lebih pintar:
- Cari file **`Add-New-PDF.exe`** di dalam folder utama project ini.
- **Klik ganda (Double-click)** file tersebut.
- Akan muncul jendela untuk memilih folder berisi file PDF yang ingin ditambahkan beserta nama kategorinya.
- Tunggu hingga proses selesai. Aplikasi akan otomatis membaca, mengekstrak, dan memasukkannya ke otak AI.
- **Penting:** Setelah proses selesai, kamu harus merestart (tutup dan buka ulang) aplikasi chatbot utama agar dokumen baru tersebut dapat dikenali oleh sistem.

---

## 🛠️ Troubleshooting (Jika Ada Masalah)

- **Aplikasi Chatbot Lambat / Lemot?**
  Pastikan Ollama menggunakan kartu grafis (GPU) komputermu. Buka **Settings Windows → System → Display → Graphics**, tambahkan `ollama.exe` dan `ollama app.exe`, lalu atur ke **High Performance**. Setelah itu *Quit/Keluar* dari Ollama di icon kanan bawah taskbar, lalu buka kembali.
  
- **Error Saat Pertama Kali Klik Launcher?**
  Pastikan Python dan Node.js sudah benar-benar terinstall dan masuk ke dalam "PATH" komputermu. Buka CMD dan ketik `python --version` serta `npm --version` untuk memastikan komputermu mendeteksinya.

---
*Dibuat khusus untuk keperluan Universitas Pendidikan Indonesia (UPI).*
