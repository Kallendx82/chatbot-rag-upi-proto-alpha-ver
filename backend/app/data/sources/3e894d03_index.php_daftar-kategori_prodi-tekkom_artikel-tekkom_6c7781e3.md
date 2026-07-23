# Artikel TEKKOM

> Source: https://kd-cibiru.upi.edu/index.php/daftar-kategori/prodi-tekkom/artikel-tekkom

Artikel TEKKOM
11 Jun 2025
Admin TEKKOM
Artikel TEKKOM
Implementasi Intrusion Detection System (IDS) Berbasis Deep Learning untuk Meningkatkan Mitigasi Serangan Cross Site Scripting (XSS)

Dalam era digital yang semakin kompleks, serangan siber menjadi ancaman nyata bagi keamanan aplikasi web. Salah satu jenis serangan yang sering terjadi adalah Cross Site Scripting (XSS), di mana penyerang menyisipkan skrip berbahaya ke dalam halaman web untuk mencuri data pengguna atau mengambil alih sesi pengguna.

Untuk menghadapi ancaman ini, pendekatan konvensional dalam mendeteksi intrusi dinilai belum cukup responsif dan adaptif terhadap pola serangan yang terus berkembang. Oleh karena itu, penerapan Intrusion Detection System (IDS) berbasis deep learning mulai dipertimbangkan sebagai solusi yang lebih canggih dan efisien.

Deep learning, khususnya arsitektur seperti Recurrent Neural Network (RNN) dan Convolutional Neural Network (CNN), memungkinkan sistem untuk mempelajari pola serangan XSS secara otomatis dari data lalu lintas web. Dengan kemampuan untuk menganalisis fitur kompleks dari input teks maupun kode yang mencurigakan, IDS berbasis deep learning mampu mendeteksi anomali secara lebih akurat dan dengan tingkat false positive yang lebih rendah dibandingkan metode tradisional.

Implementasi ini tidak hanya memberikan deteksi yang lebih presisi, tetapi juga mempercepat respons mitigasi terhadap potensi serangan. Dengan mengintegrasikan IDS ini dalam sistem keamanan web, pengembang dapat meningkatkan ketahanan aplikasi terhadap eksploitasi XSS sekaligus memberikan perlindungan proaktif bagi pengguna.

Langkah selanjutnya adalah mengembangkan dataset yang relevan, melatih model dengan data yang representatif, serta melakukan pengujian berkelanjutan untuk memastikan model dapat beradaptasi dengan teknik serangan baru yang terus bermunculan.

Dilihat: 286
10 Jun 2025
Admin TEKKOM
Artikel TEKKOM
Pengembangan Aplikasi Berbasis Mobile untuk Sistem Keamanan Data Menggunakan Enkripsi Caesar Cipher dan RC4

Kemajuan teknologi informasi telah mendorong perkembangan aplikasi mobile sebagai sarana utama dalam pertukaran data dan komunikasi digital. Namun, meningkatnya ketergantungan terhadap teknologi mobile juga diiringi dengan potensi ancaman terhadap keamanan data. Terutama dalam konteks pertukaran pesan (chatting), perlindungan terhadap isi komunikasi menjadi sangat penting guna menjaga kerahasiaan, integritas, dan keaslian data.

Untuk menjawab tantangan tersebut, pengembangan aplikasi berbasis mobile dengan sistem keamanan data yang kuat menjadi kebutuhan mendesak. Salah satu pendekatan yang dapat diimplementasikan adalah dengan menggabungkan dua metode enkripsi, yaitu Caesar Cipher sebagai teknik enkripsi klasik dan RC4 (Rivest Cipher 4) sebagai algoritma stream cipher modern. Kombinasi ini memberikan lapisan perlindungan ganda untuk menjaga keamanan pesan yang dikirim melalui aplikasi.

 

Tujuan Pengembangan

Pengembangan aplikasi ini bertujuan untuk:

