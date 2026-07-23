# Implementasi Wazuh sebagai Sistem Monitoring Keamanan Server dengan Elastic Stack dan Notifikasi Telegram

> Source: https://kd-cibiru.upi.edu/index.php/daftar-kategori/prodi-tekkom/artikel-tekkom/implementasi-wazuh-sebagai-sistem-monitoring-keamanan-server-dengan-elastic-stack-dan-notifikasi-telegram

Implementasi Wazuh sebagai Sistem Monitoring Keamanan Server dengan Elastic Stack dan Notifikasi Telegram
28 Februari 2025
Admin TEKKOM
Artikel TEKKOM
Implementasi Wazuh sebagai Sistem Monitoring Keamanan Server dengan Elastic Stack dan Notifikasi Telegram
Pendahuluan

Dalam dunia digital yang semakin berkembang, keamanan server menjadi prioritas utama bagi perusahaan dan organisasi. Serangan siber yang terus meningkat menuntut adanya sistem monitoring keamanan yang canggih dan responsif. Salah satu solusi yang banyak digunakan adalah Wazuh, sebuah platform open-source yang berfungsi sebagai Host-based Intrusion Detection System (HIDS), memungkinkan pemantauan aktivitas server secara real-time serta deteksi ancaman keamanan dengan efisiensi tinggi.

Untuk meningkatkan efektivitasnya, Wazuh dapat dikombinasikan dengan Elastic Stack (terdiri dari Elasticsearch, Logstash, dan Kibana) untuk memvisualisasikan data keamanan, serta Telegram sebagai media notifikasi untuk memberikan peringatan instan kepada administrator sistem.

Artikel ini akan membahas bagaimana implementasi Wazuh dengan Elastic Stack dan Notifikasi Telegram dapat membantu meningkatkan keamanan server secara optimal.

Apa Itu Wazuh?

Wazuh adalah platform keamanan open-source yang memiliki berbagai fitur unggulan, seperti:

Deteksi Intrusi (IDS/IPS): Mengidentifikasi aktivitas mencurigakan berdasarkan aturan yang telah ditetapkan.
Monitoring Integritas File (FIM): Memantau perubahan pada file penting dalam sistem.
Deteksi Malware dan Rootkit: Menganalisis potensi ancaman berbahaya yang ada di dalam server.
Manajemen Kepatuhan (Compliance Management): Memastikan sistem memenuhi standar keamanan seperti PCI-DSS, GDPR, dan lainnya.
Analisis Log Keamanan: Mengumpulkan dan menganalisis log dari berbagai perangkat serta aplikasi dalam jaringan.

Wazuh bekerja dengan agen (agent) yang dipasang pada setiap server yang ingin dipantau, serta server pusat yang mengelola data dari seluruh agen.

Integrasi Wazuh dengan Elastic Stack

Elastic Stack (sebelumnya ELK Stack) terdiri dari tiga komponen utama:

Elasticsearch: Mesin pencarian dan analisis data yang menyimpan serta mengindeks log dari Wazuh.
Logstash: Alat untuk mengumpulkan, memproses, dan mengirimkan log ke Elasticsearch.
Kibana: Platform visualisasi yang digunakan untuk menampilkan data dalam bentuk grafik dan dashboard interaktif.

Dengan mengintegrasikan Wazuh ke dalam Elastic Stack, administrator dapat memantau aktivitas keamanan server melalui antarmuka yang mudah dipahami, memungkinkan mereka untuk mengidentifikasi ancaman dengan lebih cepat.

Implementasi Wazuh dengan Elastic Stack dan Telegram
1. Instalasi dan Konfigurasi Wazuh

Langkah pertama dalam implementasi ini adalah menginstal Wazuh Server serta Wazuh Agent pada setiap server yang akan dimonitor.

a. Instalasi Wazuh Server
Unduh dan instal Wazuh di server utama.
Konfigurasikan server agar dapat menerima data dari agen yang terpasang di server lain.
Pastikan Wazuh Manager berjalan dan dapat mengolah data log keamanan.

shCopyEditcurl -sO https://packages.wazuh.com/4.x/wazuh-install.shsudo bash wazuh-install.sh --install-server

b. Instalasi Wazuh Agent di Server yang Dipantau
Pasang agen Wazuh pada server yang ingin dimonitor.
Hubungkan agen ke server pusat Wazuh.

shCopyEditcurl -sO https://packages.wazuh.com/4.x/wazuh-install.shsudo bash wazuh-install.sh --install-agent

