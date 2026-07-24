# BAB IV — Deskripsi Fitur Aplikasi Chatbot RAG UPI

> Tempel tiap bagian di bawah sebagai sub-bab BAB IV (mis. 4.x.1, 4.x.2,
> dst.) sesuai struktur penomoran skripsi Anda. Setiap fitur ditulis dalam
> 4 paragraf, masing-masing 4–5 kalimat, disusun berdasarkan pembacaan
> langsung kode sumber aplikasi (`frontend/`) — bukan deskripsi generik.
> Sisipkan tangkapan layar antarmuka sungguhan (bukan mockup Figma) pada
> tiap sub-bab sebagai bukti implementasi.

## 4.x.1 Fitur Percakapan dan Retrieval-Augmented Generation (RAG)

![Layar chat dengan jawaban RAG dan badge terverifikasi sumber](screenshots/4x1_chat_jawaban_sitasi.png)
*Gambar 4.1 — Percakapan dengan jawaban yang dihasilkan sistem RAG beserta badge "Terverifikasi sumber".*

Fitur inti aplikasi adalah antarmuka percakapan yang memungkinkan pengguna
mengajukan pertanyaan seputar informasi akademik UPI dan menerima jawaban
yang dihasilkan berdasarkan dokumen resmi yang telah diindeks ke dalam
basis pengetahuan sistem. Antarmuka ini diimplementasikan pada komponen
`ChatPanel`, yang menampilkan layar sambutan (*welcome screen*) ketika
belum ada pesan pada percakapan aktif, dan beralih ke tampilan daftar pesan
yang dapat digulir (*scrollable*) begitu percakapan dimulai, dengan
penggulungan otomatis ke pesan terbaru setiap kali konten bertambah.
Kolom input pesan (`ChatInput`) berupa area teks yang tumbuh secara
otomatis mengikuti panjang isi (maksimum 200 piksel), mendukung pengiriman
pesan dengan tombol Enter dan baris baru dengan Shift+Enter, serta secara
otomatis menyimpan draf ketikan pengguna ke penyimpanan lokal peramban
(*localStorage*) agar tidak hilang bila halaman dimuat ulang secara tidak
sengaja. Sistem juga menampilkan spanduk peringatan berwarna merah bila
backend tidak dapat dihubungi sama sekali, atau spanduk berwarna kuning
kecokelatan bila backend aktif namun jalur pemrosesan RAG belum siap
karena indeks vektor belum dimuat sepenuhnya, sehingga pengguna mendapat
informasi status sistem secara langsung tanpa harus menebak penyebab
kegagalan.

Proses di balik satu putaran tanya-jawab melibatkan beberapa tahap yang
diorkestrasi oleh *hook* `useChat`. Begitu pengguna mengirim pertanyaan,
sistem terlebih dahulu menambahkan pesan pengguna dan sebuah pesan asisten
sementara berstatus "sedang memproses" ke tampilan, lalu secara paralel
menjalankan panggilan pendahuluan (*preflight*) ke titik akhir pengambilan
dokumen (`/api/retrieve`) semata-mata untuk memperoleh daftar sumber lebih
awal dan mendorong perubahan label status yang ditampilkan kepada
pengguna. Setelah itu, sistem menunggu respons lengkap dari titik akhir
utama percakapan (`/api/chat`), yang mengembalikan jawaban akhir beserta
daftar sumber kutipan dan metrik performa (waktu pengambilan, waktu
pembuatan jawaban, dan waktu total). Karena backend saat ini belum
menyediakan mekanisme *streaming* token sungguhan (*Server-Sent Events*),
teks jawaban yang sudah lengkap ini kemudian dianimasikan kata demi kata
ke layar dengan jeda sekitar 14 milidetik per kata (dipercepat menjadi tiga
kata per langkah untuk jawaban yang sangat panjang), sehingga secara visual
tampak seperti proses pembuatan jawaban yang berlangsung, meski
sesungguhnya jawaban sudah diterima secara utuh dari server.

Sistem dirancang tahan terhadap gangguan sementara: kegagalan jaringan
dengan kode status yang bersifat sementara (404, 408, 500, 502, 503, 504)
akan dicoba ulang secara otomatis hingga tiga kali dengan jeda yang
membesar seiring percobaan (1.200 milidetik dikali nomor percobaan),
sehingga pesan kegagalan hanya ditampilkan kepada pengguna setelah seluruh
percobaan ulang habis, bukan pada kegagalan pertama. Pengguna dapat
menghentikan proses pembuatan jawaban yang sedang berjalan melalui tombol
"Stop" yang menggantikan tombol kirim selama proses berlangsung,
menggunakan mekanisme `AbortController` bawaan peramban; pesan yang
dihentikan tetap disimpan dengan penanda khusus, bukan dihapus, sehingga
pengguna masih dapat mencoba ulang, menyunting pertanyaan, atau menyalin isi
pesan tersebut kapan saja. Fitur regenerasi jawaban (*retry*) menggunakan
kembali pertanyaan pengguna yang sama tanpa menggandakannya pada riwayat
percakapan, sedangkan fitur sunting-dan-kirim-ulang (*edit and retry*)
memungkinkan pengguna mengubah teks pertanyaan yang sudah terkirim secara
langsung di dalam gelembung pesan tersebut sebelum meminta jawaban baru.
Terdapat pula fungsi hapus pesan beserta seluruh pesan sesudahnya
(*delete and following*), yang meminta konfirmasi pengguna terlebih dahulu
sebelum benar-benar menghapus riwayat percakapan dari titik tersebut.

