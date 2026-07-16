"""
Add New PDF - Ingestion Tool Launcher

Interactive wrapper around backend/scripts/ingestion/run_pipeline.py so a
non-technical user can add PDFs to the chatbot's knowledge base without
typing any command-line flags: double-click, answer two prompts, done.

Deliberately does NOT bundle torch/faiss/sentence-transformers into the exe
itself (that combination is exactly what caused native crashes when package
versions drifted - see backend/.venv). Instead this exe just prompts for
input and shells out to the project's own isolated backend/.venv Python,
so it always runs with the exact same, tested dependency versions the
backend uses.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

APP_NAME = "UPI Chatbot - Add New PDF"


def resolve_project_root() -> Path:
    """Find the project root (folder containing backend/scripts/ingestion)."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
    else:
        exe_dir = Path(__file__).resolve().parent

    for cand in (exe_dir, exe_dir.parent, exe_dir.parent.parent):
        if (cand / "backend" / "scripts" / "ingestion" / "run_pipeline.py").is_file():
            return cand

    raise FileNotFoundError(
        "Tidak dapat menemukan 'backend/scripts/ingestion/run_pipeline.py'. "
        "Pastikan Add-New-PDF.exe berada di dalam folder project."
    )


def resolve_venv_python(root: Path) -> Path | None:
    candidate = root / "backend" / ".venv" / "Scripts" / "python.exe"
    return candidate if candidate.is_file() else None


def ask(prompt: str, required: bool = True) -> str:
    while True:
        try:
            value = input(prompt).strip().strip('"')
        except EOFError:
            return ""
        if value or not required:
            return value
        print("  (wajib diisi)")


def pause(message: str = "\nTekan Enter untuk keluar...") -> None:
    try:
        input(message)
    except EOFError:
        pass


def main() -> int:
    print(f"=== {APP_NAME} ===\n")
    print("Alat ini menambahkan PDF baru ke basis pengetahuan chatbot:")
    print("  extract -> clean -> chunk -> embed, lalu digabung ke index yang")
    print("  sedang dipakai backend.\n")

    try:
        root = resolve_project_root()
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        pause()
        return 1

    python_exe = resolve_venv_python(root)
    if python_exe is None:
        print("[ERROR] backend/.venv belum ada.")
        print("        Jalankan UPI-Chatbot-Launcher.exe setidaknya sekali dulu")
        print("        (itu yang membuat dan mengisi .venv secara otomatis),")
        print("        baru coba lagi alat ini.")
        pause()
        return 1

    pdf_dir = ask("Folder berisi PDF baru (bisa drag & drop foldernya ke sini): ")
    pdf_path = Path(pdf_dir)
    if not pdf_path.is_dir():
        print(f"[ERROR] Folder tidak ditemukan: {pdf_path}")
        pause()
        return 1

    category = ask("Nama kategori untuk dokumen ini (contoh: BiroSDM, FIP, Perpustakaan): ")

    print(f"\n[*] Project root : {root}")
    print(f"[*] PDF folder   : {pdf_path}")
    print(f"[*] Kategori     : {category}")
    try:
        confirm = input("\nLanjutkan? (y/n): ").strip().lower()
    except EOFError:
        confirm = "n"
    if confirm not in ("y", "yes", "ya"):
        print("[*] Dibatalkan.")
        pause()
        return 0

    print()
    pipeline_script = root / "backend" / "scripts" / "ingestion" / "run_pipeline.py"
    result = subprocess.run(
        [str(python_exe), str(pipeline_script), "--pdf-dir", str(pdf_path), "--category", category],
        cwd=str(root / "backend"),
    )

    if result.returncode == 0:
        print("\n[OK] Selesai. Restart backend (tutup lalu buka lagi")
        print("     UPI-Chatbot-Launcher.exe) agar dokumen baru bisa dicari.")
    else:
        print("\n[ERROR] Proses berhenti dengan error - lihat pesan di atas.")

    pause()
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