Menyediakan platform komunikasi (chat) yang aman berbasis perangkat mobile.
Mengimplementasikan algoritma Caesar Cipher dan RC4 untuk melindungi pesan pengguna.
Menyediakan sistem enkripsi yang ringan namun cukup efektif untuk digunakan pada perangkat dengan sumber daya terbatas (mobile).
Metodologi Enkripsi

Caesar Cipher merupakan algoritma kriptografi klasik yang mengenkripsi pesan dengan cara menggeser setiap huruf dalam pesan sebanyak nilai tertentu. Meskipun secara kriptografi dianggap lemah, Caesar Cipher dapat digunakan sebagai lapisan awal obfuscation atau penyamaran pesan.

RC4 adalah algoritma enkripsi simetris yang bekerja dengan prinsip stream cipher, menghasilkan keystream yang digabungkan dengan plaintext menggunakan operasi XOR. RC4 dikenal cepat dan ringan, sehingga cocok untuk implementasi pada perangkat mobile, terutama untuk komunikasi data secara real-time seperti aplikasi chat.

RC4 digunakan dalam aplikasi ini sebagai lapisan utama dalam mengenkripsi pesan pengguna sebelum dikirimkan ke penerima.

 

Alur Sistem Aplikasi
Pengguna mengirim pesan melalui aplikasi mobile.
Pesan dienkripsi terlebih dahulu dengan Caesar Cipher untuk penyamaran dasar.
Hasil dari Caesar Cipher kemudian dienkripsi kembali menggunakan RC4 menggunakan kunci rahasia yang disepakati antar pengguna.
Pesan terenkripsi dikirim melalui server ke penerima.
Penerima mendekripsi pesan dengan urutan sebaliknya: pertama RC4, kemudian Caesar Cipher.
Pesan asli ditampilkan kepada penerima.

 

Keunggulan Sistem
Keamanan Berlapis: Kombinasi Caesar Cipher dan RC4 memberikan perlindungan ganda, menjadikan pesan lebih sulit untuk diretas secara langsung.
Efisiensi: RC4 adalah algoritma yang ringan dan cepat, cocok untuk aplikasi real-time.
Fleksibilitas: Sistem dapat dikembangkan di berbagai platform mobile seperti Android atau iOS dengan framework seperti Flutter atau React Native.
Kemudahan Implementasi: Caesar Cipher bersifat sederhana, cocok untuk aplikasi prototipe, pendidikan, atau tahap awal pengembangan sistem keamanan.

 

Tantangan dan Rekomendasi

Walaupun pendekatan ini efektif untuk tujuan edukatif dan pengembangan awal, Caesar Cipher secara kriptografi sangat lemah dan dapat dengan mudah dipecahkan. Oleh karena itu, dalam implementasi nyata yang lebih serius, disarankan untuk mengganti Caesar Cipher dengan metode enkripsi modern lainnya, seperti AES atau RSA, sebagai pelengkap RC4.

Selain itu, penting untuk:

Mengelola distribusi kunci RC4 secara aman.
Menghindari penggunaan RC4 dalam sistem berskala besar tanpa lapisan tambahan, karena RC4 juga memiliki sejumlah kelemahan yang telah ditemukan oleh para peneliti keamanan.

Pengembangan aplikasi mobile dengan fitur keamanan berbasis Caesar Cipher dan RC4 memberikan gambaran nyata tentang bagaimana kriptografi dapat diterapkan untuk meningkatkan keamanan komunikasi digital. Sistem ini cocok digunakan sebagai prototipe atau aplikasi edukatif dalam mempelajari konsep dasar enkripsi dan perlindungan data. Diharapkan, pengembangan ini dapat menjadi pijakan awal dalam menciptakan sistem komunikasi yang lebih aman dan andal di masa mendatang.

Dilihat: 430
09 Jun 2025
Admin TEKKOM
Artikel TEKKOM
Implementasi Layer 7 Protocol dan Simple Queue Menggunakan Mikrotik Berbasis Website dengan Notifikasi Telegram

