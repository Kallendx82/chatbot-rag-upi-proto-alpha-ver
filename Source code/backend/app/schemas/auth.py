"""Pydantic schemas for auth, saved chat sessions, and usage stats."""
from __future__ import annotations

import re
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

_USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{3,32}$")


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def _valid_username(cls, v: str) -> str:
        if not _USERNAME_RE.match(v):
            raise ValueError(
                "Username 3-32 karakter: huruf, angka, titik, strip, underscore."
            )
        return v


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., max_length=255)


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserInfo


class SessionSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0


class SessionCreateRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    title: str = Field("Percakapan baru", max_length=200)


class SessionRenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class StoredMessage(BaseModel):
    role: str = Field(..., max_length=16)
    content: str = Field(..., max_length=100_000)
    extra: Optional[dict[str, Any]] = None
    created_at: Optional[str] = None


class MessagesReplaceRequest(BaseModel):
    messages: list[StoredMessage] = Field(..., max_length=500)


class SessionDetail(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[StoredMessage]


class DailyCount(BaseModel):
    date: str
    count: int


class TopQuestion(BaseModel):
    question: str
    count: int


class StatsResponse(BaseModel):
    total_questions: int
    questions_per_day: list[DailyCount]
    top_questions: list[TopQuestion]
    total_users: int
    total_sessions: int
    total_saved_questions: int
