"""Xác định người dùng hiện tại.

Bản demo dùng header `X-User-Id`. Khi ghép vào dự án thật, chỉ cần thay hàm
load_current_user() bằng cách đọc user từ JWT/session — phần phân quyền
dữ liệu không phải sửa gì.
"""
from functools import wraps

from flask import g, request

from . import messages
from .db import get_db
from .scope import Role, User


def load_current_user() -> User:
    raw = request.headers.get("X-User-Id", "").strip()
    if not raw.isdigit():
        raise messages.unauthenticated()
    row = get_db().execute(
        "SELECT id, username, full_name, role, team_id FROM users WHERE id = ?",
        (int(raw),),
    ).fetchone()
    if row is None:
        raise messages.unauthenticated()
    return User(id=row["id"], username=row["username"], full_name=row["full_name"],
                role=Role(row["role"]), team_id=row["team_id"])


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        g.user = load_current_user()
        return view(*args, **kwargs)
    return wrapped