Manajemen lalu lintas jaringan (traffic shaping) merupakan hal penting dalam menjaga performa dan kestabilan jaringan, terutama dalam lingkungan yang memiliki banyak pengguna dan aplikasi yang beragam. Mikrotik, sebagai salah satu perangkat jaringan yang banyak digunakan, menyediakan berbagai fitur canggih seperti Layer 7 Protocol dan Simple Queue untuk memantau, mengatur, dan membatasi penggunaan bandwidth sesuai kebutuhan.

Dalam artikel ini, akan dibahas bagaimana penerapan Layer 7 Protocol dan Simple Queue pada Mikrotik dapat diintegrasikan dengan antarmuka website serta didukung oleh sistem notifikasi otomatis melalui Telegram, guna memberikan pemantauan real-time terhadap aktivitas jaringan.

 

Konsep Dasar:

Layer 7 Protocol:

Layer 7 Protocol adalah metode filtering berbasis konten aplikasi (Application Layer) yang memungkinkan Mikrotik mendeteksi lalu lintas berdasarkan pola teks tertentu, misalnya mendeteksi akses ke situs streaming atau media sosial seperti YouTube atau TikTok.

Simple Queue:

Simple Queue digunakan untuk mengatur batas bandwidth berdasarkan IP address atau kelompok pengguna. Dengan konfigurasi yang tepat, administrator dapat memberikan prioritas tertentu, membatasi kecepatan download/upload, atau mengalokasikan bandwidth minimum.

Integrasi Website:

Antarmuka berbasis web dibangun menggunakan framework seperti PHP, Bootstrap, dan MySQL. Website ini menampilkan data queue aktif, penggunaan bandwidth, serta log aktivitas berdasarkan Layer 7 filtering yang telah ditentukan.

Notifikasi Telegram:

Dengan menggunakan Bot Telegram, sistem dapat dikonfigurasi untuk mengirimkan notifikasi otomatis apabila terjadi pelanggaran batas bandwidth, akses ke situs tertentu, atau penambahan IP baru ke dalam daftar pengawasan. Hal ini memungkinkan admin jaringan mendapatkan update secara instan tanpa harus memantau Mikrotik secara langsung.

 

Langkah Implementasi:

Setup Simple Queue:
Menuju Queues → Simple Queues
Tambahkan rule untuk IP tertentu, misalnya 192.168.88.10
Atur max-limit dan target sesuai kebutuhan
Pembuatan Web Interface:
Website menampilkan data dari Mikrotik menggunakan API (misal PHP + RouterOS API Library)
Tabel HTML menampilkan daftar user, kecepatan saat ini, status queue, dll.
Integrasi Bot Telegram:
Buat Bot Telegram → Dapatkan token dari BotFather
Gunakan script PHP atau Python untuk mengirim pesan ke grup/admin
Tambahkan cronjob atau pemicu berbasis waktu untuk memeriksa status queue atau Layer7 dan kirim notifikasi jika ada perubahan penting

 

Manfaat Implementasi:

Memberikan kontrol penuh terhadap penggunaan jaringan, khususnya pada jaringan lokal dengan banyak pengguna.
Memungkinkan pengawasan jarak jauh melalui Telegram.
Antarmuka website membuat pengelolaan lebih mudah dan efisien, cocok untuk lingkungan pendidikan, kantor, maupun warnet.

 

Integrasi Layer 7 Protocol dan Simple Queue pada Mikrotik dengan antarmuka website dan sistem notifikasi Telegram memberikan solusi yang efisien dan responsif dalam memantau serta mengatur lalu lintas jaringan. Implementasi ini sangat bermanfaat untuk administrator jaringan yang membutuhkan kontrol real-time terhadap aktivitas pengguna tanpa perlu pengawasan manual secara terus-menerus.

