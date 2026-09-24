# UPI Chatbot — RAG-Based Information System

Sistem chatbot cerdas berbasis AI untuk menjawab pertanyaan seputar Universitas Pendidikan Indonesia (UPI) dengan akurat berdasarkan dokumen resmi universitas.

---

## 📋Persiapan Sebelum Instalasi

Sebelum menggunakan aplikasi ini, pastikan komputermu (Windows) sudah terinstall software berikut:

1. **Python 3.10+**: [Download di sini](https://www.python.org/downloads/). Pastikan kamu mencentang opsi **"Add Python to PATH"** saat instalasi.
2. **Node.js**: [Download di sini](https://nodejs.org/). Dibutuhkan untuk menjalankan tampilan antarmuka (frontend).
3. **Ollama**: [Download di sini](https://ollama.com/). Dibutuhkan sebagai mesin utama AI (LLM) yang berjalan secara lokal di komputermu.

Setelah menginstall Ollama, buka **Command Prompt (CMD)** atau **PowerShell** dan jalankan perintah ini untuk mengunduh model AI (pastikan internet lancar):
```bash
ollama run llama3.1:8b-instruct-q4_K_M
```
*(Catatan: Aplikasi ini secara default dikonfigurasi untuk menggunakan model di atas. Kamu bisa menutup CMD setelah download selesai).*

---

## 🚀 Cara Pemasangan & Penggunaan Aplikasi

Aplikasi ini sudah dilengkapi dengan *Launcher* (sistem otomatis), jadi kamu tidak perlu mengetik perintah coding apa pun untuk menjalankannya.

### 1. Memulai Chatbot
Untuk menjalankan chatbot dan mulai bertanya:
- Cari file **`UPI-Chatbot-Launcher.exe`** di dalam folder utama project ini.
- **Klik ganda (Double-click)** file tersebut.
- *Hanya pada saat pertama kali dijalankan*, aplikasi akan mengunduh dan menginstall semua kebutuhan sistem secara otomatis di latar belakang (mungkin butuh beberapa menit tergantung koneksi internet).
- Setelah selesai, browser akan otomatis terbuka di `http://localhost:3000` yang menampilkan antarmuka chatbot.

### 2. Menambah Data Dokumen Baru (PDF) - *Khusus Admin*
Aplikasi ini membaca data dari dokumen PDF. Jika kamu memiliki hak akses Admin, kamu bisa menambahkan dokumen PDF baru agar AI menjadi lebih pintar langsung dari dalam aplikasi:
1. **Login** ke dalam aplikasi menggunakan akun Admin.
2. Buka menu **Profil** (Profile).
3. Klik menu **Tambahkan PDF**.
4. Isi detail dokumen yang diminta dan tekan **Upload** file PDF-nya.
5. Tunggu hingga proses selesai. Sistem akan otomatis memproses dan memasukkan dokumen tersebut ke otak AI!

---

## 🛠️ Troubleshooting

- **Aplikasi Chatbot Lambat / Lemot?**
  Pastikan Ollama menggunakan kartu grafis (GPU) komputermu. Buka **Settings Windows → System → Display → Graphics**, tambahkan `ollama.exe` dan `ollama app.exe`, lalu atur ke **High Performance**. Setelah itu *Quit/Keluar* dari Ollama di icon kanan bawah taskbar, lalu buka kembali.
  
- **Error Saat Pertama Kali Klik Launcher?**
  Pastikan Python dan Node.js sudah benar-benar terinstall dan masuk ke dalam "PATH" komputermu. Buka CMD dan ketik `python --version` serta `npm --version` untuk memastikan komputermu mendeteksinya.

---
*Dibuat khusus untuk keperluan Universitas Pendidikan Indonesia (UPI).*