Konfigurasi /var/ossec/etc/ossec.conf untuk menghubungkan agen ke server Wazuh:

xmlCopyEdit<server>  <address>IP_WAZUH_SERVER</address>  <port>1514</port>  <protocol>tcp</protocol></server>

Jalankan agen:

shCopyEditsudo systemctl start wazuh-agent

2. Integrasi Wazuh dengan Elastic Stack

Untuk menghubungkan Wazuh dengan Elastic Stack, lakukan langkah-langkah berikut:

a. Instalasi Elasticsearch

shCopyEditsudo apt install elasticsearchsudo systemctl enable --now elasticsearch

b. Instalasi Logstash
Konfigurasikan Logstash untuk menerima data dari Wazuh:

shCopyEditsudo apt install logstashsudo nano /etc/logstash/conf.d/wazuh.conf

Tambahkan konfigurasi berikut:

jsonCopyEditinput {  beats {    port => 5044  }}output {  elasticsearch {    hosts => ["http://localhost:9200"]    index => "wazuh-alerts-%{+YYYY.MM.dd}"  }}

Jalankan Logstash:

shCopyEditsudo systemctl start logstash

c. Instalasi Kibana untuk Visualisasi
Instal Kibana dan tambahkan plugin Wazuh:

shCopyEditsudo apt install kibanasudo systemctl enable --now kibana

Konfigurasi Kibana agar dapat membaca data dari Elasticsearch.
Akses Kibana melalui browser di http://server-ip:5601 dan tambahkan dashboard Wazuh untuk memantau ancaman secara real-time.
3. Integrasi Notifikasi Telegram untuk Peringatan Instan

Agar administrator dapat menerima peringatan secara langsung di Telegram ketika ada ancaman, integrasikan Wazuh dengan Telegram menggunakan webhook API.

a. Buat Bot Telegram
Gunakan @BotFather di Telegram untuk membuat bot baru.
Dapatkan token API bot yang akan digunakan untuk mengirim pesan.
b. Buat Skrip Notifikasi Telegram

Buat skrip Python untuk mengirim peringatan ke Telegram saat Wazuh mendeteksi ancaman:

pythonCopyEditimport requests TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"CHAT_ID = "YOUR_CHAT_ID"MESSAGE = "⚠️ Peringatan Keamanan: Ancaman terdeteksi di server!" def send_telegram_alert(message):    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"    payload = {"chat_id": CHAT_ID, "text": message}    requests.post(url, data=payload) send_telegram_alert(MESSAGE)

c. Hubungkan Wazuh dengan Skrip Notifikasi

Tambahkan aturan di Wazuh agar setiap kali ada ancaman, skrip Telegram dijalankan:

shCopyEditecho "/usr/bin/python3 /path/to/telegram_alert.py" >> /var/ossec/etc/ossec.conf

Restart Wazuh Manager untuk menerapkan perubahan:

shCopyEditsudo systemctl restart wazuh-manager

Dengan konfigurasi ini, setiap kali ancaman terdeteksi, Wazuh akan mengirimkan notifikasi ke Telegram, memungkinkan administrator merespons lebih cepat terhadap insiden keamanan.

Keuntungan Implementasi Wazuh, Elastic Stack, dan Telegram
Deteksi dan Respon Cepat terhadap Ancaman
Wazuh memantau aktivitas server secara real-time.
Telegram memberikan notifikasi instan kepada administrator.
Visualisasi Data yang Mudah dengan Kibana
Administrator dapat menganalisis pola serangan dengan lebih efisien.
Efisiensi Pengelolaan Keamanan Server
Proses pemantauan otomatis mengurangi risiko kesalahan manusia.
Sistem Open-Source dengan Biaya Rendah
Tidak memerlukan lisensi mahal, tetapi tetap menawarkan fitur keamanan canggih.

 

Kesimpulan

Implementasi Wazuh sebagai sistem monitoring keamanan, dikombinasikan dengan Elastic Stack untuk analisis data dan Telegram untuk notifikasi real-time, memberikan solusi yang kuat dan efisien dalam mengamankan server. Dengan sistem ini, administrator dapat memantau, mendeteksi, dan merespons ancaman keamanan dengan lebih cepat dan efektif.

TEKNIK KOMPUTER

Dilihat: 1208
Previous article: Website vs Aplikasi: Mana yang Lebih Efektif untuk Menyelesaikan Studi Kasus Anda? Sebelum
Next article: Implementasi Steganografi PDF dengan Manipulasi Stream dan Enkripsi AES-256 untuk Keamanan Data Berikut
FaLang translation system by Faboba
