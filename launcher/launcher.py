"""
UPI Chatbot Launcher

Starts the backend (FastAPI/Uvicorn) and frontend (Next.js) servers, waits
for them to become ready, then opens the app in the default browser.

Designed to run as a standalone .exe (built with PyInstaller) sitting next
to the project's `backend/` and `frontend/` folders, or from a configured
PROJECT_ROOT path baked in at build time.
"""
from __future__ import annotations

import os
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
    for the project two levels up (launcher/ -> project root), then fall
    back to searching alongside the exe itself so the launcher also works
    when copied directly into the project root.
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
    else:
        exe_dir = Path(__file__).resolve().parent

    candidates = [exe_dir, exe_dir.parent, exe_dir.parent.parent]
    for cand in candidates:
        if (cand / "backend").is_dir() and (cand / "frontend").is_dir():
            return cand

    # Last resort: env var override
    env_root = os.environ.get("UPI_CHATBOT_ROOT")
    if env_root:
        return Path(env_root)

    raise FileNotFoundError(
        "Tidak dapat menemukan folder 'backend' dan 'frontend'. "
        "Pastikan launcher.exe berada di dalam folder project atau set "
        "environment variable UPI_CHATBOT_ROOT."
    )


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


def start_backend(root: Path) -> subprocess.Popen:
    backend_dir = root / "backend"
    python_exe = sys.executable if not getattr(sys, "frozen", False) else "python"
    # Prefer a venv python if present
    venv_python = backend_dir / ".venv" / "Scripts" / "python.exe"
    if venv_python.is_file():
        python_exe = str(venv_python)

    print(f"[*] Starting backend from {backend_dir} ...")
    return subprocess.Popen(
        [python_exe, "-m", "uvicorn", "app.main:app", "--port", "8000"],
        cwd=str(backend_dir),
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
    )


def start_frontend(root: Path) -> subprocess.Popen:
    frontend_dir = root / "frontend"
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"

    print(f"[*] Starting frontend from {frontend_dir} ...")
    return subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=str(frontend_dir),
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
    )


def main() -> int:
    print(f"=== {APP_NAME} Launcher ===")
    try:
        root = resolve_project_root()
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        input("Tekan Enter untuk keluar...")
        return 1

    print(f"[*] Project root: {root}")

    backend_proc = start_backend(root)
    frontend_proc = start_frontend(root)

    print("[*] Menunggu backend siap...")
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
