from flask import Blueprint, Flask, jsonify, request

from app.users import (
    activate_account,
    create_user,
    list_users,
    update_user,
    valid_email,
)

api = Blueprint("api", __name__, url_prefix="/api")


def _json_body() -> dict:
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else {}


def _required_user_fields(body: dict) -> tuple[dict, dict]:
    values = {
        "full_name": str(body.get("full_name", "")).strip(),
        "email": str(body.get("email", "")).strip(),
        "group_name": str(body.get("group_name", "")).strip(),
        "role_name": str(body.get("role_name", "")).strip(),
    }

    errors = {}
    if not values["full_name"]:
        errors["full_name"] = "Vui lòng nhập họ và tên."
    if not values["email"]:
        errors["email"] = "Vui lòng nhập email công ty."
    elif not valid_email(values["email"]):
        errors["email"] = "Email không hợp lệ."
    if not values["group_name"]:
        errors["group_name"] = "Vui lòng chọn nhóm."
    if not values["role_name"]:
        errors["role_name"] = "Vui lòng chọn vai trò."

    return values, errors


@api.get("/health")
def health():
    return jsonify({"status": "ok", "service": "s1-08-user-management-backend"})


@api.get("/users")
def users_index():
    search = request.args.get("q", "").strip()
    group_name = request.args.get("group", "").strip()
    role_name = request.args.get("role", "").strip()
    status = request.args.get("status", "").strip()

    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1

    try:
        per_page = int(request.args.get("per_page", "20"))
    except ValueError:
        per_page = 20

    per_page = min(max(per_page, 1), 100)

    return jsonify(
        list_users(
            search,
            group_name,
            role_name,
            status,
            page,
            per_page,
        )
    )


@api.post("/users")
def users_create():
    body = _json_body()
    values, errors = _required_user_fields(body)

    if errors:
        return (
            jsonify(
                {
                    "message": "Thông tin tài khoản chưa hợp lệ.",
                    "errors": errors,
                }
            ),
            400,
        )

    try:
        user = create_user(**values)
    except ValueError as error:
        if str(error) == "duplicate_email":
            return (
                jsonify(
                    {
                        "message": "Email đã tồn tại. Vui lòng sử dụng email khác."
                    }
                ),
                409,
            )
        raise

    return (
        jsonify(
            {
                "message": (
                    "Tạo tài khoản thành công. Email kích hoạt kèm mật khẩu tạm "
                    "đã được gửi đến người dùng."
                ),
                "user": user,
            }
        ),
        201,
    )


@api.put("/users/<int:user_id>")
def users_update(user_id: int):
    body = _json_body()
    values, errors = _required_user_fields(body)

    if errors:
        return (
            jsonify(
                {
                    "message": "Thông tin tài khoản chưa hợp lệ.",
                    "errors": errors,
                }
            ),
            400,
        )

    try:
        update_user(user_id, **values)
    except ValueError as error:
        if str(error) == "duplicate_email":
            return (
                jsonify(
                    {
                        "message": "Email đã tồn tại. Vui lòng sử dụng email khác."
                    }
                ),
                409,
            )
        raise
    except LookupError:
        return jsonify({"message": "Không tìm thấy tài khoản."}), 404

    return jsonify({"message": "Đã cập nhật tài khoản."})


@api.post("/users/activate")
def users_activate():
    body = _json_body()
    token = str(body.get("token", "")).strip()

    if not token:
        return jsonify({"message": "Thiếu mã kích hoạt."}), 400

    if not activate_account(token):
        return (
            jsonify(
                {
                    "message": (
                        "Liên kết kích hoạt không hợp lệ, đã hết hạn "
                        "hoặc đã được sử dụng."
                    )
                }
            ),
            400,
        )

    return jsonify({"message": "Kích hoạt tài khoản thành công."})


def register_routes(app: Flask) -> None:
    app.register_blueprint(api)
