from typing import Any

from flask import Blueprint, Flask, jsonify, request, session
from werkzeug.security import check_password_hash

from app.account import ChangePasswordResult, change_password, new_password_error
from app.auth import get_current_user, load_current_user, login_user, logout_current_user
from app.db import fetch_one, get_db

api = Blueprint("api", __name__, url_prefix="/api")
INVALID_LOGIN_MESSAGE = "Email hoặc mật khẩu không đúng."


def _json_body() -> dict[str, Any]:
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else {}


@api.get("/health")
def health():
    return jsonify({"status": "ok", "service": "s1-04-change-password-backend"})


@api.post("/auth/login")
def login():
    body = _json_body()
    email = str(body.get("email", "")).strip().lower()
    password = str(body.get("password", ""))

    if not email or not password:
        return jsonify({"message": INVALID_LOGIN_MESSAGE}), 400

    user = fetch_one(
        get_db(),
        """
        SELECT id, email, password_hash
        FROM dbo.users
        WHERE LOWER(email) = LOWER(?)
        """,
        (email,),
    )

    if user is None or not check_password_hash(str(user["password_hash"]), password):
        return jsonify({"message": INVALID_LOGIN_MESSAGE}), 400

    if not login_user(int(user["id"])):
        return jsonify({"message": "Không thể tạo phiên đăng nhập."}), 500

    return jsonify(
        {
            "message": "Đăng nhập thành công.",
            "user": {"id": int(user["id"]), "email": str(user["email"])},
        }
    )


@api.get("/auth/me")
def me():
    user = get_current_user()
    if user is None:
        return jsonify({"message": "Chưa đăng nhập."}), 401

    return jsonify(
        {
            "user": {
                "id": user.id,
                "email": user.email,
                "credentials_version": user.credentials_version,
            }
        }
    )


@api.post("/auth/logout")
def logout():
    user = get_current_user()
    if user is not None:
        logout_current_user()
    return jsonify({"message": "Đã đăng xuất."})


@api.post("/account/change-password")
def submit_change_password():
    user = get_current_user()
    if user is None:
        return jsonify({"message": "Phiên đăng nhập đã hết hạn hoặc chưa đăng nhập."}), 401

    body = _json_body()
    current_password = str(body.get("current_password", ""))
    new_password = str(body.get("new_password", ""))
    confirmation = str(body.get("new_password_confirmation", ""))

    errors: dict[str, str] = {}

    if not current_password:
        errors["current_password"] = "Vui lòng nhập mật khẩu hiện tại."

    password_error = new_password_error(new_password)
    if password_error:
        errors["new_password"] = password_error

    if not confirmation:
        errors["new_password_confirmation"] = "Vui lòng xác nhận mật khẩu mới."
    elif new_password != confirmation:
        errors["new_password_confirmation"] = "Mật khẩu xác nhận không khớp."

    if errors:
        return jsonify({"message": "Dữ liệu không hợp lệ.", "errors": errors}), 400

    raw_session_token = session.get("auth_token", "")
    result = change_password(
        user.id,
        str(raw_session_token),
        current_password,
        new_password,
    )

    if result is ChangePasswordResult.WRONG_CURRENT_PASSWORD:
        return (
            jsonify(
                {
                    "message": "Mật khẩu hiện tại không đúng.",
                    "errors": {"current_password": "Mật khẩu hiện tại không đúng."},
                }
            ),
            400,
        )

    if result is ChangePasswordResult.INVALID_NEW_PASSWORD:
        return (
            jsonify(
                {
                    "message": "Mật khẩu mới không đáp ứng yêu cầu bảo mật.",
                    "errors": {
                        "new_password": "Mật khẩu mới không đáp ứng yêu cầu bảo mật."
                    },
                }
            ),
            400,
        )

    if result is ChangePasswordResult.SESSION_EXPIRED:
        logout_current_user()
        return jsonify({"message": "Phiên đăng nhập đã kết thúc. Vui lòng đăng nhập lại."}), 401

    return jsonify(
        {
            "message": "Mật khẩu đã được cập nhật.",
            "other_sessions_revoked": True,
        }
    )


def register_routes(app: Flask) -> None:
    app.before_request(load_current_user)
    app.register_blueprint(api)
