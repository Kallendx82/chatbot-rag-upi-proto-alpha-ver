# Integrasi React Agent dengan YOLOv8 dan RetroEV AL-Augmented Generation untuk Identifikasi Penyakit Tanaman pada Aplikasi Chatbot

> Source: https://kd-cibiru.upi.edu/index.php/daftar-kategori/prodi-tekkom/berita-tekom/integrasi-react-agent-dengan-yolov8-dan-retroev-al-augmented-generation-untuk-identifikasi-penyakit-tanaman-pada-aplikasi-chatbot

Integrasi React Agent dengan YOLOv8 dan RetroEV AL-Augmented Generation untuk Identifikasi Penyakit Tanaman pada Aplikasi Chatbot
03 September 2025
Admin TEKKOM
Berita TEKKOM
Integrasi React Agent dengan YOLOv8 dan RetroEV AL-Augmented Generation untuk Identifikasi Penyakit Tanaman pada Aplikasi Chatbot

Pertanian modern kini semakin mengandalkan teknologi kecerdasan buatan untuk meningkatkan produktivitas dan ketepatan diagnosis penyakit tanaman. Salah satu tantangan utama petani adalah mendeteksi penyakit tanaman secara cepat dan akurat, terutama pada skala luas. Proses identifikasi manual sering kali memakan waktu dan bergantung pada keahlian individu.
Untuk menjawab permasalahan ini, dikembangkan sebuah sistem chatbot cerdas yang mampu melakukan deteksi penyakit tanaman secara otomatis menggunakan kombinasi React Agent, YOLOv8, dan RetroEV AL-Augmented Generation. Integrasi ketiga teknologi ini memungkinkan pengguna mendapatkan hasil diagnosis visual sekaligus penjelasan deskriptif secara real-time.

Konsep dan Arsitektur Sistem

Sistem ini dirancang dengan pendekatan AI-driven conversational assistant, di mana chatbot tidak hanya berfungsi menjawab pertanyaan, tetapi juga menganalisis citra daun tanaman yang diunggah pengguna untuk mendeteksi adanya penyakit.
Arsitektur sistem terdiri dari tiga komponen utama:

React Agent (Reasoning and Action Agent)
React Agent berperan sebagai pengendali utama interaksi. Dengan pendekatan Reasoning + Acting, agent dapat menggabungkan pemrosesan bahasa alami (NLP) dengan eksekusi tugas visual, seperti mengirim data gambar ke model YOLOv8 atau mengelola hasil keluaran dari RetroEV.

YOLOv8 (You Only Look Once Version 8)
YOLOv8 digunakan sebagai model deteksi objek visual berbasis deep learning yang dioptimalkan untuk mendeteksi berbagai jenis penyakit daun seperti bercak daun, hawar, dan jamur.
Model ini dilatih menggunakan dataset penyakit tanaman (misalnya PlantVillage Dataset) dan menghasilkan bounding box pada bagian daun yang terinfeksi, lengkap dengan label penyakit dan tingkat kepercayaannya.

RetroEV AL-Augmented Generation
Komponen ini berfungsi sebagai modul penalaran dan penjelasan berbasis pengetahuan. Setelah YOLOv8 mendeteksi jenis penyakit, hasilnya dikirim ke RetroEV yang akan memanfaatkan retrieval-augmented generation (RAG) dengan tambahan active learning (AL).
Tujuannya adalah menghasilkan deskripsi penyakit yang lebih kontekstual, memberikan penjelasan ilmiah, saran penanganan, dan rekomendasi tindakan pencegahan berdasarkan database agronomi yang terus diperbarui.

Proses Kerja Sistem

Berikut tahapan alur kerja sistem secara keseluruhan:

Input Data:
Pengguna mengunggah foto daun tanaman melalui antarmuka chatbot berbasis React.

Deteksi Visual:
React Agent memanggil model YOLOv8 untuk menganalisis gambar dan mengidentifikasi area daun yang mengandung penyakit.

Analisis Pengetahuan:
Hasil klasifikasi dikirim ke RetroEV AL-Augmented Generation untuk melakukan retrieval dari basis data penyakit dan menghasilkan penjelasan diagnostik.

Respon Chatbot:
Chatbot menampilkan hasil deteksi dalam bentuk gambar beranotasi, disertai penjelasan penyakit, penyebab biologis, dan rekomendasi tindakan yang dapat dilakukan petani.

Active Learning Feedback:
Pengguna dapat menandai hasil deteksi sebagai “akurasi tinggi” atau “kurang tepat”. Data umpan balik ini digunakan oleh sistem untuk memperbarui model secara bertahap (self-improving system).

Hasil Implementasi

Uji coba sistem dilakukan dengan 1.000 gambar daun tanaman padi, tomat, dan cabai.
Hasil menunjukkan tingkat akurasi deteksi YOLOv8 mencapai 96,8%, sementara integrasi dengan RetroEV meningkatkan relevansi penjelasan hingga 93% berdasarkan evaluasi pengguna.
Sistem ini mampu memberikan hasil diagnosis dan rekomendasi kurang dari 3 detik, menjadikannya efisien untuk penggunaan lapangan.

Keunggulan Integrasi

Reaktif dan Kontekstual: React Agent memungkinkan chatbot beradaptasi terhadap pertanyaan pengguna dengan logika multi-modal.

Visual Intelligence: YOLOv8 memberikan deteksi penyakit berbasis citra yang cepat dan akurat.

Generatif Berbasis Pengetahuan: RetroEV AL-Augmented Generation memperkaya hasil dengan informasi ilmiah yang relevan.

Pembelajaran Berkelanjutan: Sistem mampu meningkatkan performa dari waktu ke waktu melalui active learning feedback loop.

Integrasi antara React Agent, YOLOv8, dan RetroEV AL-Augmented Generation membuka jalan bagi lahirnya chatbot agrikultur cerdas yang mampu memberikan diagnosis penyakit tanaman secara cepat, akurat, dan informatif.
Inovasi ini menjadi langkah strategis menuju pertanian presisi berbasis kecerdasan buatan, mendukung efisiensi waktu, peningkatan hasil panen, serta pengambilan keputusan berbasis data di kalangan petani dan peneliti agronomi.

Dilihat: 166
Previous article: Mahasiswa Teknik Komputer UPI Cibiru Raih Juara 1 Internasional Short Film Competition Sebelum
Next article: Dosen Teknik Komputer UPI Menjadi Pembicara pada Applied Informatics International Webinar Series 2 (2025) Berikut
FaLang translation system by Faboba
