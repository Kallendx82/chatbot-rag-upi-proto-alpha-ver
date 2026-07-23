# Implementasi Algoritma Obstacle Avoidance Berbasis Potential Field pada AGV

> Source: https://kd-cibiru.upi.edu/index.php/daftar-kategori/prodi-tekkom/artikel-tekkom/implementasi-algoritma-obstacle-avoidance-berbasis-potential-field-pada-agv

Implementasi Algoritma Obstacle Avoidance Berbasis Potential Field pada AGV
13 Januari 2025
Admin TEKKOM
Artikel TEKKOM
Implementasi Algoritma Obstacle Avoidance Berbasis Potential Field pada AGV
Pendahuluan

Automated Guided Vehicle (AGV) merupakan kendaraan otonom yang banyak digunakan dalam industri untuk meningkatkan efisiensi dan akurasi dalam proses transportasi barang. Salah satu tantangan utama dalam pengoperasian AGV adalah bagaimana kendaraan ini dapat bergerak dengan aman di lingkungan yang dinamis serta menghindari hambatan secara efisien. Untuk mengatasi permasalahan tersebut, algoritma obstacle avoidance berbasis Potential Field (PF) menjadi salah satu pendekatan yang efektif dalam navigasi AGV.

Konsep Algoritma Potential Field

Potential Field merupakan metode navigasi yang memanfaatkan konsep medan potensial untuk mengarahkan pergerakan AGV. Prinsip utama dari algoritma ini adalah dengan menganggap tujuan sebagai sumber gaya tarik (attractive force) dan hambatan sebagai sumber gaya tolak (repulsive force). Dengan kombinasi kedua gaya ini, AGV dapat menentukan lintasan yang optimal untuk mencapai tujuan tanpa menabrak hambatan.

Komponen utama dalam algoritma Potential Field meliputi:

Gaya Tarik (Attractive Force): Menarik AGV menuju target dengan kecepatan dan arah yang sesuai.

Gaya Tolak (Repulsive Force): Menghindari rintangan dengan mengubah lintasan agar tidak terjadi tabrakan.

Resultan Gaya: Perpaduan antara gaya tarik dan tolak yang menentukan arah gerak AGV secara dinamis.

Implementasi Algoritma Potential Field pada AGV

Dalam penerapannya, algoritma Potential Field memerlukan beberapa tahapan utama, yaitu:

Pendeteksian Lingkungan: AGV dilengkapi dengan sensor seperti LiDAR, kamera, atau sensor ultrasonik untuk memetakan lingkungan dan mendeteksi hambatan.

Perhitungan Medan Potensial: Sistem menghitung vektor gaya tarik menuju tujuan serta vektor gaya tolak dari hambatan yang terdeteksi.

Penentuan Lintasan Optimal: AGV menentukan jalur pergerakan berdasarkan resultan gaya potensial sehingga dapat bergerak menuju tujuan tanpa menabrak rintangan.

Penyempurnaan Navigasi: Algoritma dikombinasikan dengan metode lain, seperti fuzzy logic atau machine learning, untuk meningkatkan adaptasi terhadap lingkungan yang lebih kompleks.

Keunggulan Algoritma Potential Field dalam Navigasi AGV

Beberapa keunggulan dari penggunaan algoritma Potential Field pada AGV adalah:

Navigasi yang Halus dan Adaptif: AGV dapat bergerak secara dinamis dengan menghindari hambatan tanpa gerakan yang tiba-tiba.

Efisiensi Perhitungan: Algoritma ini relatif sederhana dan membutuhkan sumber daya komputasi yang lebih rendah dibandingkan metode lain seperti algoritma path planning berbasis graph.

Kemudahan Implementasi: Dapat diterapkan dalam berbagai jenis AGV dengan penyesuaian parameter yang fleksibel.

Kesimpulan

Algoritma obstacle avoidance berbasis Potential Field merupakan solusi yang efektif untuk meningkatkan navigasi AGV dalam lingkungan yang dinamis. Dengan memanfaatkan gaya tarik dan gaya tolak, AGV dapat bergerak secara aman dan efisien tanpa menabrak hambatan. Ke depan, integrasi algoritma ini dengan teknologi kecerdasan buatan dan sensor yang lebih canggih dapat semakin meningkatkan kinerja dan keandalan AGV dalam berbagai aplikasi industri.

 

TEKNIK KOMPUTER

Dilihat: 232
Previous article: Rancang Bangun Aplikasi Simulasi Micro-Teaching Berbasis Virtual Reality dengan Integrasi Internet of Things Sebelum
Next article: Pengambilan Kendali PID untuk Optimalisasi Navigasi AGV Berikut
FaLang translation system by Faboba
