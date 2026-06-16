# Panduan Fine-Tuning LLM untuk Chatbot RAG UPI

Panduan praktis untuk meng-_fine-tune_ model lokal (Llama 3.1 8B / Qwen 2.5 7B)
agar respons chatbot lebih baik. Ditulis khusus untuk setup skripsi Anda:
Windows, Ollama lokal, korpus dokumen UPI, anggaran terbatas.

---

## ⚠️ BACA INI DULU: Apakah fine-tuning benar-benar Anda butuhkan?

Untuk sistem **RAG**, fine-tuning **sering bukan** cara terbaik untuk memperbaiki
jawaban. Alasannya:

| Masalah jawaban | Penyebab sebenarnya | Solusi terbaik |
|---|---|---|
| Jawaban "tidak tersedia" padahal sumber ada | `num_ctx` truncation / retrieval salah | **Perbaikan config & retrieval** (sudah dilakukan) |
| Jawaban mengarang fakta | Model kecil + prompt lemah | **Prompt + model lebih besar** |
| Jawaban tidak menyertakan sitasi `[1]` | Instruksi prompt diabaikan model kecil | **Prompt few-shot + model 7-8B** |
| Jawaban dari tabel rusak (`## 4 450 000`) | Ekstraksi PDF rusak | **Re-ekstraksi (pdfplumber)** — fine-tuning TIDAK membantu |
| Gaya bahasa kurang baku / bertele-tele | Karakteristik model dasar | **Fine-tuning BISA membantu di sini** ✅ |

**Aturan emas:** Fine-tuning untuk RAG **tidak** untuk menambah _pengetahuan_
(itu tugas retrieval). Fine-tuning berguna untuk **gaya, format, dan perilaku**:
cara menulis sitasi, cara menolak dengan sopan, register Bahasa Indonesia baku,
panjang jawaban yang konsisten.

Jadi: **kalau jawaban buruk karena retrieval/prompt, perbaiki itu dulu.**
Fine-tuning baru masuk akal kalau retrieval sudah bagus tapi Anda ingin
mengontrol _gaya jawaban_ secara konsisten.

> **Untuk skripsi:** fine-tuning adalah kontribusi metodologi yang kuat dan
> sah secara akademik — _selama Anda jujur_ bahwa tujuannya adalah perbaikan
> **gaya/format**, bukan pengetahuan. Ini bisa jadi satu bab tersendiri.

---

## Apa yang BISA dan TIDAK BISA diperbaiki fine-tuning

✅ **Bisa diperbaiki:**
- Konsistensi format sitasi `[1][2]` di setiap kalimat
- Register Bahasa Indonesia akademik/baku yang konsisten
- Penolakan sopan yang seragam ("Maaf, informasi tersebut tidak tersedia…")
- Panjang jawaban yang terkontrol (tidak bertele-tele)
- Mengenali pertanyaan di luar domain UPI dan menolaknya
- Mengurangi "Catatan:" dan kalimat pembuka yang tidak perlu

❌ **Tidak bisa diperbaiki:**
- Fakta yang tidak ada di korpus (itu tugas retrieval)
- Chunk tabel yang rusak saat ekstraksi
- Retrieval yang mengembalikan dokumen salah
- Pengetahuan terkini (tanggal, biaya, kebijakan baru)

---

## Prasyarat: Anda butuh GPU

Fine-tuning model 7-8B **tidak bisa** di CPU laptop Anda (embedding saja sudah
berjam-jam). Pilihan realistis dan **gratis**:

| Platform | GPU | VRAM | Batas | Cocok? |
|---|---|---|---|---|
| **Google Colab (free)** | T4 | 16 GB | ~4 jam/sesi | ✅ Paling mudah |
| **Kaggle Notebooks** | T4 ×2 / P100 | 16 GB | 30 jam/minggu | ✅ Sesi lebih panjang |
| **Colab Pro** | T4/L4/A100 | 16-40 GB | Rp ~160 rb/bln | Opsional |

