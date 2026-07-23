# Desain dan Implementasi Autonomous Semantic Hazard Mapping System pada Mobile Robot

> Source: https://kd-cibiru.upi.edu/index.php/daftar-kategori/prodi-tekkom/berita-tekom/desain-dan-implementasi-autonomous-semantic-hazard-mapping-system-pada-mobile-robot

Desain dan Implementasi Autonomous Semantic Hazard Mapping System pada Mobile Robot
25 September 2025
Admin TEKKOM
Berita TEKKOM
Desain dan Implementasi Autonomous Semantic Hazard Mapping System pada Mobile Robot

Perkembangan teknologi robotika dan kecerdasan buatan telah mendorong inovasi dalam sistem navigasi otonom yang lebih adaptif dan kontekstual. Salah satu aspek penting dalam navigasi tersebut adalah kemampuan untuk mengenali dan memetakan area berbahaya di lingkungan sekitar. Penelitian ini bertujuan untuk merancang dan mengimplementasikan Autonomous Semantic Hazard Mapping System pada mobile robot yang mampu mendeteksi, mengklasifikasikan, dan memetakan bahaya secara semantik secara real-time. Sistem ini menggabungkan teknologi computer vision, sensor fusion, dan semantic mapping berbasis deep learning untuk menghasilkan peta lingkungan yang lebih informatif dan aman bagi pergerakan robot.

1. Pendahuluan

Robot mobile otonom menjadi komponen penting dalam berbagai bidang seperti industri, pertanian, dan transportasi. Namun, tantangan utama dalam pengoperasiannya adalah kemampuan robot untuk memahami konteks lingkungan serta mengenali potensi bahaya di sekitarnya. Sistem navigasi konvensional umumnya hanya memanfaatkan obstacle avoidance sederhana tanpa memahami makna semantik dari area yang dilalui.

Autonomous Semantic Hazard Mapping System hadir sebagai solusi untuk meningkatkan persepsi robot terhadap lingkungan. Dengan mengintegrasikan teknologi pemetaan semantik, robot tidak hanya mengetahui posisi rintangan tetapi juga memahami jenis bahaya, seperti permukaan licin, genangan air, objek bergerak, atau area dengan risiko tinggi. Tujuan utama penelitian ini adalah mengembangkan sistem yang mampu melakukan deteksi bahaya secara otomatis dan memetakan hasilnya dalam bentuk semantic map untuk mendukung navigasi aman dan efisien.

2. Metodologi Penelitian
2.1 Arsitektur Sistem

Desain sistem terdiri dari empat komponen utama:

Sensor Perseptual
Mobile robot dilengkapi dengan kamera RGB-D, sensor LIDAR, dan sensor ultrasonik untuk menangkap data lingkungan dalam bentuk visual dan jarak.

Modul Deteksi Bahaya
Data sensor diproses menggunakan model deep learning berbasis YOLOv8 untuk mendeteksi objek dan area yang berpotensi berbahaya. Kemudian hasil deteksi diklasifikasikan ke dalam label semantik seperti “licin”, “berdebu”, “berair”, atau “rintangan keras”.

Pemetaan Semantik (Semantic Mapping)
Hasil klasifikasi bahaya diproyeksikan ke dalam peta 2D menggunakan algoritma Simultaneous Localization and Mapping (SLAM). Tiap area dalam peta diberi warna atau label sesuai tingkat risiko.

Navigasi Otonom
Modul perencanaan jalur (path planning) menggunakan algoritma A* untuk merancang lintasan aman yang menghindari area berbahaya, sedangkan kontrol gerak robot diatur dengan metode PID.

2.2 Implementasi Perangkat Keras

Sistem diimplementasikan pada platform mobile robot berbasis Raspberry Pi 4 dan Jetson Nano sebagai unit pemrosesan utama. Motor DC dengan encoder digunakan untuk sistem gerak, sementara komunikasi data antar modul dilakukan melalui protokol ROS (Robot Operating System).

2.3 Implementasi Perangkat Lunak

Pemrograman dilakukan dengan Python dan framework PyTorch untuk deep learning. Proses integrasi data sensor, pemetaan, dan navigasi dikendalikan menggunakan ROS Noetic. Antarmuka visual dikembangkan dengan RViz untuk menampilkan semantic hazard map secara real-time.

3. Hasil dan Pembahasan
3.1 Hasil Pengujian Sistem

Pengujian dilakukan di lingkungan indoor dengan berbagai kondisi bahaya buatan seperti genangan air, permukaan miring, dan rintangan dinamis. Hasil uji menunjukkan:

Akurasi deteksi bahaya: 94,2%

Latensi pemrosesan rata-rata: 0,28 detik per frame

Keberhasilan robot menghindari area bahaya: 96%

Kemampuan peta memperbarui kondisi lingkungan secara real-time dengan jeda kurang dari 1 detik.

3.2 Analisis Kinerja

Sistem berhasil menghasilkan semantic hazard map yang memuat informasi spasial dan semantik secara bersamaan. Integrasi data multi-sensor meningkatkan akurasi deteksi bahaya, sementara algoritma A* memungkinkan navigasi yang lebih adaptif terhadap perubahan kondisi lingkungan.

Kendati demikian, sistem masih menghadapi keterbatasan dalam mendeteksi bahaya di area dengan pencahayaan rendah atau pantulan tinggi. Penambahan sensor inframerah atau thermal camera dapat menjadi solusi pada penelitian selanjutnya.

Penelitian ini berhasil merancang dan mengimplementasikan Autonomous Semantic Hazard Mapping System pada mobile robot yang mampu mendeteksi dan memetakan bahaya secara otomatis dan semantik. Sistem ini dapat meningkatkan kemampuan persepsi robot terhadap lingkungan serta memperkuat aspek keselamatan dan efisiensi dalam navigasi otonom.

Ke depan, pengembangan sistem dapat diarahkan pada peningkatan akurasi deteksi berbasis multi-modal learning serta integrasi jaringan komunikasi berbasis IoT untuk kolaborasi antar robot dalam pemetaan lingkungan yang lebih luas.

Dilihat: 164
Previous article: Implementasi Algoritma Multilayer Perceptron dan K-Means untuk Feedback Naratif Instan pada Sistem Pembelajaran Program Sebelum
Next article: Perancangan Sarung Tangan Pintar untuk Monitoring Kelelahan Pengendara Motor Berikut
FaLang translation system by Faboba