Dilihat: 818
04 Jun 2025
Admin TEKKOM
Artikel TEKKOM
Implementasi Snort dan IPTables untuk Deteksi dan Pencegahan Serangan Jaringan dengan Notifikasi Bot Telegram

Keamanan jaringan komputer merupakan aspek penting yang harus diperhatikan dalam pengelolaan sistem informasi modern. Ancaman seperti port scanning, serangan DDoS, dan eksploitasi celah keamanan dapat mengganggu stabilitas dan integritas sistem. Oleh karena itu, perlu diterapkan sistem deteksi dan pencegahan yang responsif dan terintegrasi.

Salah satu solusi yang banyak digunakan adalah kombinasi Snort sebagai sistem deteksi intrusi (IDS/IPS), IPTables sebagai firewall untuk tindakan pencegahan, serta Bot Telegram sebagai media notifikasi real-time kepada administrator jaringan.

 

Arsitektur Sistem

Implementasi ini terdiri dari tiga komponen utama:

Snort – Mendeteksi lalu lintas mencurigakan berdasarkan signature dan aturan yang telah ditentukan.
IPTables – Mengatur kebijakan pencegahan seperti pemblokiran IP atau port tertentu berdasarkan hasil deteksi Snort.

Telegram Bot – Mengirimkan peringatan otomatis ke ponsel admin jika terjadi serangan.

Keunggulan Sistem

Deteksi Real-Time: Snort mampu mendeteksi berbagai jenis serangan berdasarkan signature.
Pencegahan Otomatis: IP penyerang langsung diblokir melalui IPTables.
Respons Cepat: Admin mendapat notifikasi instan melalui Telegram untuk tindakan lebih lanjut.

Kesimpulan

Mengintegrasikan Snort dengan IPTables dan Bot Telegram adalah langkah strategis untuk memperkuat pertahanan jaringan secara otomatis dan real-time. Dengan sistem ini, serangan tidak hanya terdeteksi, tetapi juga dicegah serta diinformasikan kepada admin secara langsung, sehingga respons terhadap insiden keamanan dapat dilakukan dengan cepat dan tepat.

Dilihat: 261
03 Jun 2025
Admin TEKKOM
Artikel TEKKOM
Meningkatkan Keamanan Data Penduduk melalui Implementasi Enkripsi AES-128 dan Caesar Cipher pada Aplikasi Website

Di era digital saat ini, pengelolaan data penduduk secara daring telah menjadi kebutuhan utama dalam mendukung pelayanan publik yang efisien dan cepat. Namun, seiring dengan meningkatnya pemanfaatan teknologi, tantangan terhadap keamanan data juga semakin kompleks. Perlindungan terhadap informasi pribadi, seperti Nomor Induk Kependudukan (NIK), nama, dan alamat, menjadi sangat krusial untuk mencegah penyalahgunaan data oleh pihak yang tidak bertanggung jawab.

Salah satu pendekatan yang dapat diterapkan dalam menjaga kerahasiaan dan integritas data adalah dengan menggunakan metode enkripsi. Dua jenis enkripsi yang dapat diimplementasikan dalam aplikasi website adalah AES-128 (Advanced Encryption Standard) dan Caesar Cipher. Meskipun memiliki karakteristik yang berbeda, kombinasi keduanya dapat memberikan lapisan perlindungan tambahan terhadap data yang disimpan dan ditransmisikan melalui sistem digital.

 

AES-128: Enkripsi Kuat untuk Perlindungan Data Sensitif

AES-128 merupakan algoritma kriptografi simetris yang telah terbukti andal dan banyak digunakan dalam berbagai sistem keamanan modern. Dengan panjang kunci 128-bit, AES memberikan tingkat keamanan yang tinggi serta performa yang efisien dalam proses enkripsi dan dekripsi data.

