"""Auth, saved chat sessions, and usage-stats routes.

Token auth is a simple opaque bearer token (stored hashed server-side).
All /sessions routes require auth; /stats additionally requires admin.
Question statistics are aggregated from app/data/logs/chat.jsonl, which
logs every /chat call — including anonymous ones — so the numbers cover
all users, not only logged-in accounts.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    MessagesReplaceRequest,
    RegisterRequest,
    SessionCreateRequest,
    SessionDetail,
    SessionRenameRequest,
    SessionSummary,
    StatsResponse,
    UserInfo,
)
from app.services import auth_db

router = APIRouter()

_CHAT_LOG = Path("./app/data/logs/chat.jsonl")


def _bearer_token(request: Request) -> str:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Belum login.")
    return header[7:].strip()


def get_current_user(request: Request) -> dict[str, Any]:
    user = auth_db.user_for_token(_bearer_token(request))
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Sesi login kedaluwarsa. Silakan login ulang."
        )
    return user


def get_admin_user(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if not user["is_admin"]:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Hanya admin yang dapat mengakses statistik."
        )
    return user


# --- auth --------------------------------------------------------------------
@router.post("/auth/register", response_model=AuthResponse, tags=["auth"])
def register(body: RegisterRequest) -> AuthResponse:
    try:
        user = auth_db.create_user(body.username, body.password)
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None
    return AuthResponse(token=auth_db.issue_token(user["id"]), user=UserInfo(**user))


@router.post("/auth/login", response_model=AuthResponse, tags=["auth"])
def login(body: LoginRequest) -> AuthResponse:
    user = auth_db.verify_login(body.username, body.password)
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Username atau password salah."
        )
    return AuthResponse(token=auth_db.issue_token(user["id"]), user=UserInfo(**user))


@router.post("/auth/logout", tags=["auth"])
def logout(request: Request) -> Response:
    auth_db.revoke_token(_bearer_token(request))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/auth/me", response_model=UserInfo, tags=["auth"])
def me(user: dict[str, Any] = Depends(get_current_user)) -> UserInfo:
    return UserInfo(**user)


# --- saved chat sessions ------------------------------------------------------
@router.get("/sessions", response_model=list[SessionSummary], tags=["sessions"])
def sessions_list(user: dict[str, Any] = Depends(get_current_user)):
    return [SessionSummary(**s) for s in auth_db.list_sessions(user["id"])]


@router.post("/sessions", response_model=SessionSummary, tags=["sessions"])
def sessions_create(
    body: SessionCreateRequest, user: dict[str, Any] = Depends(get_current_user)
):
    try:
        row = auth_db.create_session(user["id"], body.id, body.title)
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None
    return SessionSummary(**row, message_count=0)


@router.get("/sessions/{session_id}", response_model=SessionDetail, tags=["sessions"])
def sessions_get(
    session_id: str, user: dict[str, Any] = Depends(get_current_user)
):
    row = auth_db.get_session(user["id"], session_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sesi tidak ditemukan.")
    return SessionDetail(**row)


@router.put("/sessions/{session_id}", tags=["sessions"])
def sessions_rename(
    session_id: str,
    body: SessionRenameRequest,
    user: dict[str, Any] = Depends(get_current_user),
):
    if not auth_db.rename_session(user["id"], session_id, body.title):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sesi tidak ditemukan.")
    return {"ok": True}


@router.delete("/sessions/{session_id}", tags=["sessions"])
def sessions_delete(
    session_id: str, user: dict[str, Any] = Depends(get_current_user)
) -> Response:
    if not auth_db.delete_session(user["id"], session_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sesi tidak ditemukan.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/sessions/{session_id}/messages", tags=["sessions"])
def sessions_replace_messages(
    session_id: str,
    body: MessagesReplaceRequest,
    user: dict[str, Any] = Depends(get_current_user),
):
    ok = auth_db.replace_messages(
        user["id"], session_id, [m.model_dump() for m in body.messages]
    )
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sesi tidak ditemukan.")
    return {"ok": True, "saved": len(body.messages)}


# --- stats (admin) -------------------------------------------------------------
@router.get("/stats", response_model=StatsResponse, tags=["stats"])
def stats(_admin: dict[str, Any] = Depends(get_admin_user)) -> StatsResponse:
    per_day: Counter[str] = Counter()
    questions: Counter[str] = Counter()
    total = 0
    if _CHAT_LOG.is_file():
        with _CHAT_LOG.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                query = str(rec.get("query", "")).strip()
                if not query:
                    continue
                total += 1
                per_day[str(rec.get("ts", ""))[:10]] += 1
                questions[query.lower()] += 1

    top = [
        {"question": q, "count": n}
        for q, n in questions.most_common(20)
    ]
    days = [
        {"date": d, "count": n} for d, n in sorted(per_day.items())
    ]
    return StatsResponse(
        total_questions=total,
        questions_per_day=days,
        top_questions=top,
        **auth_db.account_stats(),
    )