Setiap gelembung pesan (`MessageBubble`) dibedakan secara visual antara
pesan pengguna (rata kanan, warna latar primer) dan pesan asisten (rata
kiri, gaya kotak bertepi dengan logo aplikasi sebagai avatar). Selama
jawaban belum tersedia, sistem menampilkan indikator "sedang mengetik"
berupa tiga titik berdenyut disertai penghitung waktu berjalan yang
diperbarui setiap 200 milidetik dan label status yang berubah seiring
waktu — mulai dari "Sedang mencari dokumen yang relevan..." hingga "Masih
memproses, mohon tunggu..." bila proses melewati satu menit — memberi
pengguna gambaran tahap pemrosesan tanpa perlu memahami detail teknis di
baliknya. Jawaban yang telah selesai disertai lencana verifikasi sumber
("Terverifikasi sumber" bila jawaban didasarkan pada dokumen yang
ditemukan, atau "Tanpa sumber" bila tidak), dan bila mode debug aktif, juga
menampilkan lencana latensi dalam milidetik serta nama backend/model yang
menghasilkan jawaban tersebut. Ikon aksi pada setiap jawaban memungkinkan
pengguna menyalin teks jawaban ke papan klip (dengan tanda centang
konfirmasi selama 1,5 detik) dan meminta jawaban dibuat ulang, sementara
layar sambutan sengaja dibiarkan bersih tanpa rekomendasi pertanyaan
otomatis agar tampilan awal aplikasi tetap sederhana dan tidak
mengarahkan pengguna secara berlebihan.

## 4.x.2 Fitur Sitasi Sumber (Source Citations)

![Panel inspeksi sumber dengan metadata lengkap potongan dokumen](screenshots/4x2_source_inspector.png)
*Gambar 4.2 — Panel `SourceInspector` menampilkan skor kemiripan, chunk ID, document ID, dan tombol "Buka PDF".*

Untuk mendukung transparansi dan akuntabilitas jawaban yang dihasilkan
sistem RAG, setiap jawaban asisten yang berhasil menemukan dokumen relevan
disertai daftar kartu sumber (`SourceCard`) yang ditampilkan sebagai grid
di bawah teks jawaban, dengan label "Sumber (N)" yang mencantumkan jumlah
dokumen yang digunakan. Setiap kartu muncul dengan animasi tampil bertahap
(*staggered fade-in*) yang memberi jeda singkat antar kartu berdasarkan
urutan peringkatnya, sehingga pengalaman visual terasa lebih halus
dibandingkan seluruh kartu muncul serentak. Kartu menampilkan ikon yang
menyesuaikan jenis sumber (ikon dunia untuk sumber web/HTML, ikon berkas
untuk dokumen), judul dokumen, lencana persentase skor kemiripan, lencana
kategori, nomor halaman, dan cuplikan dua baris dari isi potongan dokumen
tersebut. Rancangan ini memungkinkan pengguna menilai sekilas relevansi
sumber tanpa harus membuka setiap dokumen secara penuh.

Mengeklik salah satu kartu sumber membuka panel inspeksi sumber
(`SourceInspector`), sebuah laci geser (*slide-over drawer*) dari sisi
kanan layar dengan animasi pegas (*spring animation*) yang menampilkan
metadata lengkap potongan dokumen tersebut: skor kemiripan dalam bentuk
persentase sekaligus nilai desimal mentah hingga empat angka di belakang
koma, peringkat kemunculan dalam hasil pengambilan, kategori dokumen,
nomor halaman, identifikasi potongan (*chunk ID*) dan identifikasi dokumen
(*document ID*) dalam format monospace, bagian/seksi dokumen, jenis sumber,
serta lokasi berkas sumber mentah. Tingkat detail ini jauh melampaui
tampilan ringkas pada kartu sumber, dan ditujukan untuk memverifikasi
keakuratan sistem pengambilan dokumen secara menyeluruh, termasuk untuk
kebutuhan audit dan debugging pada tahap pengembangan maupun evaluasi.
Seluruh metadata tersebut disusun dalam format kisi (*grid*) yang rapi
sehingga mudah dipindai secara visual, bukan sebagai teks naratif panjang
yang lebih sulit dibaca sekilas oleh pengguna.
Panel ini menampilkan pula teks lengkap potongan dokumen yang diambil pada
bagian bawah dengan label "Konteks yang diambil", memungkinkan pembaca
memverifikasi langsung apakah jawaban chatbot benar-benar konsisten dengan
isi dokumen sumber.

Khusus untuk sumber yang berasal dari berkas PDF, panel inspeksi
menampilkan tombol "Buka PDF" yang membuka penampil PDF internal aplikasi
pada tab baru melalui rute `/viewer`, dengan parameter dokumen, nomor
halaman, dan judul yang diteruskan langsung ke penampil tersebut. Pendekatan
ini sengaja dipilih menggantikan penampil PDF bawaan peramban karena
perilaku tautan jangkar halaman (`#page=N`) pada penampil PDF bawaan
peramban terbukti tidak konsisten antar perangkat dan ekstensi peramban
yang berbeda-beda, sehingga pengguna sering diarahkan ke halaman pertama
alih-alih halaman kutipan yang sebenarnya. Dengan penampil internal berbasis
pdf.js, aplikasi memiliki kendali penuh atas navigasi halaman yang akurat,
memastikan pengguna langsung diarahkan ke halaman yang menjadi sumber
kutipan jawaban. Untuk sumber berupa halaman web, tombol serupa berupa
tautan URL eksternal yang dapat diklik langsung menuju sumber aslinya.

