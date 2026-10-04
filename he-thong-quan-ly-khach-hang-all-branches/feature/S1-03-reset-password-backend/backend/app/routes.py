from flask import Blueprint, Flask, current_app, jsonify, request

from app.password_reset import (
    GENERIC_RESET_MESSAGE,
    INVALID_LINK_MESSAGE,
    ResetPasswordResult,
    inspect_reset_token,
    is_valid_email,
    password_rule_error,
    request_password_reset,
    reset_password,
)

api = Blueprint("api", __name__, url_prefix="/api")


def _json_body() -> dict:
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else {}


@api.get("/health")
def health():
    return jsonify({"status": "ok", "service": "s1-03-reset-password-backend"})


@api.post("/auth/forgot-password")
def forgot_password():
    body = _json_body()
    email = str(body.get("email", "")).strip()

    if not email:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "validation_failed",
                    "message": "Thông tin chưa hợp lệ.",
                    "errors": {"email": "Vui lòng nhập email."},
                }
            ),
            400,
        )

    if not is_valid_email(email):
        return (
            jsonify(
                {
                    "success": False,
                    "error": "validation_failed",
                    "message": "Thông tin chưa hợp lệ.",
                    "errors": {
                        "email": "Vui lòng nhập một địa chỉ email hợp lệ."
                    },
                }
            ),
            400,
        )

    # Với email hợp lệ, email tồn tại hay không đều trả cùng thông báo.
    message = request_password_reset(email)
    return jsonify({"success": True, "message": message or GENERIC_RESET_MESSAGE})


@api.get("/auth/reset-password/<token>")
def inspect_token(token: str):
    if not inspect_reset_token(token):
        return (
            jsonify(
                {
                    "success": False,
                    "error": "invalid_link",
                    "message": INVALID_LINK_MESSAGE,
                }
            ),
            400,
        )

    return jsonify({"success": True, "valid": True})


@api.post("/auth/reset-password/<token>")
def submit_new_password(token: str):
    body = _json_body()
    password = str(body.get("password", ""))
    confirmation = str(body.get("password_confirmation", ""))

    errors: dict[str, str] = {}

    rule_error = password_rule_error(password)
    if rule_error:
        errors["password"] = rule_error

    if not confirmation:
        errors["password_confirmation"] = "Vui lòng xác nhận mật khẩu mới."
    elif password != confirmation:
        errors["password_confirmation"] = "Mật khẩu xác nhận không khớp."

    if errors:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "validation_failed",
                    "message": "Thông tin chưa hợp lệ.",
                    "errors": errors,
                }
            ),
            400,
        )

    result = reset_password(token, password)

    if result is ResetPasswordResult.INVALID_LINK:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "invalid_link",
                    "message": INVALID_LINK_MESSAGE,
                }
            ),
            400,
        )

    return jsonify(
        {
            "success": True,
            "message": "Đặt lại mật khẩu thành công.",
        }
    )


@api.get("/auth/demo-user")
def demo_user():
    if not current_app.config["DEMO_USER_ENABLED"]:
        return jsonify({"message": "Chế độ demo đã tắt."}), 404

    return jsonify({"email": current_app.config["DEMO_USER_EMAIL"]})


def register_routes(app: Flask) -> None:
    app.register_blueprint(api)
