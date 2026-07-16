"""
UPI Chatbot Launcher

Starts the backend (FastAPI/Uvicorn) and frontend (Next.js) servers, waits
for them to become ready, then opens the app in the default browser.

On first run it also checks for missing Python/Node dependencies and
installs them automatically, so a fresh checkout only needs Python + Node.js
installed on PATH - no manual `pip install` / `npm install` step required.

Designed to run as a standalone .exe (built with PyInstaller) sitting in the
project root, next to `backend/` and `frontend/`.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.request import urlopen

APP_NAME = "UPI Chatbot"
BACKEND_URL = "http://127.0.0.1:8000/health"
FRONTEND_URL = "http://localhost:3000"
STARTUP_TIMEOUT = 120  # seconds to wait for backend readiness


def resolve_project_root() -> Path:
    """Find the project root (folder containing backend/ and frontend/).

    When frozen by PyInstaller, sys.executable points at the .exe; we look
    at the exe's own folder and its parents so the launcher works whether
    it sits at the project root or one level down (e.g. launcher/).
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
    else:
        exe_dir = Path(__file__).resolve().parent

    candidates = [exe_dir, exe_dir.parent, exe_dir.parent.parent]
    for cand in candidates:
        if (cand / "backend").is_dir() and (cand / "frontend").is_dir():
            return cand

    env_root = os.environ.get("UPI_CHATBOT_ROOT")
    if env_root:
        return Path(env_root)

    raise FileNotFoundError(
        "Tidak dapat menemukan folder 'backend' dan 'frontend'. "
        "Pastikan UPI-Chatbot-Launcher.exe berada di dalam folder project."
    )


def find_system_python() -> str | None:
    """Locate a real Python interpreter on PATH (not this frozen exe).

    PyInstaller's bundled interpreter has no pip/site-packages of its own,
    so `python -m venv` must go through whatever Python the user has
    installed on the machine.
    """
    for candidate in ("python", "python3", "py"):
        path = shutil.which(candidate)
        if path:
            return path
    return None


def ensure_backend_venv(root: Path, system_python: str) -> str | None:
    """Return the path to an isolated backend/.venv Python, creating it if needed.

    The backend MUST run from its own venv, not the system-wide Python: this
    machine's global site-packages drift out of sync with this project's
    pinned numpy/torch/faiss/sentence-transformers versions whenever an
    unrelated project on the same machine upgrades them, and that mismatch
    causes a native segfault a few seconds into backend startup (while
    loading the embedding model / FAISS index) - it looks like the backend
    window "just closes itself" with no Python traceback, because it's an
    OS-level access violation, not a catchable exception.
    """
    backend_dir = root / "backend"
    venv_python = backend_dir / ".venv" / "Scripts" / "python.exe"

    if venv_python.is_file():
        return str(venv_python)

    print("[*] backend/.venv belum ada - membuat virtual environment terisolasi...")
    result = subprocess.run([system_python, "-m", "venv", str(backend_dir / ".venv")])
    if result.returncode != 0 or not venv_python.is_file():
        print("[ERROR] Gagal membuat backend/.venv.")
        return None
    print("[OK] backend/.venv dibuat.")
    return str(venv_python)


def ensure_backend_deps(root: Path, python_exe: str) -> bool:
    backend_dir = root / "backend"
    check = subprocess.run(
        [python_exe, "-c", "import fastapi, uvicorn"],
        cwd=str(backend_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if check.returncode == 0:
        print("[OK] Backend dependencies sudah terpasang.")
        return True

    req = backend_dir / "requirements.txt"
    if not req.is_file():
        print(f"[ERROR] {req} tidak ditemukan.")
        return False

    print("[*] Menginstall backend dependencies (pip install) ke backend/.venv... "
          "ini bisa memakan beberapa menit.")
    result = subprocess.run(
        [python_exe, "-m", "pip", "install", "-r", str(req)],
        cwd=str(backend_dir),
    )
    if result.returncode != 0:
        print("[ERROR] Gagal menginstall backend dependencies.")
        return False
    print("[OK] Backend dependencies terpasang.")
    return True


def ensure_frontend_deps(root: Path) -> bool:
    frontend_dir = root / "frontend"
    node_modules = frontend_dir / "node_modules"
    if node_modules.is_dir():
        print("[OK] Frontend dependencies sudah terpasang.")
        return True

    npm_cmd = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm_cmd:
        print("[ERROR] npm tidak ditemukan di PATH. Install Node.js terlebih dahulu (nodejs.org).")
        return False

    print("[*] Menginstall frontend dependencies (npm install)... ini bisa memakan beberapa menit.")
    result = subprocess.run([npm_cmd, "install"], cwd=str(frontend_dir))
    if result.returncode != 0:
        print("[ERROR] Gagal menginstall frontend dependencies.")
        return False
    print("[OK] Frontend dependencies terpasang.")
    return True


def wait_for_backend(timeout: int = STARTUP_TIMEOUT) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(BACKEND_URL, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(1.5)
    return False


def start_backend(root: Path, python_exe: str) -> subprocess.Popen:
    backend_dir = root / "backend"
    print(f"[*] Starting backend from {backend_dir} ...")
    return subprocess.Popen(
        [python_exe, "-m", "uvicorn", "app.main:app", "--port", "8000"],
        cwd=str(backend_dir),
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
    )


def start_frontend(root: Path) -> subprocess.Popen:
    frontend_dir = root / "frontend"
    npm_cmd = shutil.which("npm.cmd") or shutil.which("npm") or "npm"

    print(f"[*] Starting frontend from {frontend_dir} ...")
    return subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=str(frontend_dir),
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
    )


def main() -> int:
    print(f"=== {APP_NAME} Launcher ===\n")
    try:
        root = resolve_project_root()
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        input("Tekan Enter untuk keluar...")
        return 1

    print(f"[*] Project root: {root}")

    system_python = find_system_python()
    if not system_python:
        print("[ERROR] Python tidak ditemukan di PATH. Install Python 3.10+ terlebih dahulu (python.org).")
        input("Tekan Enter untuk keluar...")
        return 1

    backend_python = ensure_backend_venv(root, system_python)
    if not backend_python:
        input("Tekan Enter untuk keluar...")
        return 1

    if not ensure_backend_deps(root, backend_python):
        input("Tekan Enter untuk keluar...")
        return 1

    if not ensure_frontend_deps(root):
        input("Tekan Enter untuk keluar...")
        return 1

    backend_proc = start_backend(root, backend_python)
    frontend_proc = start_frontend(root)

    print("\n[*] Menunggu backend siap (model + index bisa memakan waktu ~1 menit pertama kali)...")
    if not wait_for_backend():
        print("[WARN] Backend belum merespons setelah timeout, membuka browser tetap dilanjutkan.")
    else:
        print("[OK] Backend siap.")

    # Frontend (Next.js dev) usually takes a few seconds after backend
    time.sleep(5)

    print(f"[*] Membuka {FRONTEND_URL} di browser...")
    webbrowser.open(FRONTEND_URL)

    print("\n[OK] UPI Chatbot berjalan.")
    print("     Jangan tutup jendela terminal backend/frontend yang muncul.")
    print("     Tutup jendela ini untuk menghentikan launcher (server tetap berjalan).")
    input("\nTekan Enter untuk keluar dari launcher ini...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