Dengan **QLoRA (4-bit) + Unsloth**, model 7-8B muat di T4 16 GB. Inilah jalur
yang kita pakai.

---

## Strategi: QLoRA + Unsloth + Colab gratis

- **QLoRA** = fine-tune hanya sebagian kecil parameter (adapter LoRA) pada model
  yang dikuantisasi 4-bit. Hemat memori drastis; cukup untuk T4.
- **Unsloth** = library yang membuat QLoRA ~2× lebih cepat dan ~70% lebih hemat
  memori. Mendukung Llama 3.1, Qwen 2.5, Gemma 2.
- **Export → GGUF → Ollama** = hasil fine-tune langsung masuk ke stack Ollama
  Anda yang sudah ada. Backend tidak perlu diubah.

Alur lengkap:

```
Korpus UPI (chunks.jsonl)
       |
       v
[1] Bangun dataset instruksi  (build_finetuning_dataset.py — di laptop)
       |  -> finetune_dataset.jsonl  (format ChatML)
       v
[2] Upload ke Google Colab
       |
       v
[3] Train QLoRA dgn Unsloth  (notebook Colab — di GPU gratis)
       |  -> adapter LoRA
       v
[4] Merge + export ke GGUF   (di Colab)
       |  -> model-upi.gguf
       v
[5] Download GGUF -> Modelfile -> ollama create upi-chat
       |
       v
[6] Pilih "upi-chat" di dropdown Model frontend
```

---

## Langkah 1 — Bangun dataset instruksi (di laptop Anda)

Kualitas dataset = kualitas hasil. **Garbage in, garbage out.** Untuk memperbaiki
_gaya_, Anda butuh **200-1000 contoh** berkualitas berbentuk:

```
(system prompt aturan) + (konteks dari retrieval) + (pertanyaan)  ->  (jawaban ideal)
```

Jalankan skrip yang sudah saya buat:

```powershell
cd "D:\Project\RAG_UPI\Source code"
python build_finetuning_dataset.py --n-questions 300 --teacher qwen2.5:7b
```

Skrip ini:
1. Mengambil pertanyaan dari `Dataset/evaluation.csv` + meng-_generate_ pertanyaan
   tambahan dari isi chunk.
2. Untuk tiap pertanyaan, melakukan **retrieval nyata** dari FAISS Anda.
3. Membuat jawaban kandidat dengan model "guru" (mis. `qwen2.5:7b`) memakai
   prompt grounded yang baik.
4. Menyimpan `finetune_dataset.jsonl` dalam format ChatML siap Unsloth.

> ⚠️ **WAJIB:** Skrip menghasilkan jawaban _kandidat_. Anda **harus meninjau dan
> mengedit** sebagian besar (atau semua) sebelum training. Kalau jawaban guru
> jelek, model hasil fine-tune juga akan jelek. Untuk skripsi, **kurasi manual
> minimal 200 contoh** memberi hasil jauh lebih baik daripada 1000 contoh mentah.

### Format dataset (ChatML)

Setiap baris `finetune_dataset.jsonl` berbentuk:

```json
{"messages": [
  {"role": "system", "content": "Anda adalah asisten resmi UPI. Jawab HANYA dari SUMBER bernomor, sertakan [1][2]..."},
  {"role": "user", "content": "SUMBER:\n[1] ...\n[2] ...\n\nPERTANYAAN: Berapa biaya pendaftaran Magister?"},
  {"role": "assistant", "content": "Biaya pendaftaran Program Magister (S2) UPI adalah Rp 750.000 per peserta [1]. Catatan: ini biaya seleksi, bukan UKT per semester [1]."}
]}
```

---

## Langkah 2 & 3 — Training di Google Colab

1. Buka https://colab.research.google.com → New Notebook.
2. **Runtime → Change runtime type → T4 GPU**.
3. Upload `finetune_dataset.jsonl` (ikon folder di kiri → upload).
4. Tempel sel-sel berikut.

### Sel 1 — Install Unsloth

