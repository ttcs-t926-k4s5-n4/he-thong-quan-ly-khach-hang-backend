"""Đăng nhập và thông tin người dùng hiện tại."""
from datetime import timedelta

from flask import Blueprint, current_app, jsonify, request
from werkzeug.security import check_password_hash

from app import clock
from app.auth import create_token, current_user, load_user, login_required, revoke_token
from app.db import commit, execute, row
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
    raw_account = row(
        "SELECT id, password_hash, is_active, failed_login_attempts, locked_until FROM users WHERE username = ?",
        (data["username"],)
    )
    if not raw_account:
        raise Unauthorized("Tên đăng nhập hoặc mật khẩu không đúng.")

    account = dict(raw_account)
    now_dt = clock.now()

    # Kiểm tra nếu tài khoản đang bị khóa tạm thời do nhập sai quá 5 lần
    if account["locked_until"]:
        locked_until_dt = clock.from_db(account["locked_until"])
        if locked_until_dt and locked_until_dt > now_dt:
            raise Unauthorized("Tài khoản tạm thời bị khóa trong 15 phút do nhập sai mật khẩu quá 5 lần liên tiếp.")
        elif locked_until_dt and locked_until_dt <= now_dt:
            # Hết thời gian 15 phút -> tự động mở khóa và reset bộ đếm
            execute("UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE id = ?", (account["id"],))
            commit()
            account["failed_login_attempts"] = 0
            account["locked_until"] = None

    if not check_password_hash(account["password_hash"], data["password"]):
        attempts = (account["failed_login_attempts"] or 0) + 1
        if attempts >= 5:
            new_locked = clock.to_db(now_dt + timedelta(minutes=15))
            execute("UPDATE users SET failed_login_attempts = ?, locked_until = ? WHERE id = ?",
                    (attempts, new_locked, account["id"]))
            commit()
        else:
            execute("UPDATE users SET failed_login_attempts = ? WHERE id = ?", (attempts, account["id"]))
            commit()
        raise Unauthorized("Tên đăng nhập hoặc mật khẩu không đúng.")

    if not account["is_active"]:
        raise Unauthorized("Tài khoản đã bị khoá, vui lòng liên hệ quản trị hệ thống.")

    # Đăng nhập thành công -> reset failed_login_attempts và locked_until nếu có
    if (account["failed_login_attempts"] or 0) > 0 or account["locked_until"]:
        execute("UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE id = ?", (account["id"],))
        commit()

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


@bp.post("/logout")
@login_required
def logout():
    """Đăng xuất và thu hồi phiên làm việc trên máy chủ."""
    header = request.headers.get("Authorization", "")
    token = header[7:].strip()
    revoke_token(token)
    return jsonify({
        "message": "Đăng xuất thành công. Phiên làm việc đã được thu hồi trên máy chủ."
    })

