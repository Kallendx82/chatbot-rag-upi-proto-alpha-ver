"""User accounts + per-account chat session storage (SQLite).

Deliberately dependency-free: sqlite3 + hashlib.scrypt from the standard
library. The DB lives next to the other runtime artefacts in app/data/.

Security model (appropriate for a thesis prototype, still done properly):
- Passwords are hashed with scrypt (n=2^14, r=8, p=1) and a per-user salt.
- API tokens are opaque random strings; only their SHA-256 lands in the DB,
  so a leaked DB file cannot be replayed as a bearer token.
- The first registered account becomes admin (can read /api/stats).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

_DB_PATH = Path("./app/data/users.db")
_TOKEN_TTL_DAYS = 30

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA foreign_keys=ON")
        _conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                pw_salt BLOB NOT NULL,
                pw_hash BLOB NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS auth_tokens (
                token_sha256 TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL DEFAULT 'Percakapan baru',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_user
                ON chat_sessions(user_id, updated_at DESC);
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL
                    REFERENCES chat_sessions(id) ON DELETE CASCADE,
                position INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                extra TEXT,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_messages_session
                ON chat_messages(session_id, position);
            """
        )
        logger.info("Auth DB ready at %s", _DB_PATH)
    return _conn


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=64
    )


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _user_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "username": row["username"],
        "is_admin": bool(row["is_admin"]),
        "created_at": row["created_at"],
    }


# --- users / tokens ---------------------------------------------------------
def create_user(username: str, password: str) -> dict[str, Any]:
    """Create a user; the very first account becomes admin. Raises ValueError."""
    with _lock:
        db = _db()
        salt = secrets.token_bytes(16)
        is_first = db.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"] == 0
        try:
            cur = db.execute(
                "INSERT INTO users (username, pw_salt, pw_hash, is_admin, created_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (username, salt, _hash_password(password, salt),
                 1 if is_first else 0, _now()),
            )
            db.commit()
        except sqlite3.IntegrityError:
            raise ValueError("Username sudah terdaftar.") from None
        row = db.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _user_row_to_dict(row)


def verify_login(username: str, password: str) -> dict[str, Any] | None:
    with _lock:
        row = _db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    if row is None:
        # Burn comparable time so missing users are not detectable via timing.
        _hash_password(password, b"0" * 16)
        return None
    if not hmac.compare_digest(_hash_password(password, row["pw_salt"]), row["pw_hash"]):
        return None
    return _user_row_to_dict(row)


def issue_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = (datetime.now(timezone.utc) + timedelta(days=_TOKEN_TTL_DAYS)).isoformat()
    with _lock:
        db = _db()
        db.execute(
            "INSERT INTO auth_tokens (token_sha256, user_id, expires_at, created_at)"
            " VALUES (?, ?, ?, ?)",
            (_token_digest(token), user_id, expires, _now()),
        )
        db.execute("DELETE FROM auth_tokens WHERE expires_at < ?", (_now(),))
        db.commit()
    return token


def revoke_token(token: str) -> None:
    with _lock:
        db = _db()
        db.execute("DELETE FROM auth_tokens WHERE token_sha256 = ?",
                   (_token_digest(token),))
        db.commit()


def user_for_token(token: str) -> dict[str, Any] | None:
    with _lock:
        row = _db().execute(
            "SELECT u.* FROM auth_tokens t JOIN users u ON u.id = t.user_id"
            " WHERE t.token_sha256 = ? AND t.expires_at >= ?",
            (_token_digest(token), _now()),
        ).fetchone()
    return _user_row_to_dict(row) if row else None


# --- chat sessions ----------------------------------------------------------
def list_sessions(user_id: int) -> list[dict[str, Any]]:
    with _lock:
        rows = _db().execute(
            "SELECT s.*, COUNT(m.id) AS message_count"
            " FROM chat_sessions s LEFT JOIN chat_messages m ON m.session_id = s.id"
            " WHERE s.user_id = ? GROUP BY s.id ORDER BY s.updated_at DESC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def create_session(user_id: int, session_id: str, title: str) -> dict[str, Any]:
    now = _now()
    with _lock:
        db = _db()
        db.execute(
            "INSERT OR IGNORE INTO chat_sessions (id, user_id, title, created_at,"
            " updated_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, user_id, title, now, now),
        )
        db.commit()
        row = db.execute(
            "SELECT * FROM chat_sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        ).fetchone()
    if row is None:
        raise ValueError("ID sesi sudah dipakai akun lain.")
    return dict(row)


def _owned_session(db: sqlite3.Connection, user_id: int, session_id: str):
    return db.execute(
        "SELECT * FROM chat_sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id),
    ).fetchone()


def get_session(user_id: int, session_id: str) -> dict[str, Any] | None:
    with _lock:
        db = _db()
        row = _owned_session(db, user_id, session_id)
        if row is None:
            return None
        msgs = db.execute(
            "SELECT role, content, extra, created_at FROM chat_messages"
            " WHERE session_id = ? ORDER BY position",
            (session_id,),
        ).fetchall()
    out = dict(row)
    out["messages"] = [
        {
            "role": m["role"],
            "content": m["content"],
            "extra": json.loads(m["extra"]) if m["extra"] else None,
            "created_at": m["created_at"],
        }
        for m in msgs
    ]
    return out


def rename_session(user_id: int, session_id: str, title: str) -> bool:
    with _lock:
        db = _db()
        cur = db.execute(
            "UPDATE chat_sessions SET title = ?, updated_at = ?"
            " WHERE id = ? AND user_id = ?",
            (title, _now(), session_id, user_id),
        )
        db.commit()
    return cur.rowcount > 0


def delete_session(user_id: int, session_id: str) -> bool:
    with _lock:
        db = _db()
        cur = db.execute(
            "DELETE FROM chat_sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        )
        db.commit()
    return cur.rowcount > 0


def replace_messages(
    user_id: int, session_id: str, messages: list[dict[str, Any]]
) -> bool:
    """Full-replace sync: the frontend pushes the whole message list after a
    turn completes. Simpler and more robust than incremental diffs for a chat
    of this size, and idempotent by construction."""
    now = _now()
    with _lock:
        db = _db()
        if _owned_session(db, user_id, session_id) is None:
            return False
        db.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
        db.executemany(
            "INSERT INTO chat_messages (session_id, position, role, content,"
            " extra, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    session_id,
                    i,
                    str(m.get("role", "user"))[:16],
                    str(m.get("content", "")),
                    json.dumps(m.get("extra"), ensure_ascii=False)
                    if m.get("extra") is not None
                    else None,
                    str(m.get("created_at") or now),
                )
                for i, m in enumerate(messages)
            ],
        )
        db.execute(
            "UPDATE chat_sessions SET updated_at = ? WHERE id = ?", (now, session_id)
        )
        db.commit()
    return True


# --- stats ------------------------------------------------------------------
def account_stats() -> dict[str, int]:
    with _lock:
        db = _db()
        users = db.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
        sessions = db.execute("SELECT COUNT(*) AS n FROM chat_sessions").fetchone()["n"]
        messages = db.execute(
            "SELECT COUNT(*) AS n FROM chat_messages WHERE role = 'user'"
        ).fetchone()["n"]
    return {"total_users": users, "total_sessions": sessions,
            "total_saved_questions": messages}
