# Implementasi Snort dan IPTables untuk Deteksi serta Pencegahan Serangan Jaringan dengan Notifikasi Telegram

> Source: https://kd-cibiru.upi.edu/index.php/daftar-kategori/prodi-tekkom/artikel-tekkom/implementasi-snort-dan-iptables-untuk-deteksi-serta-pencegahan-serangan-jaringan-dengan-notifikasi-telegram

Implementasi Snort dan IPTables untuk Deteksi serta Pencegahan Serangan Jaringan dengan Notifikasi Telegram
23 Mei 2025
Admin TEKKOM
Artikel TEKKOM
Implementasi Snort dan IPTables untuk Deteksi serta Pencegahan Serangan Jaringan dengan Notifikasi Telegram

Keamanan jaringan menjadi salah satu aspek krusial yang tidak dapat diabaikan. Serangan siber seperti port scanning, brute force, dan distributed denial-of-service (DDoS) dapat mengganggu bahkan melumpuhkan layanan penting dalam suatu sistem informasi. Oleh karena itu, penerapan sistem deteksi dan pencegahan intrusi (Intrusion Detection and Prevention System/IDPS) menjadi langkah strategis untuk menjaga integritas dan ketersediaan infrastruktur jaringan.

Salah satu solusi efektif yang dapat diterapkan dalam skala menengah hingga besar adalah integrasi antara Snort sebagai sistem deteksi intrusi (IDS), IPTables sebagai alat pencegah (firewall), serta Telegram Bot sebagai media notifikasi real-time kepada administrator.

Mengenal Komponen Utama

Snort
Snort adalah sistem IDS berbasis open-source yang mampu menganalisis lalu lintas jaringan secara real-time dan mendeteksi berbagai jenis serangan berdasarkan aturan-aturan yang telah ditetapkan.
IPTables
IPTables merupakan utilitas firewall pada sistem operasi Linux yang digunakan untuk memfilter paket jaringan. Dalam konteks ini, IPTables akan bekerja sebagai sistem pencegahan serangan dengan memblokir IP atau koneksi mencurigakan.
Telegram Bot
Telegram menyediakan API bot yang memungkinkan pengiriman pesan otomatis. Bot ini akan dimanfaatkan untuk mengirimkan pemberitahuan kepada administrator ketika Snort mendeteksi aktivitas mencurigakan.

Arsitektur Sistem

Alur kerja sistem deteksi dan pencegahan ini dapat dijelaskan sebagai berikut:

Snort memantau lalu lintas jaringan berdasarkan rule yang telah dikonfigurasi.
Jika terdeteksi aktivitas mencurigakan, Snort akan mencatatnya dalam log atau mengeksekusi script tertentu.
Script tersebut kemudian dapat mengeksekusi perintah IPTables untuk memblokir IP sumber serangan.
Bersamaan dengan itu, bot Telegram akan mengirim notifikasi yang berisi detail serangan (waktu, IP sumber, jenis serangan) kepada administrator.

Langkah-Langkah Implementasi

Instalasi Snort dan IPTables
Instal Snort menggunakan manajer paket Linux atau kompilasi manual.
Konfigurasikan rule Snort yang sesuai dengan pola serangan yang ingin dideteksi.
Pastikan IPTables aktif dan memiliki aturan dasar untuk mengizinkan dan memblokir koneksi.
Integrasi dengan Script Otomatis
Buat script bash atau Python yang membaca log Snort dan mengeksekusi perintah IPTables untuk memblokir IP berbahaya.
Script ini juga harus memanggil API Telegram untuk mengirim pesan.
Pembuatan Telegram Bot
Buat bot melalui BotFather di Telegram dan simpan token-nya.
Gunakan curl atau requests (jika menggunakan Python) untuk mengirim pesan melalui API bot Telegram.
Otomatisasi dan Monitoring
Integrasikan script ke dalam cron job atau daemon agar berjalan secara otomatis saat serangan terdeteksi.
Monitoring log Snort secara berkala untuk validasi.

Manfaat dan Keunggulan

Pencegahan aktif: Kombinasi Snort dan IPTables tidak hanya mendeteksi serangan tetapi juga langsung memblokirnya.
Notifikasi real-time: Telegram memungkinkan administrator mendapatkan informasi secara instan tanpa perlu membuka log secara manual.
Open-source dan fleksibel: Semua komponen bersifat gratis dan dapat dikustomisasi sesuai kebutuhan organisasi.

Integrasi antara Snort, IPTables, dan Telegram merupakan solusi cerdas dan efisien untuk meningkatkan keamanan jaringan secara proaktif. Dengan kemampuan mendeteksi serangan secara dini, memblokir sumber ancaman, serta memberikan notifikasi instan, sistem ini mampu membantu administrator dalam menjaga kestabilan dan keamanan infrastruktur TI, terutama dalam lingkungan jaringan yang dinamis seperti cloud computing atau data center modern.

Dilihat: 393
Previous article: Implementasi Honeypot sebagai Sistem Deteksi dan Pencegahan Serangan Jaringan Server Sebelum
Next article: Implementasi Suricata sebagai Sistem Deteksi dan Pencegahan Serangan Jaringan Server Berikut
FaLang translation system by Faboba
