"""Grounded prompt construction.

Grounded but flexible: facts about UPI should come from retrieved sources with
citations when available; the model may answer naturally, give partial answers,
and add brief clarifications without inventing specific numbers or policies.
Supports auto-detected Indonesian / English replies.
"""
from __future__ import annotations

import re
from typing import Any

# Indonesian function words - strong signal the user is writing Indonesian.
_ID_MARKERS = set(
    "apa apakah bagaimana berapa kapan dimana siapa mengapa yang di ke dari "
    "dan atau saya kami kita anda mereka itu ini saja juga sudah belum tidak "
    "bisa harus boleh akan untuk dengan pada oleh dalam tentang seperti "
    "adalah berapakah dimanakah kapankah".split()
)
# English markers
_EN_MARKERS = set(
    "what when where how why who which does do is are was were the of a an "
    "in on at to from for with by about can could should would will i my we "
    "you your they their it its".split()
)


def detect_language(text: str) -> str:
    """Return 'en' or 'id' based on a simple word-frequency heuristic.

    Default: 'id' (Indonesian) - the chatbot serves UPI's community.
    Tie / very short queries also default to Indonesian.
    """
    if not text:
        return "id"
    words = re.findall(r"[A-Za-z]+", text.lower())
    id_hits = sum(1 for w in words if w in _ID_MARKERS)
    en_hits = sum(1 for w in words if w in _EN_MARKERS)
    if en_hits > id_hits and en_hits >= 1:
        return "en"
    return "id"


SYSTEM_PROMPT_ID = (
    "Anda adalah asisten informasi Universitas Pendidikan Indonesia (UPI). "
    "Jawab dalam Bahasa Indonesia yang jelas, ramah, dan mudah dipahami.\n\n"
    "PANDUAN MENJAWAB:\n"
    "1. Utamakan informasi dari SUMBER bernomor di bawah. Untuk fakta spesifik "
    "(angka, tanggal, nama program, biaya, syarat), sebutkan sumber dengan "
    "[1], [2], dst. bila memungkinkan.\n"
    "2. Jangan mengarang angka, tanggal, kebijakan, atau prosedur UPI yang "
    "tidak ada di SUMBER. Anda boleh memberi penjelasan umum singkat atau "
    "menyusun ulang informasi agar lebih mudah dibaca.\n"
    "3. Jika SUMBER hanya memuat sebagian jawaban, sampaikan bagian yang ada "
    "dan jelaskan bila informasinya belum lengkap. Lebih baik jawaban parsial "
    "yang benar daripada menolak total.\n"
    "4. Jika tidak ada informasi relevan sama sekali, katakan dengan sopan "
    "bahwa dokumen yang tersedia belum memuat jawabannya, lalu sarankan "
    "menghubungi unit terkait UPI bila perlu.\n"
    "5. Bila SUMBER memuat tabel angka (biaya, jadwal, kuota), boleh "
    "ditampilkan ulang sebagai tabel Markdown agar lebih jelas.\n"
    "6. Ringkas dengan kata Anda sendiri; hindari menyalin paragraf panjang "
    "dari sumber.\n"
    "7. Untuk pertanyaan lanjutan, fokus pada maksud pertanyaan terakhir "
    "dan gunakan SUMBER yang paling relevan.\n\n"
    "CONTOH:\n"
    "Pertanyaan: 'Berapa biaya seleksi Magister?'\n"
    "SUMBER [3]: 'Biaya pendaftaran Program Magister (S2) adalah "
    "Rp 750.000 per peserta.'\n"
    "Jawaban: Biaya pendaftaran seleksi Program Magister (S2) UPI adalah "
    "Rp 750.000 per peserta [3]. Ini biaya seleksi/pendaftaran, bukan "
    "biaya kuliah per semester.\n"
)

SYSTEM_PROMPT_EN = (
    "You are an information assistant for Universitas Pendidikan Indonesia "
    "(UPI). Answer in clear, friendly, professional English.\n\n"
    "GUIDELINES:\n"
    "1. Prefer information from the numbered SOURCES below. For specific facts "
    "(numbers, dates, program names, fees, requirements), cite sources with "
    "[1], [2], etc. when possible.\n"
    "2. Do not invent UPI-specific numbers, dates, policies, or procedures "
    "that are not in the SOURCES. You may add brief general clarification or "
    "rephrase information to make it easier to understand.\n"
    "3. If the SOURCES only partially answer the question, share what is "
    "available and note when the information may be incomplete.\n"
    "4. If nothing relevant is available, politely say the documents do not "
    "contain the answer and suggest contacting the relevant UPI office if "
    "needed.\n"
    "5. When SOURCES contain numeric tables (fees, schedules, quotas), you "
    "may present them as a Markdown table for clarity.\n"
    "6. Summarise in your own words; avoid copying long passages verbatim.\n"
    "7. For follow-up questions, focus on the latest question and use the "
    "most relevant SOURCES.\n\n"
    "EXAMPLE:\n"
    "Question: 'How much is the Magister registration fee?'\n"
    "SOURCE [3]: 'The registration fee for the Master program is "
    "Rp 750,000 per applicant.'\n"
    "Answer: The registration fee for UPI Master (S2) is Rp 750,000 per "
    "applicant [3]. This is the application/selection fee, not per-semester "
    "tuition.\n"
)


