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
    ChangePasswordRequest,
    DeleteAccountRequest,
    FeedbackSubmitRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessagesReplaceRequest,
    RegisterRequest,
    ResetPasswordRequest,
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


def get_optional_user(request: Request) -> dict[str, Any] | None:
    try:
        token = _bearer_token(request)
        return auth_db.user_for_token(token)
    except HTTPException:
        return None

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
    is_admin = False
    if body.admin_code == "UPI_ADMIN_2026" and (body.email.endswith("@upi.edu") or body.email.endswith("@student.upi.edu")):
        is_admin = True
        
    try:
        user = auth_db.create_user(body.username, body.password, body.email, is_admin=is_admin)
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


@router.post("/auth/change-password", tags=["auth"])
def change_password(
    body: ChangePasswordRequest,
    user: dict[str, Any] = Depends(get_current_user),
) -> Response:
    if not auth_db.change_password(user["id"], body.old_password, body.new_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Password lama tidak sesuai."
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/auth/delete-account", tags=["auth"])
def delete_account(
    body: DeleteAccountRequest,
    user: dict[str, Any] = Depends(get_current_user),
) -> Response:
    if not auth_db.delete_account(user["id"], body.password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Password yang Anda masukkan salah."
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/auth/forgot-password", tags=["auth"])
def forgot_password(body: ForgotPasswordRequest) -> dict[str, str]:
    """Password reset disabled for alpha testing."""
    raise HTTPException(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "Fitur lupa password masih dalam development. Hubungi admin jika lupa password.",
    )


@router.post("/auth/reset-password", tags=["auth"])
def reset_password(body: ResetPasswordRequest) -> Response:
    """Reset password disabled for alpha testing."""
    raise HTTPException(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "Fitur reset password masih dalam development.",
    )


@router.post("/auth/feedback", tags=["auth"])
def submit_feedback(
    body: FeedbackSubmitRequest,
    user: dict[str, Any] = Depends(get_current_user),
) -> Response:
    auth_db.submit_user_feedback(
        user["id"], body.satisfaction, body.ease_of_use, body.feedback_text
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


from datetime import datetime, timedelta, timezone

@router.get("/stats", response_model=StatsResponse, tags=["stats"])
def stats(_admin: dict[str, Any] = Depends(get_admin_user)) -> StatsResponse:
    per_day: Counter[str] = Counter()
    q_all: Counter[str] = Counter()
    q_day: Counter[str] = Counter()
    q_week: Counter[str] = Counter()
    q_month: Counter[str] = Counter()
    q_latencies_all: dict[str, list[dict[str, Any]]] = {}
    q_latencies_day: dict[str, list[dict[str, Any]]] = {}
    q_latencies_week: dict[str, list[dict[str, Any]]] = {}
    q_latencies_month: dict[str, list[dict[str, Any]]] = {}
    total = 0
    now = datetime.now(timezone.utc)

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
                
                ts_str = str(rec.get("ts", ""))
                if ts_str:
                    per_day[ts_str[:10]] += 1
                
                query_lower = query.lower()
                q_all[query_lower] += 1
                
                rec_latency = {
                    "ts": ts_str,
                    "total_ms": float(rec.get("total_ms", 0) or 0),
                    "retrieval_ms": float(rec.get("retrieval_ms", 0) or 0),
                    "generation_ms": float(rec.get("generation_ms", 0) or 0),
                    "backend": str(rec.get("backend", "ollama")),
                }
                if query_lower not in q_latencies_all:
                    q_latencies_all[query_lower] = []
                q_latencies_all[query_lower].append(rec_latency)

                if ts_str:
                    try:
                        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        delta = now - dt
                        if delta <= timedelta(days=1):
                            q_day[query_lower] += 1
                            if query_lower not in q_latencies_day:
                                q_latencies_day[query_lower] = []
                            q_latencies_day[query_lower].append(rec_latency)
                        if delta <= timedelta(days=7):
                            q_week[query_lower] += 1
                            if query_lower not in q_latencies_week:
                                q_latencies_week[query_lower] = []
                            q_latencies_week[query_lower].append(rec_latency)
                        if delta <= timedelta(days=30):
                            q_month[query_lower] += 1
                            if query_lower not in q_latencies_month:
                                q_latencies_month[query_lower] = []
                            q_latencies_month[query_lower].append(rec_latency)
                    except ValueError:
                        pass

    def _make_top(q_counter: Counter[str], latencies_dict: dict[str, list[dict[str, Any]]], limit: int | None = 20) -> list[dict[str, Any]]:
        res = []
        items = q_counter.most_common(limit) if limit is not None else q_counter.most_common()
        for q, n in items:
            # Sort descending by ts and take top 10
            recs = sorted(latencies_dict.get(q, []), key=lambda x: x["ts"], reverse=True)[:10]
            res.append({"question": q, "count": n, "latency_records": recs})
        return res

    top_all = _make_top(q_all, q_latencies_all, limit=None)
    top_day = _make_top(q_day, q_latencies_day, limit=100)
    top_week = _make_top(q_week, q_latencies_week, limit=200)
    top_month = _make_top(q_month, q_latencies_month, limit=500)
    days = [{"date": d, "count": n} for d, n in sorted(per_day.items())]

    users_list = auth_db.get_users_list_stats()

    return StatsResponse(
        total_questions=total,
        questions_per_day=days,
        top_questions=top_all,
        top_questions_day=top_day,
        top_questions_week=top_week,
        top_questions_month=top_month,
        users_list=users_list,
        **auth_db.account_stats(),
    )
