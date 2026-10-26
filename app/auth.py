"""Đăng nhập bằng token (ký bằng SECRET_KEY) và lấy người dùng hiện tại."""
from __future__ import annotations

import hashlib
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.db import row
from app.errors import Unauthorized


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


def is_token_revoked(raw_token: str) -> bool:
    r = row("SELECT token_hash FROM revoked_tokens WHERE token_hash = ?", (hash_token(raw_token),))
    return r is not None


def revoke_token(raw_token: str) -> None:
    from app import clock
    from app.db import commit, execute
    execute(
        "INSERT OR REPLACE INTO revoked_tokens (token_hash, revoked_at) VALUES (?, ?)",
        (hash_token(raw_token), clock.to_db(clock.now())),
    )
    commit()


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="crm-dang-nhap")


def create_token(user_id: int) -> str:
    return _serializer().dumps({"uid": user_id})


def load_user(user_id) -> dict | None:
    return row(
        "SELECT u.id, u.username, u.full_name, u.email, u.role, u.team_id, u.is_active, "
        "t.name AS team_name FROM users u LEFT JOIN teams t ON t.id = u.team_id WHERE u.id = ?",
        (user_id,),
    )


def login_required(view):
    """Bắt buộc gửi header: Authorization: Bearer <token>."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.lower().startswith("bearer ") or not header[7:].strip():
            raise Unauthorized("Bạn chưa đăng nhập. Vui lòng gửi header Authorization: Bearer <token>.")
        raw_token = header[7:].strip()
        if is_token_revoked(raw_token):
            raise Unauthorized("Phiên đăng nhập đã bị thu hồi hoặc đã đăng xuất, vui lòng đăng nhập lại.")
        try:
            payload = _serializer().loads(raw_token,
                                          max_age=current_app.config["TOKEN_MAX_AGE_SECONDS"])
        except SignatureExpired:
            raise Unauthorized("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.") from None
        except BadSignature:
            raise Unauthorized("Token đăng nhập không hợp lệ.") from None
        user = load_user(payload.get("uid")) if isinstance(payload, dict) else None
        if not user or not user["is_active"]:
            raise Unauthorized("Tài khoản không tồn tại hoặc đã bị khoá.")
        g.user = user
        return view(*args, **kwargs)

    return wrapper


def current_user() -> dict:
    return g.user
