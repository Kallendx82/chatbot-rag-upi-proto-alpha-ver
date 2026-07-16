#!/usr/bin/env python3
"""Simple user management for users.db."""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(r"D:\Project\RAG_UPI\Source code\backend\app\data\users.db")

def list_users():
    """Show all users."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    rows = cursor.execute("SELECT id, username, email, is_admin, created_at FROM users").fetchall()
    conn.close()

    if not rows:
        print("[!] Tidak ada user")
        return

    print("\n" + "=" * 80)
    print("DAFTAR USER")
    print("=" * 80)
    for row in rows:
        badge = "[ADMIN]" if row["is_admin"] else "[USER]"
        print(f"{badge} ID:{row['id']:2d} | {row['username']:20s} | {row['email']}")
    print("=" * 80)

def delete_user(username, force=False):
    """Delete user by username."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Check if exists
    user = cursor.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        print(f"[ERROR] User '{username}' tidak ditemukan")
        conn.close()
        return False

    if not force:
        confirm = input(f"[?] Hapus user '{username}'? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("[*] Dibatalkan")
            conn.close()
            return False

    try:
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        print(f"[OK] User '{username}' dihapus dari database")
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        conn.close()
        return False

# Show usage
if len(sys.argv) < 2:
    print("""
Usage: python manage_users.py <command> [args]

Commands:
  list              - Tampilkan semua user
  delete <username> - Hapus user (dengan confirmation)
  delete <username> --force - Hapus user tanpa confirmation

Examples:
  python manage_users.py list
  python manage_users.py delete admin
  python manage_users.py delete admin --force
""")
    sys.exit(0)

cmd = sys.argv[1]

if cmd == "list":
    list_users()
elif cmd == "delete" and len(sys.argv) > 2:
    username = sys.argv[2]
    force = "--force" in sys.argv
    delete_user(username, force=force)
else:
    print("[ERROR] Command tidak valid")
    sys.exit(1)