Fitur sitasi sumber secara langsung mendukung salah satu tujuan utama
sistem RAG, yaitu mengurangi risiko halusinasi (*hallucination*) dengan
memberi pengguna kemampuan memverifikasi klaim jawaban terhadap dokumen
asli, bukan sekadar memercayai keluaran model bahasa secara membabi buta.
Kombinasi lencana skor kemiripan pada tingkat kartu maupun panel inspeksi
memungkinkan pengguna maupun peneliti menilai seberapa relevan konteks yang
diambil sebelum menilai kualitas jawaban itu sendiri — sebuah pemisahan
yang sejalan dengan metodologi evaluasi *Context Precision* dan *Context
Recall* yang dijelaskan pada bagian evaluasi model (lihat dokumentasi
`docs/evaluation/`). Rancangan antarmuka ini merupakan realisasi langsung
dari panel "Retrieved Context" yang sudah direncanakan sejak tahap
prototipe Figma pada BAB III, dengan tingkat detail metadata yang jauh
lebih kaya pada implementasi akhir. Secara keseluruhan, fitur ini
menjembatani kesenjangan kepercayaan yang umum terjadi pada sistem berbasis
model bahasa generatif, dengan menjadikan proses pengambilan dokumen
sebagai bagian yang transparan dan dapat diperiksa oleh pengguna akhir.

## 4.x.3 Fitur Pengaturan Aplikasi (Settings)

![Panel Pengaturan pada tampilan desktop](screenshots/4x3_settings_desktop.png)
*Gambar 4.3 — Panel `SettingsModal`: tema, bahasa, Top-K, Temperature, pemilihan model, dan mode debug.*