```python
%%capture
!pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
!pip install --no-deps "xformers<0.0.27" trl peft accelerate bitsandbytes
```

### Sel 2 — Muat model 4-bit

```python
from unsloth import FastLanguageModel
import torch

max_seq_length = 4096   # cukup untuk system + 5 chunk + jawaban
model, tokenizer = FastLanguageModel.from_pretrained(
    # Ganti sesuai model dasar yang Anda pakai di Ollama:
    model_name = "unsloth/Qwen2.5-7B-Instruct-bnb-4bit",
    # alternatif: "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit"
    max_seq_length = max_seq_length,
    dtype = None,            # auto (float16 di T4)
    load_in_4bit = True,
)

# Tambahkan adapter LoRA (hanya ~1-2% parameter yang dilatih)
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,                 # rank LoRA; 16 cukup
    target_modules = ["q_proj","k_proj","v_proj","o_proj",
                      "gate_proj","up_proj","down_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 42,
)
```

### Sel 3 — Muat dataset

```python
from datasets import load_dataset

dataset = load_dataset("json", data_files="finetune_dataset.jsonl", split="train")

def format_chat(example):
    return {"text": tokenizer.apply_chat_template(
        example["messages"], tokenize=False, add_generation_prompt=False)}

dataset = dataset.map(format_chat)
print(dataset[0]["text"][:500])
print(f"Total contoh: {len(dataset)}")
```

### Sel 4 — Latih

```python
from trl import SFTTrainer
from transformers import TrainingArguments

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,   # batch efektif = 8
        warmup_steps = 5,
        num_train_epochs = 2,              # 1-3 epoch; lebih = overfitting
        learning_rate = 2e-4,
        fp16 = True,
        logging_steps = 5,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 42,
        output_dir = "outputs",
    ),
)
trainer.train()
```

Dengan ~300 contoh dan 2 epoch, training di T4 selesai dalam **10-30 menit**.

### Sel 5 — Uji cepat

```python
FastLanguageModel.for_inference(model)
messages = [
    {"role":"system","content":"Anda adalah asisten resmi UPI. Jawab HANYA dari SUMBER, sertakan [1][2]."},
    {"role":"user","content":"SUMBER:\n[1] Biaya pendaftaran Program Magister (S2) sebesar Rp 750.000 per peserta.\n\nPERTANYAAN: Berapa biaya daftar Magister?"},
]
inputs = tokenizer.apply_chat_template(messages, tokenize=True,
            add_generation_prompt=True, return_tensors="pt").to("cuda")
out = model.generate(input_ids=inputs, max_new_tokens=256, temperature=0.1)
print(tokenizer.decode(out[0], skip_special_tokens=True))
```

---

## Langkah 4 — Export ke GGUF (di Colab)

```python
# Merge adapter + kuantisasi ke GGUF Q4_K_M (seimbang ukuran/kualitas)
model.save_pretrained_gguf("upi-model", tokenizer, quantization_method="q4_k_m")
```

Ini menghasilkan file `.gguf` (~4-5 GB). Download ke laptop:

```python
from google.colab import files
import glob
gguf = glob.glob("upi-model/*.gguf")[0]
files.download(gguf)   # simpan ke D:\Project\RAG_UPI\models\upi-model.gguf
```

---

## Langkah 5 — Import ke Ollama (di laptop)

Buat file `Modelfile` (tanpa ekstensi) di samping GGUF:

```dockerfile
FROM ./upi-model.gguf

# Samakan dengan sistem prompt produksi Anda
SYSTEM """Anda adalah asisten informasi resmi Universitas Pendidikan Indonesia (UPI). Jawab HANYA dari SUMBER bernomor, sertakan [1][2] di setiap fakta. Jangan mengarang. Bahasa Indonesia baku."""

PARAMETER temperature 0.1
PARAMETER num_ctx 8192
PARAMETER stop "<|im_end|>"
```

Lalu:

