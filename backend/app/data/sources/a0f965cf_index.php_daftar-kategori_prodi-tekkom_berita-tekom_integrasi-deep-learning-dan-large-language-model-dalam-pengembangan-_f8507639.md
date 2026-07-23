# Integration of Deep Learning and Large Language Models in Chatbot Development for Skin Cancer Detection

> Source: https://kd-cibiru.upi.edu/index.php/daftar-kategori/prodi-tekkom/berita-tekom/integrasi-deep-learning-dan-large-language-model-dalam-pengembangan-chatbot-untuk-deteksi-kanker-kulit

Integration of Deep Learning and Large Language Models in Chatbot Development for Skin Cancer Detection
November 13, 2025
TEKKOM Admin
TEKKOM News
Integration of Deep Learning and Large Language Models in Chatbot Development for Skin Cancer Detection

Skin cancer is a highly prevalent disease worldwide, yet early detection is often hampered by limited access to dermatology professionals. Advances in artificial intelligence (AI) technology offer opportunities for intelligent chatbot- based solutions that can facilitate rapid and affordable early detection of skin cancer. This article discusses the integration of Deep Learning (DL) for skin image analysis with a Large Language Model (LLM) as a natural language interaction system, enabling the chatbot to provide adaptive and informative interpretations of results, education, and initial medical recommendations.

1. Introduction

Early detection of skin cancer, especially melanoma , is crucial for successful treatment. However, many patients lack access to dermatologists due to limited facilities and costs. This creates a need for intelligent diagnostic tools that are easy for the general public to use.

In this context, the integration of Deep Learning and Large Language Models (LLMs) presents a potential solution. Deep Learning , particularly through Convolutional Neural Network (CNN) models , has proven effective in analyzing medical images. Meanwhile, LLMs such as GPT , BERT , or MedPaLM can understand the user's natural language and convey analysis results in a narrative and empathetic manner. The combination of the two creates a chatbot capable of detecting, explaining, and providing initial guidance regarding potential skin cancer.

2. System Architecture

This skin cancer detection chatbot system is built through three main components:

2.1. Image Analysis Module (Deep Learning)

Using CNN (Convolutional Neural Network) to process uploaded user skin images.

The dataset was trained using dermatology databases such as ISIC (International Skin Imaging Collaboration) which contains thousands of images of skin lesions.

The models are classified to differentiate between several categories: normal, melanoma, basal cell carcinoma, and squamous cell carcinoma .

Hasil analisis berupa tingkat probabilitas (misal: “lesi ini memiliki kemiripan 87% dengan melanoma”).

2.2. Modul Bahasa dan Interaksi (Large Language Model)

LLM digunakan untuk memproses input teks pengguna, menjawab pertanyaan, dan menghasilkan narasi hasil analisis.

Model bahasa ini mampu:

Mengubah hasil numerik dari CNN menjadi deskripsi yang mudah dipahami.

Memberikan rekomendasi non-diagnostik, seperti saran untuk konsultasi ke dokter spesialis.

Memberikan edukasi tentang pencegahan kanker kulit (misalnya penggunaan tabir surya, pemeriksaan rutin).

2.3. Integrasi dan Antarmuka Chatbot

Sistem integrasi menggunakan API antara model CNN dan LLM.

LLM menginterpretasikan output CNN, lalu menyusunnya menjadi respons natural seperti:

“Berdasarkan gambar yang Anda unggah, terdapat kemungkinan tinggi bahwa lesi kulit ini bersifat mencurigakan. Sebaiknya segera konsultasikan ke dokter kulit untuk pemeriksaan lanjutan.”

3. Hasil Implementasi dan Evaluasi

Eksperimen dilakukan menggunakan dataset ISIC 2020, dengan model CNN berbasis EfficientNet-B4. Model mencapai akurasi 91,8% dalam membedakan melanoma dari lesi jinak.

LLM yang digunakan (misalnya GPT-4 atau MedPaLM) diintegrasikan untuk menjawab lebih dari 500 skenario pertanyaan pengguna, dengan tingkat kepuasan pengguna sebesar 88%, berdasarkan survei usability.

Selain itu, chatbot diuji pada 100 responden non-medis. Hasil menunjukkan:

92% responden memahami hasil analisis setelah dijelaskan oleh LLM.

80% menyatakan chatbot membantu mereka menentukan langkah awal menuju pemeriksaan profesional.

4. Keterkaitan dengan Tujuan Pembangunan Berkelanjutan (SDGs)

Pengembangan chatbot ini berkontribusi terhadap:

SDG 3: Kehidupan Sehat dan Sejahtera (Good Health and Well-being) — meningkatkan akses deteksi dini penyakit.

SDG 9: Inovasi dan Infrastruktur — memanfaatkan teknologi AI untuk pelayanan kesehatan digital.

SDG 10: Mengurangi Ketimpangan — menyediakan akses diagnosis awal untuk masyarakat di daerah minim fasilitas medis.

5. Tantangan dan Pengembangan Lanjutan

Beberapa tantangan yang masih perlu diatasi meliputi:

Keakuratan data citra yang dipengaruhi pencahayaan atau perangkat kamera pengguna.

Etika dan privasi medis, karena gambar kulit termasuk data sensitif.

Kebutuhan validasi klinis agar hasil chatbot dapat diakui oleh lembaga medis.

Ke depan, sistem dapat ditingkatkan melalui:

Integrasi multimodal LLM, yang memproses gambar dan teks secara bersamaan.

Penggunaan federated learning untuk menjaga privasi data pasien.

Kolaborasi dengan rumah sakit untuk validasi hasil berbasis data dunia nyata.

6. Conclusion

The integration of deep learning and large language models into a health chatbot represents a significant innovation in the early detection of skin cancer. This technology combines high-precision visual analysis with natural communication capabilities , not only helping users recognize early symptoms but also improving public health literacy.

With continued development and collaboration between AI experts, dermatologists, and medical institutions, this chatbot has the potential to become an intelligent digital health assistant that supports early skin cancer screening globally.

SDGs 3: Healthy and Prosperous Lives , SDGs 9: Industry, Innovation, and Infrastructure

Views: 168
Previous article: UPI Cibiru Computer Engineering Study Program Holds "IT for School" at SMAN 24 Bandung and SMKN 2 Bandung Before
Next article: UPI Computer Engineering Students Achieve Excellence in the 2025 Bandung Bedas Innovation Competition Following
FaLang translation system by Faboba
