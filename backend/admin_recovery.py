"""Admin account recovery tool.

Run from the backend directory:
    python admin_recovery.py

Shows admin account info and allows password reset.
Only someone with access to the project files can run this.
"""
import getpass
import hashlib
import os
import secrets
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "app" / "data" / "users.db"


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=64
    )


def main() -> int:
    if not DB_PATH.exists():
        print(f"[ERROR] Database tidak ditemukan: {DB_PATH}")
        return 1

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    admins = conn.execute(
        "SELECT id, username, email, created_at FROM users WHERE is_admin = 1"
    ).fetchall()

    if not admins:
        print("[!] Tidak ada akun admin terdaftar.")
        conn.close()
        return 1

    print("\n=== ADMIN ACCOUNT RECOVERY ===\n")
    print("Akun admin yang terdaftar:\n")
    for a in admins:
        print(f"  ID       : {a['id']}")
        print(f"  Username : {a['username']}")
        print(f"  Email    : {a['email']}")
        print(f"  Dibuat   : {a['created_at']}")
        print()

    answer = input("Reset password admin? (y/n): ").strip().lower()
    if answer != "y":
        print("Dibatalkan.")
        conn.close()
        return 0

    if len(admins) > 1:
        target_id = input(f"Masukkan ID admin yang ingin direset: ").strip()
    else:
        target_id = str(admins[0]["id"])

    new_pw = getpass.getpass("Password baru: ")
    confirm = getpass.getpass("Konfirmasi password baru: ")

    if new_pw != confirm:
        print("[ERROR] Password tidak cocok.")
        conn.close()
        return 1

    if len(new_pw) < 6:
        print("[ERROR] Password minimal 6 karakter.")
        conn.close()
        return 1

    salt = secrets.token_bytes(32)
    hashed = _hash_password(new_pw, salt)

    conn.execute(
        "UPDATE users SET password_hash = ?, salt = ? WHERE id = ? AND is_admin = 1",
        (hashed, salt, int(target_id)),
    )
    conn.commit()

    updated = conn.execute(
        "SELECT username FROM users WHERE id = ?", (int(target_id),)
    ).fetchone()
    conn.close()

    if updated:
        print(f"\n[OK] Password untuk '{updated['username']}' berhasil direset.")
    else:
        print("[ERROR] ID admin tidak ditemukan.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
