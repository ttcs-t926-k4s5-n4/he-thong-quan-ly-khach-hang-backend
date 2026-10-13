"""Đăng nhập và thông tin người dùng hiện tại."""
from flask import Blueprint, current_app, jsonify
from werkzeug.security import check_password_hash

from app.auth import create_token, current_user, load_user, login_required
from app.db import row
from app.errors import Unauthorized
from app.labels import ROLES
from app.validation import Str, json_body, validate

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

LOGIN_SCHEMA = {
    "username": Str("Tên đăng nhập", required=True, min_len=1, max_len=100),
    "password": Str("Mật khẩu", required=True, min_len=1, max_len=200, strip=False),
}


def user_out(user: dict) -> dict:
    return {
        "id": user["id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "email": user.get("email"),
        "role": user["role"],
        "role_label": ROLES.get(user["role"], user["role"]),
        "team": {"id": user["team_id"], "name": user.get("team_name")} if user.get("team_id") else None,
    }


@bp.post("/login")
def login():
    """Đăng nhập bằng tên đăng nhập và mật khẩu, nhận token truy cập."""
    data = validate(json_body(), LOGIN_SCHEMA)
    account = row("SELECT id, password_hash, is_active FROM users WHERE username = ?", (data["username"],))
    if not account or not check_password_hash(account["password_hash"], data["password"]):
        raise Unauthorized("Tên đăng nhập hoặc mật khẩu không đúng.")
    if not account["is_active"]:
        raise Unauthorized("Tài khoản đã bị khoá, vui lòng liên hệ quản trị hệ thống.")
    profile = load_user(account["id"])
    return jsonify({
        "message": f"Đăng nhập thành công. Xin chào {profile['full_name']}!",
        "access_token": create_token(profile["id"]),
        "token_type": "Bearer",
        "expires_in": current_app.config["TOKEN_MAX_AGE_SECONDS"],
        "user": user_out(profile),
    })


@bp.get("/me")
@login_required
def me():
    """Thông tin tài khoản đang đăng nhập."""
    return jsonify(user_out(current_user()))