```powershell
cd "D:\Project\RAG_UPI\models"
ollama create upi-chat -f Modelfile
ollama list           # pastikan "upi-chat" muncul
ollama run upi-chat "Tes: Berapa biaya daftar Magister?"
```

### Pakai di chatbot Anda

Tambahkan ke dropdown Model di frontend
(`Claude/frontend/components/settings/SettingsModal.tsx`):

```tsx
<SelectItem value="upi-chat">UPI Fine-tuned (hasil skripsi)</SelectItem>
```

Karena backend sudah mendukung override model per-request, model fine-tune Anda
langsung bisa dipilih — **tanpa ubah backend**.

---

## Langkah 6 — Evaluasi (BUKTI untuk skripsi)

Inilah bagian terpenting untuk skripsi: **buktikan** fine-tune Anda lebih baik.

1. Set `CONFIG["judge_model"]` / model di **notebook 05 & 06** ke `upi-chat`.
2. Jalankan ulang RAGAS (05) dan metrik IR (06).
3. Bandingkan tabel **sebelum** (Qwen 2.5 7B base) vs **sesudah** (upi-chat):

| Metrik | Base (Qwen 2.5 7B) | Fine-tuned (upi-chat) |
|---|---|---|
| Faithfulness | 0.xx | 0.xx |
| Answer Relevancy | 0.xx | 0.xx |
| Citation rate | 0.xx | 0.xx |
| Refusal correctness | 0.xx | 0.xx |

Tabel perbandingan ini = inti bab eksperimen skripsi Anda.

---

## Jebakan umum (hindari ini)

1. **Overfitting** — terlalu banyak epoch (>3) atau dataset terlalu kecil membuat
   model menghafal dan jadi kaku. Gunakan 2 epoch, ≥200 contoh beragam.
2. **Dataset jelek** — jawaban guru yang tidak dikurasi → model meniru kesalahan.
   **Kurasi manual** adalah investasi terpenting.
3. **Fine-tune untuk fakta** — jangan masukkan jawaban berisi tanggal/biaya
   spesifik berharap model menghafal. Itu tugas retrieval. Fokus ke _gaya_.
4. **Chat template salah** — pakai template yang sesuai model dasar (Unsloth
   menanganinya otomatis via `apply_chat_template`). Jangan campur format.
5. **Lupa `num_ctx`** di Modelfile — default Ollama 2048 akan truncate lagi.
6. **Tidak ada baseline** — selalu ukur model SEBELUM fine-tune untuk pembanding.

---

## Rekomendasi jujur untuk situasi Anda

Jika waktu skripsi mepet, urutan prioritas:

1. **(Sudah) Perbaiki num_ctx + retrieval dedup** — dampak terbesar, usaha kecil.
2. **Pakai Qwen 2.5 7B** sebagai model utama — kualitas Indonesia naik signifikan.
3. **Fine-tuning** — kerjakan **hanya jika** Anda punya 2-3 hari luang DAN ingin
   kontribusi metodologi tambahan untuk skripsi. Hasilnya bagus untuk bab
   "eksperimen", tapi bukan keajaiban.

Fine-tuning adalah _nilai tambah_ skripsi yang bagus (menunjukkan Anda menguasai
LoRA/QLoRA), tapi **bukan** perbaikan ajaib. Sampaikan dengan jujur di sidang:
fine-tuning memperbaiki **konsistensi gaya dan format sitasi**, sementara
**akurasi faktual tetap ditentukan oleh kualitas retrieval**.

---

## Ringkasan perintah

```powershell
# 1. Bangun dataset (laptop)
cd "D:\Project\RAG_UPI\Source code"
python build_finetuning_dataset.py --n-questions 300 --teacher qwen2.5:7b
# 2. Kurasi finetune_dataset.jsonl secara MANUAL
# 3. Upload ke Colab, latih dengan Unsloth (notebook di atas)
# 4. Export GGUF, download
# 5. Import ke Ollama:
ollama create upi-chat -f Modelfile
# 6. Evaluasi dengan notebook 05 & 06, bandingkan dengan baseline
```
