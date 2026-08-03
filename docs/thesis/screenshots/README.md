# Screenshot Antarmuka Asli — Bukti Implementasi BAB IV

Placeholder gambar sudah disisipkan langsung di `../BAB_IV_fitur_aplikasi.md`
(sintaks `![...](screenshots/nama_file.png)` + keterangan "Gambar 4.x").
Simpan screenshot yang ditampilkan Claude di percakapan ke folder ini
dengan nama **persis** seperti tabel di bawah — begitu file dengan nama
yang sama ada di sini, gambar langsung tampil saat dokumen dirender/di-
convert ke Word/PDF.

| Nama file | Dipakai di | Isi |
|---|---|---|
| `4x1_chat_jawaban_sitasi.png` | 4.x.1 (Gambar 4.1) | Layar chat, jawaban RAG + badge "Terverifikasi sumber" + 5 kartu sumber |
| `4x2_source_inspector.png` | 4.x.2 (Gambar 4.2) | Panel detail sumber (skor, chunk ID, document ID, tombol Buka PDF) |
| `4x3_settings_desktop.png` | 4.x.3 (Gambar 4.3) | Panel Pengaturan desktop (tema, bahasa, Top-K, Temperature, model, debug) |
| `4x4_debug_panel.png` | 4.x.4 (Gambar 4.4) | Panel Retrieval Debug (metrik latensi, pratinjau prompt, daftar chunk) |
| `4x5_admin_tambah_dokumen.png` | 4.x.5 (Gambar 4.5) | Halaman admin "Tambah Dokumen PDF" + Pengaturan Chunk terbuka |
| `4x6_statistik_ringkasan.png` | 4.x.6 (Gambar 4.6a) | Halaman Statistik — 3 kartu metrik + grafik pertanyaan per hari |
| `4x6_statistik_terpopuler.png` | 4.x.6 (Gambar 4.6b) | Halaman Statistik — daftar "Pertanyaan terpopuler" |
| `4x7_auth_modal_desktop.png` | 4.x.7 (Gambar 4.7) | Modal Masuk/Daftar pada tampilan desktop |
| `mobile_welcome.png` | 4.x.8 (Gambar 4.8a) | Layar sambutan pada viewport mobile (375×812) |
| `mobile_sidebar_drawer.png` | 4.x.8 (Gambar 4.8b) | Sidebar sebagai overlay drawer pada viewport mobile |
| `mobile_settings.png` | 4.x.8 (Gambar 4.8c) | Panel Pengaturan pada viewport mobile |
| `mobile_auth.png` | 4.x.8 (Gambar 4.8d) | Modal Masuk/Daftar pada viewport mobile |
| `tablet_padding_artifact.png` | 4.x.8 (Gambar 4.8e) | Contoh padding kanvas alat emulasi pada viewport tablet |

## Kenapa foldernya masih kosong

Claude tidak punya cara menulis file gambar langsung ke disk dari sisi
alat browser-nya (tool screenshot hanya mengembalikan gambar inline di
chat, tidak ada opsi "save to path"), dan sesi Bash/PowerShell yang
dipakai Claude berjalan di sandbox terpisah dari layar tempat panel
Browser dirender — sudah dikonfirmasi lewat percobaan screenshot level-OS
yang malah menangkap aplikasi lain, bukan panel Browser. Karena itu,
screenshot yang sudah ditampilkan Claude di riwayat percakapan perlu
disimpan manual: klik kanan gambar di chat → "Save image as" → simpan ke
folder ini dengan nama sesuai tabel di atas.

`4x4_debug_panel.png` dan panel Retrieval Debug sempat menunjukkan error
"Belum login" meski sudah login sebagai admin (kemungkinan bug kecil di
frontend, sudah ditandai terpisah untuk diperbaiki) — screenshot bisa
diambil ulang setelah itu diperbaiki, atau gunakan screenshot state error
tersebut sebagai catatan pengujian jika relevan.