def system_prompt(language: str = "id") -> str:
    return SYSTEM_PROMPT_EN if language == "en" else SYSTEM_PROMPT_ID


def _is_low_content(text: str) -> bool:
    """True if a chunk is mostly digits / punctuation (e.g. corrupted table).

    These chunks hurt the LLM - they get high embedding similarity but contain
    no semantically extractable answer.
    """
    if not text or len(text) < 60:
        return True
    letters = sum(1 for c in text if c.isalpha())
    if letters / len(text) < 0.35:   # < 35% letters -> noisy table dump
        return True
    return False


def format_context(chunks: list[dict[str, Any]]) -> str:
    """Render retrieved chunks as numbered SUMBER blocks. Skip low-content chunks."""
    usable = [c for c in chunks if not _is_low_content(c.get("text", ""))]
    if not usable:
        return "(tidak ada konteks yang dapat dibaca / no readable context)"
    blocks: list[str] = []
    for i, c in enumerate(usable, start=1):
        ref = c.get("title", "Dokumen tanpa judul")
        page = c.get("page")
        if page is not None:
            ref += f", hal. {page}"
        section = c.get("section")
        if section:
            ref += f", bagian: {section}"
        blocks.append(f"[{i}] {ref}\n{c.get('text', '').strip()}")
    return "\n\n".join(blocks)


def format_examples(examples: list[dict[str, Any]] | None, language: str) -> str:
    """Render Q&A exemplars as a STYLE guide. Explicitly forbids copying facts."""
    if not examples:
        return ""
    if language == "en":
        head = ("=== ANSWER-STYLE EXAMPLES (tone and structure only — use facts "
                "from SOURCES, not from these examples) ===")
        q, a = "Q", "A"
    else:
        head = ("=== CONTOH GAYA MENJAWAB (untuk nada dan struktur saja — "
                "fakta tetap dari SUMBER, bukan dari contoh) ===")
        q, a = "T", "J"
    blocks = []
    for i, e in enumerate(examples, start=1):
        blocks.append(f"Contoh {i}:\n{q}: {e.get('question','').strip()}\n"
                      f"{a}: {e.get('answer','').strip()}")
    return head + "\n" + "\n\n".join(blocks) + "\n\n"


_REASONING_ID = (
    "LANGKAH BERPIKIR (internal saja, jangan ditampilkan): "
    "(1) pilih SUMBER yang relevan; (2) ambil poin-poin yang membantu menjawab; "
    "(3) susun jawaban yang jelas dan natural, dengan sitasi [n] untuk fakta "
    "spesifik. Bila informasi terbatas, jawab sejauh yang ada.\n\n"
)
_REASONING_EN = (
    "REASONING STEPS (internal only, do not show in the answer): "
    "(1) pick relevant SOURCES; (2) extract helpful points; (3) compose a clear, "
    "natural answer with [n] citations for specific facts. If information is "
    "limited, answer as far as the SOURCES allow.\n\n"
)


def build_prompt(
    query: str,
    chunks: list[dict[str, Any]],
    language: str = "id",
    examples: list[dict[str, Any]] | None = None,
    reasoning: bool = False,
) -> str:
    """Full grounded prompt: system rules + (reasoning) + (style examples) +
    numbered context + question. Examples guide STYLE only; facts come from SOURCES."""
    context = format_context(chunks)
    q_label = "PERTANYAAN" if language != "en" else "QUESTION"
    a_label = "JAWABAN" if language != "en" else "ANSWER"
    reasoning_block = ("" if not reasoning else
                       (_REASONING_EN if language == "en" else _REASONING_ID))
    examples_block = format_examples(examples, language)
    return (
        f"{system_prompt(language)}\n"
        f"{reasoning_block}"
        f"{examples_block}"
        f"=== SUMBER / SOURCES ===\n{context}\n\n"
        f"=== {q_label} ===\n{query}\n\n"
        f"=== {a_label} ===\n"
    )