Aplikasi menyediakan panel pengaturan (`SettingsModal`) yang memungkinkan
pengguna menyesuaikan berbagai parameter operasional sistem tanpa perlu
mengubah kode maupun berkas konfigurasi. Panel ini menggunakan pola
penyuntingan berbasis draf (*draft-based editing*): perubahan yang dibuat
pengguna disimpan sementara ke salinan lokal sebelum benar-benar diterapkan
ke penyimpanan pengaturan utama, dan sistem melacak apakah draf tersebut
berbeda dari nilai yang tersimpan (status "kotor"/*dirty*). Bila pengguna
mencoba menutup panel — baik melalui tombol Escape, mengeklik di luar
panel, atau tombol silang — sementara terdapat perubahan yang belum
disimpan, sistem menampilkan dialog konfirmasi "Pergi tanpa menyimpan?"
alih-alih membuang perubahan tersebut secara diam-diam. Tombol "Atur ulang"
pada bagian bawah panel mengembalikan seluruh draf ke nilai bawaan sistem,
sedangkan tombol "Simpan" hanya aktif ketika terdapat perubahan yang belum
diterapkan.

Bagian tampilan (*appearance*) menyediakan tiga pilihan tema — Terang,
Gelap, dan Sistem (mengikuti preferensi sistem operasi perangkat) — masing-
masing dengan ikon matahari, bulan, dan monitor, dengan opsi yang sedang
aktif ditandai bingkai dan latar berwarna primer. Bagian bahasa dipisah
menjadi dua pengaturan independen: bahasa antarmuka (*interface language*)
yang mengubah seluruh label, tombol, dan teks statis aplikasi antara Bahasa
Indonesia dan Bahasa Inggris — perubahan ini memicu pemuatan ulang
halaman penuh karena bahasa antarmuka diterapkan di luar cakupan
penyimpanan pengaturan biasa — dan bahasa jawaban (*answer language*) yang
secara khusus mengatur bahasa yang diminta dari model bahasa saat
menghasilkan jawaban, diteruskan langsung ke titik akhir `/api/chat` dan
`/api/retrieve/debug`. Pemisahan dua pengaturan bahasa ini memungkinkan,
misalnya, pengguna berbahasa Inggris tetap dapat meminta jawaban dalam
Bahasa Indonesia, atau sebaliknya, sesuai kebutuhan penggunaan. Pemisahan
ini juga relevan bagi kebutuhan evaluasi, karena parameter bahasa jawaban
yang sama persis dipakai skrip perbandingan model pada `docs/evaluation/`
saat memanggil titik akhir `/api/chat`.

Dua kontrol geser (*slider*) mengatur parameter teknis pengambilan dan
pembuatan jawaban: Top-K retrieval (rentang 1 hingga 20, bilangan bulat)
menentukan berapa banyak potongan dokumen yang diambil sebagai konteks
untuk setiap pertanyaan, dengan pembacaan nilai langsung dan teks bantuan
yang menjelaskan fungsinya; serta Temperature (rentang 0 hingga 1, dengan
langkah 0,05) yang mengatur tingkat variasi/kreativitas keluaran model
bahasa, disertai anjuran agar nilainya dijaga rendah (di bawah 0,2) untuk
menjaga konsistensi jawaban berbasis fakta. Pemilihan model backend
disediakan melalui menu tarik-turun dengan daftar model konkret yang
tersedia melalui Ollama — di antaranya `llama3.1:8b-instruct-q4_K_M`
(ditandai sebagai bawaan/*default* karena akurasinya), varian Llama dan
Qwen lain yang lebih ringan, `gemma4:e2b`, serta mode "Extractive (tanpa
LLM)" yang hanya mengembalikan potongan dokumen yang paling relevan tanpa
melalui proses pembuatan jawaban generatif sama sekali — memberi pengguna
kendali langsung atas keseimbangan antara kecepatan, kebutuhan sumber daya
komputasi, dan kualitas jawaban. Nilai `top_k` yang sama inilah yang, pada
tahap evaluasi, dijaga konsisten di sisi backend agar model penilai selalu
menilai konteks yang persis sama dengan yang dilihat model generasi (lihat
`docs/evaluation/THESIS_NOTES.md` §1.1). Ketersediaan opsi "Extractive"
sebagai mode tanpa model generatif sama sekali juga berguna sebagai
pembanding dasar (*baseline*) saat menilai seberapa besar kontribusi model
bahasa generatif terhadap kualitas jawaban dibandingkan sekadar menampilkan
potongan dokumen mentah.

Sakelar "Mode Debug" pada bagian bawah panel mengaktifkan tampilan
informasi teknis tambahan pada setiap jawaban — lencana latensi dalam
milidetik dan nama backend yang digunakan — yang secara bawaan
disembunyikan agar antarmuka tetap sederhana bagi pengguna umum. Sakelar
ini juga menjadi salah satu syarat gerbang (bersama status admin) yang
menentukan apakah panel debug retrieval (dibahas pada sub-bab berikutnya)
dapat diakses sama sekali, menjadikannya kontrol terpusat bagi fitur-fitur
yang ditujukan untuk keperluan pengembangan dan evaluasi, bukan penggunaan
sehari-hari. Kombinasi seluruh kontrol pengaturan ini mencerminkan
kebutuhan aplikasi untuk melayani dua kelompok pengguna sekaligus:
mahasiswa/pengguna umum yang membutuhkan antarmuka sederhana, dan
administrator/peneliti yang membutuhkan kendali granular atas parameter
sistem RAG untuk kepentingan pengujian dan evaluasi. Desain berlapis ini —
kontrol dasar yang selalu terlihat, kontrol lanjutan yang tersembunyi di
balik sakelar debug — menjadi pola yang konsisten diterapkan di seluruh
aplikasi, termasuk pada fitur tambah dokumen yang dibahas berikutnya.

## 4.x.4 Fitur Panel Debug Retrieval (Debug Panel)

![Panel Retrieval Debug dengan metrik latensi dan pratinjau prompt](screenshots/4x4_debug_panel.png)
*Gambar 4.4 — Panel `DebugPanel`: metrik latensi, parameter retrieval, pratinjau prompt, dan daftar chunk.*

Panel debug (`DebugPanel`) merupakan fitur yang secara eksplisit
diperuntukkan sebagai sarana pembuktian (*explainability surface*) bagi
klaim pengurangan halusinasi yang menjadi tujuan utama sistem RAG dalam
penelitian ini, dan hanya dapat diakses oleh pengguna dengan status
administrator. Panel ini muncul sebagai laci geser dari sisi kanan layar
dengan aksen warna kehijauan (*teal*) dan ikon serangga (*bug*) pada
kepala panelnya, memisahkan secara visual fungsinya dari fitur-fitur
biasa yang ditujukan untuk pengguna umum. Panel menyediakan kolom masukan
pertanyaan tersendiri beserta tombol "Jalankan", yang memungkinkan
administrator menguji proses pengambilan dokumen (*retrieval*) secara
terisolasi tanpa harus melalui alur percakapan penuh dan tanpa memicu
proses pembuatan jawaban oleh model bahasa. Pemisahan ini penting agar
pengujian retrieval dapat dilakukan berulang kali dengan cepat tanpa
menunggu waktu pemrosesan model generatif yang jauh lebih lambat.

Ketika sebuah kueri dijalankan, panel memanggil titik akhir debug khusus
(`GET /api/retrieve/debug`) yang mengembalikan informasi jauh lebih rinci
dibandingkan titik akhir pengambilan dokumen biasa. Empat kartu metrik
ditampilkan sekaligus: latensi tahap penyematan kueri (*embedding
latency*), latensi tahap pencarian pada indeks vektor (*search latency*),
latensi total keseluruhan proses, dan ukuran indeks (jumlah dokumen
terindeks) — memberi administrator gambaran langsung mengenai di mana
waktu pemrosesan paling banyak terpakai. Lencana tambahan menampilkan nama
model penyematan (*embedding model*) yang digunakan, nilai parameter
Top-K dan ambang skor (*score threshold*) yang berlaku pada pengujian
tersebut, serta indikator apakah awalan kueri/dokumen khas model E5
(*E5 query/passage prefixes*) sedang diaktifkan — sebuah detail teknis
yang berpengaruh signifikan terhadap kualitas pengambilan pada model
penyematan multibahasa yang digunakan sistem. Seluruh informasi ini
ditampilkan bersamaan pada satu layar tanpa perlu berpindah tab atau
membuka konsol pengembang peramban, sehingga administrator dapat langsung
membandingkan efek perubahan parameter terhadap perilaku pengambilan
dokumen.

Sebuah bagian yang dapat diciutkan (*collapsible*) berjudul "Pratinjau
prompt (grounded)" menampilkan teks *prompt* mentah dalam format monospace
persis seperti yang akan dikirimkan ke model bahasa apabila proses
berlanjut ke tahap pembuatan jawaban — mencakup instruksi sistem,
seluruh konteks dokumen yang disisipkan, dan pertanyaan pengguna dalam
susunan akhirnya. Fitur pratinjau ini memungkinkan administrator memeriksa
secara langsung apakah *prompt* yang dibangun sistem sudah benar secara
struktural sebelum dikirim ke model, sebuah kemampuan yang sangat berguna
saat men-debug kasus jawaban yang tidak sesuai harapan. Di bawahnya,
daftar seluruh potongan dokumen yang berhasil diambil ditampilkan lengkap
dengan peringkat, judul, lencana skor kemiripan, kategori, nomor halaman,
identitas potongan (*chunk_id*), dan teks lengkap potongan tersebut —
tanpa pemotongan cuplikan seperti pada kartu sumber di antarmuka
percakapan biasa. Tampilan tanpa pemotongan ini penting khususnya saat
menelusuri kasus di mana jawaban model tampak tidak akurat, karena
administrator dapat langsung memeriksa apakah kesalahan berasal dari
tahap pengambilan dokumen atau dari tahap pembuatan jawaban itu sendiri.

Panel ini secara fungsional menjadi versi diagnostik dari fitur sitasi
sumber yang dibahas pada sub-bab sebelumnya, namun dengan tingkat
transparansi maksimal yang sengaja tidak diekspos kepada pengguna umum
untuk menjaga kesederhanaan antarmuka. Keberadaan fitur ini secara langsung
mendukung metodologi evaluasi yang dijelaskan pada `docs/evaluation/`,
di mana metrik seperti *Context Precision* memerlukan pemeriksaan manual
terhadap potongan dokumen yang diambil sistem. Dengan menyediakan akses
langsung ke *prompt* mentah dan metadata pengambilan dokumen tanpa perlu
membuka log server atau basis data secara manual, panel ini mempercepat
proses debugging dan analisis kegagalan selama tahap pengembangan dan
pengujian sistem secara signifikan. Fitur ini melengkapi rangkaian alat
bantu pengembangan yang terintegrasi langsung ke dalam antarmuka produksi
aplikasi, alih-alih memerlukan perangkat terpisah di luar aplikasi.

## 4.x.5 Fitur Tambah Dokumen PDF (Admin Ingest)

![Halaman admin Tambah Dokumen PDF dengan Pengaturan Chunk terbuka](screenshots/4x5_admin_tambah_dokumen.png)
*Gambar 4.5 — Halaman `/admin`: formulir unggah PDF, kategori, dan Pengaturan Chunk (Lanjutan).*

Fitur tambah dokumen memungkinkan administrator memperluas basis
pengetahuan sistem RAG dengan mengunggah berkas PDF baru langsung melalui
antarmuka web, tanpa perlu mengakses server atau menjalankan skrip baris
perintah secara manual. Halaman ini beralamat di rute `/admin` dan hanya
dapat diakses oleh pengguna yang statusnya ditandai sebagai administrator;
pengguna lain yang mencoba mengaksesnya akan melihat pesan "Halaman ini
hanya untuk admin" alih-alih formulir unggah. Formulir utama terdiri atas
kolom pemilihan berkas PDF yang menampilkan nama dan ukuran berkas (dalam
megabita) setelah dipilih, kolom judul dokumen opsional yang secara bawaan
menggunakan nama berkas apabila dikosongkan, dan kolom kategori wajib
berupa menu tarik-turun berisi sepuluh kategori bawaan yang mencerminkan
struktur organisasi UPI — di antaranya PPID UPI, PMB UPI, LPPM UPI,
Direktorat Pendidikan, serta lima kampus daerah (Cibiru, Sumedang,
Tasikmalaya, Purwakarta, Serang) — ditambah opsi "Kategori lainnya…" yang
memunculkan kolom teks bebas apabila kategori yang dibutuhkan tidak
tercantum dalam daftar bawaan. Daftar kategori bawaan ini sengaja disusun
mengikuti struktur organisasi UPI yang sesungguhnya, sehingga dokumen yang
diunggah dapat langsung dikelompokkan secara konsisten dengan sumber
resminya sejak awal, tanpa memerlukan proses pengategorian ulang di
kemudian hari.

Bagian "Pengaturan Chunk (Lanjutan)" yang dapat diciutkan menyediakan dua
parameter teknis pemrosesan dokumen bagi administrator yang memahami
dampaknya: ukuran potongan teks (*chunk size*, rentang 100–2.000 karakter)
dan jumlah kalimat tumpang tindih antar potongan (*overlap*, rentang 0–5
kalimat). Kedua nilai divalidasi di sisi klien sebelum pengiriman —
sistem menampilkan pesan kesalahan spesifik seperti "Ukuran chunk harus
antara 100–2.000 karakter" apabila nilai di luar rentang yang diizinkan
dimasukkan, mencegah permintaan tidak valid terkirim ke server. Apabila
kedua kolom dibiarkan kosong, sistem menggunakan nilai bawaan otomatis
yang disesuaikan berdasarkan karakteristik dokumen. Bagian kedua yang juga
dapat diciutkan, "Panduan Upload PDF", menyediakan teks bantuan statis
berisi jenis dokumen yang didukung (teks polos, tabel, dan dokumen hasil
pemindaian/OCR melalui Tesseract), anjuran pengaturan ukuran potongan
tergantung karakter dokumen (naratif versus padat tabel), serta peringatan
bahwa mengunggah ulang berkas dengan lokasi/path yang sama akan
menggantikan potongan lama yang sudah terindeks sebelumnya.

Ketika tombol "Unggah & Proses" ditekan, sistem membangun data multipart
(`FormData`) berisi berkas, kategori, judul, serta parameter *chunk* jika
diisi, lalu mengirimkannya melalui permintaan HTTP langsung (bukan melalui
pembungkus JSON generik yang dipakai fitur lain) ke titik akhir `POST
/api/ingest` disertai token otorisasi administrator. Selama proses
berlangsung, tombol menampilkan ikon pemuatan berputar beserta teks
"Memproses…" dan dinonaktifkan sementara untuk mencegah pengiriman ganda
yang tidak disengaja. Keberhasilan proses ditandai kotak notifikasi
berwarna hijau dengan ikon centang yang menampilkan pesan dari server
beserta jumlah potongan yang berhasil ditambahkan ke indeks, sedangkan
kegagalan ditandai kotak merah dengan ikon peringatan berisi pesan
kesalahan yang diterima dari server. Formulir otomatis dikosongkan setelah
proses berhasil, memungkinkan administrator langsung mengunggah dokumen
berikutnya tanpa perlu menyegarkan halaman.

Halaman ini dibungkus dengan elemen visual latar belakang yang berputar
menampilkan enam foto kampus UPI (Isola, Cibiru, Sumedang, Purwakarta,
Tasikmalaya, dan Serang) secara bergantian setiap sembilan menit selama
halaman dibuka, dengan efek transisi memudar (*cross-fade*) selama 1,5
detik antar foto menggunakan dua lapisan elemen yang tumpang tindih.
Sebuah lapisan tekstur derau (*noise texture*) dihasilkan langsung melalui
filter SVG bawaan (`feTurbulence`) tanpa memerlukan berkas gambar
eksternal, diterapkan dengan mode campuran (*mixBlendMode*) "multiply"
dan opasitas rendah (0,08) di atas foto latar, ditambah lapisan
semi-transparan tambahan agar teks formulir tetap mudah dibaca pada kedua
mode tema terang maupun gelap. Elemen dekoratif ini murni bertujuan
estetika dan tidak memengaruhi fungsi unggah dokumen, namun mencerminkan
perhatian terhadap detail visual bahkan pada halaman yang ditujukan khusus
untuk administrator, bukan pengguna umum aplikasi. Karena tekstur derau
dihasilkan langsung melalui filter SVG, bukan berkas gambar tersimpan,
elemen ini tidak menambah beban unduhan (*payload*) halaman sama sekali,
sekaligus menghindari kendala hak cipta atas gambar tekstur pihak ketiga.

## 4.x.6 Fitur Statistik Penggunaan (Usage Statistics)

![Halaman Statistik: kartu ringkasan dan grafik pertanyaan per hari](screenshots/4x6_statistik_ringkasan.png)
*Gambar 4.6a — Halaman `/stats`: kartu Total Pertanyaan/Akun Terdaftar/Sesi Tersimpan dan grafik harian.*

![Halaman Statistik: daftar pertanyaan terpopuler](screenshots/4x6_statistik_terpopuler.png)
*Gambar 4.6b — Daftar "Pertanyaan terpopuler" berperingkat dengan jumlah kemunculan.*

Fitur statistik menyediakan ringkasan penggunaan aplikasi secara agregat
bagi administrator, diakses melalui rute `/stats` dengan mekanisme
pembatasan akses yang identik dengan halaman tambah dokumen — hanya
pengguna berstatus administrator yang dapat melihat halaman ini. Data
statistik diambil dari titik akhir `GET /api/stats` saat halaman dimuat,
yang menurut catatan pada kode sumber mengagregasi data dari log
percakapan backend mencakup seluruh pertanyaan (termasuk dari pengguna
anonim yang belum masuk akun) beserta jumlah akun dan sesi yang tersimpan.
Selama data belum tersedia, halaman menampilkan teks "Memuat statistik…",
dan apabila terjadi kegagalan pengambilan data, pesan kesalahan dari
server ditampilkan atau pesan bawaan "Gagal memuat statistik." sebagai
cadangan. Header halaman menampilkan judul "Statistik Pertanyaan" dengan
tautan panah kembali menuju halaman utama aplikasi.

Tiga kartu ringkasan metrik ditampilkan pada bagian atas halaman, masing-
masing dengan ikon berbeda: jumlah total pertanyaan yang pernah diajukan
ke sistem, jumlah akun terdaftar, dan jumlah sesi percakapan yang
tersimpan — seluruh angka diformat menggunakan pemisah ribuan sesuai
konvensi Bahasa Indonesia. Ketiga kartu ini memberi administrator
gambaran cepat mengenai skala pemakaian sistem tanpa perlu menelusuri
basis data secara manual. Format angka yang konsisten dengan lokal
Indonesia (`id-ID`) mencerminkan bahwa aplikasi ini memang ditujukan
khusus untuk audiens berbahasa Indonesia, sejalan dengan bahasa antarmuka
bawaan sistem secara keseluruhan. Ketiganya ditampilkan berdampingan tanpa
memerlukan interaksi tambahan seperti klik atau gulir, sehingga informasi
paling penting dapat langsung terlihat begitu halaman selesai dimuat.

Bagian "Pertanyaan per hari" menampilkan diagram batang horizontal
sederhana yang dibangun langsung menggunakan CSS (bukan pustaka
visualisasi data pihak ketiga), menampilkan jumlah pertanyaan untuk
tiga puluh hari terakhir. Setiap baris terdiri atas label tanggal, batang
horizontal yang lebarnya proporsional terhadap jumlah pertanyaan hari
tersebut dibandingkan hari dengan jumlah tertinggi dalam rentang yang
ditampilkan, dan angka jumlah pertanyaan itu sendiri. Pendekatan
implementasi mandiri tanpa pustaka eksternal ini menjaga ukuran berkas
aplikasi (*bundle size*) tetap ringan, mengingat kebutuhan visualisasi
pada halaman ini relatif sederhana dan tidak memerlukan interaktivitas
lanjutan seperti *zoom* atau *tooltip* yang kompleks. Apabila tidak
terdapat data pada rentang waktu tersebut, sistem menampilkan pesan
"Belum ada data." alih-alih menampilkan diagram kosong yang membingungkan.

Bagian "Pertanyaan terpopuler" menampilkan daftar berperingkat berisi
pertanyaan-pertanyaan yang paling sering diajukan pengguna, masing-masing
disertai nomor peringkat, teks pertanyaan lengkap, lencana berbentuk pil
yang menampilkan jumlah kemunculan (mis. "12×"), dan batang kemajuan tipis
yang panjangnya relatif terhadap pertanyaan dengan jumlah kemunculan
tertinggi dalam daftar tersebut. Fitur ini memberi wawasan berharga bagi
pengelola sistem mengenai kebutuhan informasi yang paling sering dicari
mahasiswa/pengguna, yang dapat dimanfaatkan untuk memprioritaskan dokumen
mana yang perlu diperbarui atau diperkaya konten sumbernya di dalam basis
pengetahuan. Secara keseluruhan, halaman statistik ini berfungsi sebagai
alat pemantauan berkelanjutan (*ongoing monitoring*) di luar konteks
evaluasi satu kali yang dijelaskan pada `docs/evaluation/`, memungkinkan
administrator memantau tren pemakaian sistem secara real-time setelah
aplikasi berjalan di lingkungan produksi.

## 4.x.7 Fitur Akun: Autentikasi, Ubah Kata Sandi, dan Ganti Akun

![Modal Masuk/Daftar pada tampilan desktop](screenshots/4x7_auth_modal_desktop.png)
*Gambar 4.7 — Dialog `AuthModal`: tab Masuk/Daftar dengan validasi kompleksitas kata sandi.*

Aplikasi menerapkan sistem autentikasi berbasis akun untuk membedakan
akses pengguna umum dari administrator, dengan kontrol terpusat pada
komponen menu pengguna (`UserMenu`) di bagian atas antarmuka. Bagi
pengunjung yang belum masuk akun, kontrol ini berupa tombol "Masuk"
bergaya garis (*outline*) dengan ikon masuk (*login*) yang membuka jendela
dialog autentikasi (`AuthModal`). Setelah masuk akun, kontrol berubah
menjadi tombol berbentuk pil menampilkan avatar lingkaran berwarna dengan
huruf pertama nama pengguna, nama pengguna itu sendiri, dan panah bawah
yang berputar 180 derajat ketika menu dropdown terbuka. Menu ini
menggunakan pemantauan klik di luar area menu (*document click listener*)
untuk menutup dirinya secara otomatis ketika pengguna mengeklik area lain
di halaman, sebuah pola interaksi standar bagi menu tarik-turun modern.

Jendela dialog autentikasi mendukung dua mode yang dapat ditukar melalui
tab "Masuk" dan "Daftar". Mode masuk memerlukan nama pengguna dan kata
sandi (dengan tombol mata untuk menampilkan/menyembunyikan karakter kata
sandi), sedangkan mode pendaftaran menambahkan kolom surel dan konfirmasi
kata sandi. Khusus pada mode pendaftaran, sistem menerapkan kebijakan
kompleksitas kata sandi yang divalidasi secara langsung (*real-time*)
saat pengguna mengetik: panjang minimal delapan karakter, minimal satu
huruf kecil, satu huruf besar, dan satu karakter khusus, dengan daftar
kesalahan yang belum terpenuhi ditampilkan sebagai poin-poin di bawah
kolom kata sandi. Setelah proses masuk atau daftar berhasil, sistem
memicu sebuah mekanisme teknis yang membangun formulir tersembunyi dan
mengirimkannya ke `about:blank` semata-mata untuk memancing kotak dialog
"simpan kata sandi" bawaan peramban muncul secara otomatis, sebuah teknik
yang meningkatkan kenyamanan pengguna dalam mengelola kredensial tanpa
memerlukan pengelola kata sandi pihak ketiga.

Fitur "Ubah Password" yang tersedia dari menu pengguna membuka dialog
tersendiri dengan tiga kolom (kata sandi lama, kata sandi baru, dan
konfirmasi), masing-masing dilengkapi tombol tampilkan/sembunyikan, dan
memvalidasi bahwa kata sandi baru serta konfirmasinya cocok dan memenuhi
panjang minimal delapan karakter sebelum dikirim ke server melalui titik
akhir perubahan kata sandi. Keberhasilan proses ditandai kotak konfirmasi
hijau dengan ikon centang yang menutup dirinya secara otomatis setelah dua
detik, memberi umpan balik yang jelas tanpa memerlukan interaksi tambahan
dari pengguna. Fitur pemulihan kata sandi lupa (*forgot password*) juga
telah dikembangkan pada level komponen dan backend, namun secara sengaja
dinonaktifkan pada pembangunan aplikasi tahap alfa ini karena belum
tersedia mekanisme pengiriman surel sungguhan untuk menyalurkan token
pemulihan kepada pengguna secara aman. Komponen ini tetap dipertahankan di
dalam basis kode sebagai fitur yang siap diaktifkan kembali begitu
infrastruktur pengiriman surel produksi tersedia, alih-alih dihapus
seluruhnya dari aplikasi.

Fitur "Ganti Akun" yang diminta secara khusus untuk didokumentasikan
diimplementasikan sebagai tautan pada menu pengguna yang, ketika diklik,
membuka kembali jendela dialog autentikasi yang sama persis dengan yang
digunakan untuk proses masuk awal — bukan sebuah mekanisme pengalihan
multi-akun tersendiri yang menyimpan beberapa sesi sekaligus. Dengan kata
lain, "berganti akun" pada implementasi saat ini berarti pengguna yang
sedang aktif dapat langsung memasukkan kredensial akun lain melalui
formulir masuk yang sama, yang secara implisit akan menggantikan sesi/token
otorisasi yang tersimpan di peramban dengan sesi akun baru tersebut. Menu
pengguna juga menampilkan dua tautan tambahan yang hanya muncul bagi
administrator — "Statistik Penggunaan" menuju halaman `/stats` dan "Tambah
Dokumen" menuju halaman `/admin` — dipisahkan dengan garis pembatas dari
menu umum lainnya, serta tombol "Keluar" bergaya destruktif (merah) yang
mengakhiri sesi pengguna melalui titik akhir keluar (*logout*) pada
backend. Rancangan menu terpadu ini memastikan seluruh fungsi terkait
identitas pengguna dapat diakses dari satu titik yang konsisten di seluruh
halaman aplikasi.

## 4.x.8 Pengujian Responsivitas Antarmuka (Desktop, Tablet, Mobile)

![Layar sambutan pada viewport mobile 375x812](screenshots/mobile_welcome.png)
*Gambar 4.8a — Layar sambutan pada viewport mobile (375×812 piksel).*

![Sidebar sebagai overlay drawer pada viewport mobile](screenshots/mobile_sidebar_drawer.png)
*Gambar 4.8b — Sidebar riwayat percakapan tampil sebagai panel tumpang tindih (off-canvas drawer) di mobile.*

![Panel Pengaturan pada viewport mobile](screenshots/mobile_settings.png)
*Gambar 4.8c — Panel Pengaturan tetap legible dengan scroll internal di lebar layar sempit.*

![Modal autentikasi pada viewport mobile](screenshots/mobile_auth.png)
*Gambar 4.8d — Dialog Masuk/Daftar menyesuaikan diri pada lebar layar ponsel.*

![Panel tablet 768x1024 menampilkan padding kanvas alat emulasi](screenshots/tablet_padding_artifact.png)
*Gambar 4.8e — Contoh area kanvas kosong (padding alat emulasi, bukan sisa tampilan desktop) pada viewport tablet.*

Selain diuji pada resolusi layar desktop standar, antarmuka aplikasi juga
diuji pada dua ukuran viewport tambahan untuk memverifikasi klaim
responsivitas rancangan: tablet (768×1024 piksel) dan mobile (375×812
piksel, setara lebar layar ponsel umum seperti iPhone SE). Pengujian
dilakukan menggunakan fitur emulasi viewport pada peramban, yang mengubah
lebar efektif tampilan tanpa memerlukan perangkat fisik tablet maupun
ponsel selama tahap pengembangan. Pendekatan ini dipilih karena seluruh
tata letak aplikasi dibangun dengan kelas responsif berbasis breakpoint
(mengikuti konvensi Tailwind CSS) yang secara teori seharusnya menyesuaikan
diri terhadap lebar viewport, sehingga pengujian lintas ukuran layar
menjadi langkah verifikasi yang penting sebelum klaim tersebut dicantumkan
sebagai kapabilitas sistem. Pengujian mencakup empat elemen antarmuka
utama: layar sambutan, sidebar riwayat percakapan, panel Pengaturan, dan
modal autentikasi.

Pada viewport mobile, sidebar riwayat percakapan yang pada tampilan
desktop selalu terlihat di sisi kiri secara otomatis menciut menjadi
sebuah ikon tunggal di pojok kiri atas, dan baru ditampilkan penuh sebagai
panel tumpang tindih (*overlay drawer*) ketika ikon tersebut diketuk —
pola desain yang lazim disebut *off-canvas navigation* pada pengembangan
aplikasi web responsif. Panel Pengaturan, yang pada tampilan desktop
berupa jendela dialog di tengah layar, tetap tampil sebagai kartu terpusat
yang lebar dan tata letak kontrolnya menyesuaikan diri sepenuhnya dengan
lebar layar sempit, lengkap dengan bilah gulir internal (*internal
scrollbar*) agar seluruh kontrol pengaturan tetap dapat dijangkau meski
tidak muat dalam satu layar penuh. Modal autentikasi (masuk/daftar) juga
terbukti menyesuaikan diri dengan baik, dengan seluruh kolom input dan
tombol tetap proporsional dan mudah dijangkau jari pada lebar layar
ponsel. Tidak ditemukan elemen yang terpotong, tumpang tindih secara tidak
disengaja, atau teks yang meluber keluar batas layar pada seluruh
viewport yang diuji.

Selama proses pengujian, ditemukan satu catatan metodologis terkait alat
bantu emulasi viewport yang digunakan: kanvas tangkapan layar yang
dihasilkan alat tersebut berukuran sedikit lebih besar dari dimensi
viewport yang diminta (mis. meminta 768×1024 piksel namun kanvas yang
dikembalikan berukuran 800×1066 piksel), menyisakan area kosong berwarna
polos di tepi kanan dan bawah tangkapan layar. Area kosong ini bukan
merupakan sisa tampilan versi desktop yang masih ter-*render* di baliknya,
melainkan sekadar latar belakang bawaan kanvas alat pengujian di luar
batas viewport yang sedang diemulasi — sebuah karakteristik dari
mekanisme *device emulation* yang mengubah lebar CSS di dalam kanvas
peramban berukuran tetap, bukan cacat pada CSS responsif aplikasi itu
sendiri. Temuan ini penting dicatat sebagai keterbatasan metodologi
pengujian, bukan sebagai kekurangan pada implementasi antarmuka aplikasi
yang sedang diuji.

Sebagai catatan bagi pengembangan lanjutan, disarankan agar pengujian
responsivitas pada tahap berikutnya dilakukan langsung melalui mode
emulasi perangkat bawaan peramban (*device toolbar*) yang tersedia pada
peramban modern seperti Google Chrome maupun Mozilla Firefox, karena mode
tersebut mengubah ukuran bingkai jendela peramban secara utuh mengikuti
dimensi perangkat yang dipilih, tanpa menyisakan area kanvas tambahan di
luar viewport seperti yang ditemukan pada alat pengujian otomatis yang
dipakai dalam penelitian ini. Pendekatan tersebut juga tidak memerlukan
kepemilikan perangkat Android maupun iOS secara fisik, sehingga pengujian
lintas perangkat tetap dapat dilakukan sepenuhnya di lingkungan
pengembangan desktop. Secara keseluruhan, hasil pengujian pada ketiga
kelas ukuran layar ini memberikan bukti pendukung bahwa antarmuka
aplikasi telah memenuhi prinsip *responsive web design*, sehingga dapat
diakses dengan pengalaman yang layak baik oleh pengguna desktop, tablet,
maupun ponsel tanpa memerlukan aplikasi native terpisah untuk setiap
platform. Temuan ini relevan khususnya bagi mahasiswa yang mengakses
chatbot ini melalui ponsel pribadi mereka, mengingat pola akses layanan
informasi kampus di kalangan mahasiswa Indonesia saat ini didominasi oleh
perangkat mobile dibandingkan komputer desktop.
