# BAB III — Rancangan Prototipe Antarmuka Awal (Figma)

> Tempel ke bagian BAB III yang membahas perancangan antarmuka (UI/UX design)
> sebelum tahap implementasi. Sisipkan tangkapan layar prototipe Figma
> sebagai gambar bernomor (mis. Gambar 3.x, 3.y) mengikuti paragraf yang
> merujuknya. Dua tangkapan layar yang dirujuk di bawah: (1) layar utama
> percakapan dengan panel Retrieved Context terbuka, dan (2) panel
> Pengaturan (Settings) dengan opsi tema, bahasa, dan pemilihan model.

## 3.x Perancangan Antarmuka Pengguna (Prototyping)

Sebelum tahap implementasi teknis dimulai, dilakukan perancangan antarmuka
pengguna (*user interface*) menggunakan perangkat lunak desain kolaboratif
Figma untuk memvalidasi tata letak, arsitektur informasi, dan alur interaksi
sistem sebelum kode aplikasi sesungguhnya ditulis. Pendekatan ini dipilih
agar keputusan desain — seperti penempatan riwayat percakapan, struktur
panel sumber kutipan, dan susunan menu pengaturan — dapat dievaluasi dan
diiterasi secara visual tanpa biaya pengembangan penuh, sesuai praktik umum
dalam metodologi *Design and Development Research* pada tahap perancangan
produk sebelum pengembangan (*development*). Prototipe ini bersifat statis
dan interaktif secara terbatas: seluruh data yang ditampilkan — termasuk
skor kemiripan dokumen, judul sumber, dan contoh pertanyaan — merupakan
data contoh (*dummy/placeholder*) yang disusun manual, **bukan hasil
pemrosesan sungguhan dari sistem RAG**, karena pada tahap ini backend,
model bahasa, dan basis data vektor belum dikembangkan. Prototipe dirancang
menggunakan komponen desain generik (ikon, tipografi, dan palet warna) yang
kemudian menjadi acuan visual bagi implementasi antarmuka sesungguhnya pada
tahap pengembangan selanjutnya.

Rancangan layar utama (Gambar 3.x) menggambarkan tata letak percakapan
dengan tiga area utama: sidebar kiri berisi tombol "New Chat" dan daftar
riwayat percakapan sebelumnya beserta cap waktu relatif (mis. "2 hours
ago", "Yesterday", "2 days ago"); area tengah berisi judul aplikasi
"University AI Chatbot" dengan indikator status "Connected to Knowledge
Base", pemilih model ("🦙 LLaMA"), dan tampilan sambutan (*welcome screen*)
berisi ikon topi wisuda, judul sambutan, deskripsi singkat fungsi aplikasi,
serta empat kartu pertanyaan cepat (*quick-reply*) dalam grid 2×2 seperti
"What are the admission requirements?" dan "Tell me about scholarship
opportunities"; serta kolom input percakapan di bagian bawah dengan
*placeholder* "Ask about university information..." dan tombol kirim.
Rancangan ini juga sudah mengantisipasi kondisi jaringan bermasalah sejak
tahap desain, ditandai dengan notifikasi *toast* "Possible network issues
detected" beserta tautan "Learn more" yang muncul di atas kolom input —
sebuah elemen desain yang kemudian diwujudkan pada implementasi akhir
sebagai spanduk peringatan status backend (*offline*/*degraded*) di atas
kolom input percakapan.

Bagian kanan pada rancangan (Gambar 3.x) menampilkan panel "Retrieved
Context" yang dapat ditutup (ikon silang), berfungsi menampilkan potongan
dokumen (*chunk*) yang berhasil diambil sistem sebagai konteks jawaban.
Setiap kartu sumber pada panel ini menampilkan judul dokumen (mis. "Student
Handbook 2026.pdf", "Admission Guide.pdf"), skor kemiripan dalam persentase
(94%, 87%), lokasi kutipan (nomor halaman dan kategori/bagian, mis. "Page
12 • Academic Programs"), serta cuplikan teks dari dokumen tersebut. Bagian
bawah panel menampilkan ringkasan agregat berupa jumlah total potongan yang
diambil ("Total chunks: 3") dan rata-rata skor kemiripan ("Avg similarity:
88%"). Rancangan panel ini menjadi cetak biru langsung bagi fitur sitasi
sumber dan panel debug retrieval yang diimplementasikan pada tahap
pengembangan (lihat BAB IV bagian Fitur Sitasi Sumber dan Fitur Panel
Debug), meski pada implementasi akhir informasi metadata yang ditampilkan
diperluas (mis. ID potongan, ID dokumen, jenis sumber) melebihi apa yang
tergambar pada prototipe awal ini.

Rancangan panel Pengaturan (Gambar 3.y) memperlihatkan menu "Settings"
dengan tiga kelompok kontrol: bagian "APPEARANCE" berupa tiga tombol pilihan
tema (Light/Dark/System) dengan ikon matahari, bulan, dan monitor; bagian
"LANGUAGE" berupa menu tarik-turun (*dropdown*) dengan opsi bendera Inggris
dan Indonesia; serta daftar pilihan model bahasa dalam bentuk tombol radio,
yaitu "LLaMA 4" (Meta's open-source LLM), "Gemma 4" (Google DeepMind LLM),
dan "Extractive (No LLM)" untuk mode pengambilan kutipan langsung tanpa
model generatif. Footer panel menampilkan versi aplikasi ("University RAG
System · v1.0"). Perbandingan antara rancangan ini dengan implementasi
akhir (`SettingsModal.tsx`, dibahas di BAB IV) menunjukkan evolusi desain
selama pengembangan: struktur inti (tema tiga-pilihan, bahasa, pilihan
model berbasis radio) dipertahankan, namun daftar model pada implementasi
akhir berubah signifikan — opsi "Gemma 4" pada prototipe tidak
diimplementasikan secara identik, digantikan oleh varian model yang
benar-benar tersedia melalui Ollama (`llama3.1:8b-instruct-q4_K_M`,
`qwen2.5:3b`, `qwen3.5:4b-q4_K_M`, `gemma4:e2b`, dan lainnya) — dan dua
kontrol tambahan (*slider* Top-K retrieval dan Temperature, serta sakelar
Mode Debug) ditambahkan pada implementasi akhir yang tidak ada pada
rancangan prototipe awal, sebagai hasil kebutuhan teknis yang baru
teridentifikasi selama tahap pengembangan backend RAG.