Dalam konteks aplikasi website berbasis pengelolaan data penduduk, AES-128 sangat ideal untuk melindungi informasi penting seperti NIK, tanggal lahir, dan alamat lengkap. Data yang dimasukkan oleh pengguna melalui antarmuka aplikasi dapat langsung dienkripsi menggunakan kunci rahasia sebelum disimpan ke dalam basis data. Dengan demikian, meskipun terjadi akses tidak sah terhadap database, informasi yang disimpan tetap tidak dapat dibaca tanpa kunci enkripsi.

 

Caesar Cipher: Sandi Sederhana untuk Masking Data Ringan

Di sisi lain, Caesar Cipher adalah teknik kriptografi klasik yang menggunakan pergeseran huruf berdasarkan jumlah tertentu. Walaupun tidak sekuat AES dan tidak cocok digunakan sebagai mekanisme utama pengamanan data, Caesar Cipher dapat dimanfaatkan untuk masking ringan atau penyamaran informasi di tingkat tampilan atau pengolahan sementara.

Sebagai contoh, Caesar Cipher dapat diterapkan pada nama pengguna atau label tertentu dalam aplikasi, guna menghindari ekspos langsung data saat debugging atau proses sementara lainnya. Hal ini memberikan lapisan obfuscation tambahan yang berguna dalam konteks pengembangan aplikasi yang masih dalam tahap uji coba.

 

Integrasi dalam Aplikasi Website

Implementasi enkripsi dalam aplikasi website memerlukan pendekatan teknis yang terstruktur. Berikut adalah alur integrasi umum yang dapat diterapkan:

Input Data
Pengguna mengisi data pribadi melalui form website.
Proses Enkripsi
Data sensitif seperti NIK dan alamat dienkripsi menggunakan AES-128.
Informasi lain yang tidak terlalu sensitif dapat dimasking menggunakan Caesar Cipher sebagai pelengkap.
Penyimpanan Aman
Data terenkripsi disimpan di dalam database, sehingga tidak terbaca langsung oleh pihak ketiga.
Dekripsi saat Diperlukan
Data akan didekripsi kembali hanya oleh sistem atau petugas yang memiliki otorisasi saat informasi tersebut perlu ditampilkan atau diolah.
Manajemen Kunci
Kunci AES disimpan secara aman, misalnya melalui environment variables, dan tidak dituliskan langsung dalam kode sumber.

 

Manfaat dan Tantangan

Penerapan kombinasi enkripsi ini memberikan sejumlah manfaat, antara lain:

Menjaga kerahasiaan dan integritas data penduduk
Meningkatkan kepercayaan pengguna terhadap sistem layanan digital
Mengurangi risiko kebocoran data akibat serangan siber

Namun, tantangan seperti manajemen kunci enkripsi, performa sistem, dan integrasi dengan arsitektur aplikasi harus diperhatikan secara cermat. Oleh karena itu, pengembangan sistem proteksi data harus disertai dengan pendekatan yang menyeluruh dan didukung oleh praktik keamanan siber yang baik.

 

Keamanan data penduduk merupakan prioritas utama dalam pengembangan sistem digital yang andal dan terpercaya. Dengan mengimplementasikan enkripsi AES-128 untuk proteksi data inti dan Caesar Cipher untuk masking ringan, aplikasi website dapat memberikan perlindungan berlapis terhadap informasi sensitif. Semoga upaya ini menjadi langkah nyata dalam mendukung tata kelola data yang aman, bertanggung jawab, dan berorientasi pada perlindungan hak privasi masyarakat di era digital.

Dilihat: 335
Artikel Selanjutnya...
Perancangan Aplikasi Web untuk Keamanan Data Menggunakan Discrete Wavelet Transform pada Media Audio
Implementasi Honeypot sebagai Sistem Deteksi dan Pencegahan Serangan Jaringan Server
Implementasi Snort dan IPTables untuk Deteksi serta Pencegahan Serangan Jaringan dengan Notifikasi Telegram
Implementasi Suricata sebagai Sistem Deteksi dan Pencegahan Serangan Jaringan Server

Halaman 1 dari 6

1
2
3
4
5
6
FaLang translation system by Faboba
