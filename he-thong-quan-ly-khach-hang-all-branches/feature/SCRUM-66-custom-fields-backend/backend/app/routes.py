"""
routes.py — Tất cả API endpoints của Sprint 1
"""
from typing import Any

from flask import Blueprint, Flask, jsonify, request, send_file, session

from app.auth import (
    get_current_user,
    load_current_user,
    login,
    logout_current_user,
)
from app.custom_fields import (
    create_custom_field,
    delete_custom_field,
    get_custom_field,
    get_form_schema,
    list_custom_fields,
    update_custom_field,
)
from app.customers import (
    create_customer,
    delete_customer,
    get_customer,
    list_customers,
    update_customer,
)
from app.excel_export import export_customers_excel, export_opportunities_excel
from app.opportunities import (
    create_opportunity,
    delete_opportunity,
    get_opportunity,
    list_opportunities,
    update_opportunity,
)
from app.password import (
    ChangePasswordResult,
    ResetPasswordResult,
    change_password,
    inspect_reset_token,
    password_rule_error,
    request_password_reset,
    reset_password,
)
from app.roles import get_user_profile
from app.users import activate_account, create_user, list_users, update_user, valid_email

api = Blueprint("api", __name__, url_prefix="/api")



def _body() -> dict[str, Any]:
    b = request.get_json(silent=True)
    return b if isinstance(b, dict) else {}


def _require_auth():
    user = get_current_user()
    if user is None:
        return None, (jsonify({"message": "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.", "code": "session_expired"}), 401)
    return user, None


# ─── Health ──────────────────────────────────────────────────────────────────

@api.get("/health")
def health():
    return jsonify({"status": "ok", "service": "sprint1-backend", "version": "1.0.0"})


# ─── Auth (S1-01, S1-02, S1-10) ─────────────────────────────────────────────

@api.post("/auth/login")
def auth_login():
    body = _body()
    email = str(body.get("email", "")).strip()
    password = str(body.get("password", ""))
    if not email or not password:
        return jsonify({"message": "Email hoặc mật khẩu không đúng."}), 401
    status_code, payload = login(email, password)
    return jsonify(payload), status_code


@api.get("/auth/me")
def auth_me():
    user = get_current_user()
    if user is None:
        return jsonify({"message": "Chưa đăng nhập.", "code": "unauthenticated"}), 401
    return jsonify(get_user_profile(user))


@api.post("/auth/logout")
def auth_logout():
    logout_current_user()
    return jsonify({"message": "Đã đăng xuất an toàn."})


# ─── Reset password (S1-03) ──────────────────────────────────────────────────

@api.post("/auth/forgot-password")
def forgot_password():
    body = _body()
    email = str(body.get("email", "")).strip()
    if not email:
        return jsonify({"message": "Vui lòng nhập email."}), 400
    msg = request_password_reset(email)
    return jsonify({"message": msg})


@api.get("/auth/reset-password/<token>")
def check_reset_token(token: str):
    valid = inspect_reset_token(token)
    if not valid:
        return jsonify({"valid": False, "message": "Liên kết không hợp lệ hoặc đã hết hạn."}), 400
    return jsonify({"valid": True})


@api.post("/auth/reset-password/<token>")
def do_reset_password(token: str):
    body = _body()
    new_password = str(body.get("new_password", ""))
    confirm = str(body.get("new_password_confirmation", ""))

    errors: dict[str, str] = {}
    err = password_rule_error(new_password)
    if err:
        errors["new_password"] = err
    if not confirm:
        errors["new_password_confirmation"] = "Vui lòng xác nhận mật khẩu mới."
    elif new_password != confirm:
        errors["new_password_confirmation"] = "Mật khẩu xác nhận không khớp."
    if errors:
        return jsonify({"message": "Dữ liệu không hợp lệ.", "errors": errors}), 400

    result = reset_password(token, new_password)
    if result is ResetPasswordResult.INVALID_LINK:
        return jsonify({"message": "Liên kết không hợp lệ, đã hết hạn hoặc đã được sử dụng."}), 400
    return jsonify({"message": "Mật khẩu đã được đặt lại. Vui lòng đăng nhập với mật khẩu mới."})


# ─── Change password (S1-04) ─────────────────────────────────────────────────

@api.post("/account/change-password")
def change_pwd():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    body = _body()
    current_password = str(body.get("current_password", ""))
    new_password = str(body.get("new_password", ""))
    confirm = str(body.get("new_password_confirmation", ""))

    errors: dict[str, str] = {}
    if not current_password:
        errors["current_password"] = "Vui lòng nhập mật khẩu hiện tại."
    pw_err = password_rule_error(new_password)
    if pw_err:
        errors["new_password"] = pw_err
    if not confirm:
        errors["new_password_confirmation"] = "Vui lòng xác nhận mật khẩu mới."
    elif new_password != confirm:
        errors["new_password_confirmation"] = "Mật khẩu xác nhận không khớp."
    if errors:
        return jsonify({"message": "Dữ liệu không hợp lệ.", "errors": errors}), 400

    raw = session.get("auth_token", "")
    result = change_password(user.id, str(raw), current_password, new_password)

    if result is ChangePasswordResult.WRONG_CURRENT:
        return jsonify({"message": "Mật khẩu hiện tại không đúng.", "errors": {"current_password": "Mật khẩu hiện tại không đúng."}}), 400
    if result is ChangePasswordResult.INVALID_NEW:
        return jsonify({"message": "Mật khẩu mới không đáp ứng yêu cầu.", "errors": {"new_password": "Mật khẩu mới không đáp ứng yêu cầu."}}), 400
    if result is ChangePasswordResult.SESSION_EXPIRED:
        logout_current_user()
        return jsonify({"message": "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.", "code": "session_expired"}), 401

    return jsonify({"message": "Mật khẩu đã được cập nhật thành công.", "other_sessions_revoked": True})


# ─── User management (S1-05, S1-06, S1-08) ───────────────────────────────────

@api.get("/users")
def users_list():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role != "admin":
        return jsonify({"message": "Không có quyền truy cập."}), 403

    q = request.args.get("q", "").strip()
    group = request.args.get("group", "").strip()
    role = request.args.get("role", "").strip()
    status = request.args.get("status", "").strip()
    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1
    try:
        per_page = min(max(int(request.args.get("per_page", "20")), 1), 100)
    except ValueError:
        per_page = 20

    return jsonify(list_users(q, group, role, status, page, per_page))


@api.post("/users")
def users_create():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role != "admin":
        return jsonify({"message": "Không có quyền truy cập."}), 403

    body = _body()
    values = {
        "full_name": str(body.get("full_name", "")).strip(),
        "email": str(body.get("email", "")).strip(),
        "group_name": str(body.get("group_name", "")).strip(),
        "role_name": str(body.get("role_name", "")).strip(),
    }
    errors: dict[str, str] = {}
    if not values["full_name"]:
        errors["full_name"] = "Vui lòng nhập họ và tên."
    if not values["email"]:
        errors["email"] = "Vui lòng nhập email."
    elif not valid_email(values["email"]):
        errors["email"] = "Email không hợp lệ."
    if not values["group_name"]:
        errors["group_name"] = "Vui lòng chọn nhóm."
    if not values["role_name"]:
        errors["role_name"] = "Vui lòng chọn vai trò."
    if errors:
        return jsonify({"message": "Thông tin chưa hợp lệ.", "errors": errors}), 400

    try:
        result = create_user(**values)
    except ValueError as e:
        if str(e) == "duplicate_email":
            return jsonify({"message": "Email đã tồn tại. Vui lòng dùng email khác."}), 409
        raise
    return jsonify({"message": "Tạo tài khoản thành công. Email kích hoạt kèm mật khẩu tạm đã được gửi.", "user": result}), 201


@api.put("/users/<int:user_id>")
def users_update(user_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role != "admin":
        return jsonify({"message": "Không có quyền truy cập."}), 403

    body = _body()
    values = {
        "full_name": str(body.get("full_name", "")).strip(),
        "email": str(body.get("email", "")).strip(),
        "group_name": str(body.get("group_name", "")).strip(),
        "role_name": str(body.get("role_name", "")).strip(),
    }
    errors: dict[str, str] = {}
    if not values["full_name"]:
        errors["full_name"] = "Vui lòng nhập họ và tên."
    if not values["email"]:
        errors["email"] = "Vui lòng nhập email."
    elif not valid_email(values["email"]):
        errors["email"] = "Email không hợp lệ."
    if errors:
        return jsonify({"message": "Thông tin chưa hợp lệ.", "errors": errors}), 400

    try:
        update_user(user_id, **values)
    except ValueError as e:
        if str(e) == "duplicate_email":
            return jsonify({"message": "Email đã tồn tại."}), 409
        raise
    except LookupError:
        return jsonify({"message": "Không tìm thấy tài khoản."}), 404
    return jsonify({"message": "Đã cập nhật tài khoản."})


@api.post("/users/activate")
def users_activate():
    body = _body()
    token = str(body.get("token", "")).strip()
    if not token:
        return jsonify({"message": "Thiếu mã kích hoạt."}), 400
    ok = activate_account(token)
    if not ok:
        return jsonify({"message": "Liên kết kích hoạt không hợp lệ, đã hết hạn hoặc đã dùng."}), 400
    return jsonify({"message": "Kích hoạt tài khoản thành công! Vui lòng đăng nhập."})


# ─── Custom Fields Management (SCRUM-66) ─────────────────────────────────────

@api.get("/custom-fields")
def custom_fields_list():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    entity_type = request.args.get("entity_type", "").strip().lower()
    is_active_only = request.args.get("active_only", "false").lower() == "true"
    fields = list_custom_fields(entity_type=entity_type or None, is_active_only=is_active_only)
    return jsonify({"items": fields})


@api.get("/custom-fields/schema/<entity_type>")
def custom_fields_schema(entity_type: str):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if entity_type not in {"customer", "opportunity"}:
        return jsonify({"message": "Loại đối tượng không hợp lệ."}), 400
    schema = get_form_schema(entity_type)
    return jsonify({"entity_type": entity_type, "fields": schema})


@api.post("/custom-fields")
def custom_fields_create():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role != "admin":
        return jsonify({"message": "Chỉ Quản trị hệ thống mới có quyền khai báo trường tùy chỉnh."}), 403

    body = _body()
    try:
        field = create_custom_field(
            entity_type=str(body.get("entity_type", "")),
            field_key=str(body.get("field_key", "")),
            field_label=str(body.get("field_label", "")),
            field_type=str(body.get("field_type", "")),
            options=body.get("options"),
            is_required=bool(body.get("is_required", False)),
            description=str(body.get("description", "")),
            display_order=int(body.get("display_order", 0)),
            is_active=bool(body.get("is_active", True)),
        )
        return jsonify({"message": "Khai báo trường tùy chỉnh thành công.", "field": field}), 201
    except ValueError as e:
        err_code = str(e)
        msg_map = {
            "entity_type_invalid": "Loại đối tượng phải là 'customer' hoặc 'opportunity'.",
            "field_key_invalid": "Mã trường không hợp lệ.",
            "field_type_invalid": "Kiểu dữ liệu phải là 'text', 'number', 'date' hoặc 'select'.",
            "field_label_empty": "Vui lòng nhập tên/nhãn trường.",
            "select_options_empty": "Trường kiểu danh sách chọn (select) cần ít nhất một tùy chọn.",
            "duplicate_field_key": "Mã trường tùy chỉnh này đã tồn tại cho đối tượng.",
        }
        return jsonify({"message": msg_map.get(err_code, "Dữ liệu khai báo chưa hợp lệ.")}), 400


@api.get("/custom-fields/<int:field_id>")
def custom_fields_get(field_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    field = get_custom_field(field_id)
    if not field:
        return jsonify({"message": "Không tìm thấy trường tùy chỉnh."}), 404
    return jsonify(field)


@api.put("/custom-fields/<int:field_id>")
def custom_fields_update(field_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role != "admin":
        return jsonify({"message": "Chỉ Quản trị hệ thống mới có quyền cập nhật trường tùy chỉnh."}), 403

    body = _body()
    try:
        field = update_custom_field(
            field_id=field_id,
            field_label=str(body.get("field_label", "")),
            field_type=str(body.get("field_type", "")),
            options=body.get("options"),
            is_required=bool(body.get("is_required", False)),
            description=str(body.get("description", "")),
            display_order=int(body.get("display_order", 0)),
            is_active=bool(body.get("is_active", True)),
        )
        return jsonify({"message": "Cập nhật trường tùy chỉnh thành công.", "field": field})
    except LookupError:
        return jsonify({"message": "Không tìm thấy trường tùy chỉnh."}), 404
    except ValueError as e:
        err_code = str(e)
        msg_map = {
            "field_type_invalid": "Kiểu dữ liệu phải là 'text', 'number', 'date' hoặc 'select'.",
            "field_label_empty": "Vui lòng nhập tên/nhãn trường.",
            "select_options_empty": "Trường kiểu danh sách chọn (select) cần ít nhất một tùy chọn.",
        }
        return jsonify({"message": msg_map.get(err_code, "Dữ liệu cập nhật chưa hợp lệ.")}), 400


@api.delete("/custom-fields/<int:field_id>")
def custom_fields_delete(field_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role != "admin":
        return jsonify({"message": "Chỉ Quản trị hệ thống mới có quyền xóa trường tùy chỉnh."}), 403

    try:
        delete_custom_field(field_id)
        return jsonify({"message": "Đã xóa trường tùy chỉnh và các dữ liệu liên quan."})
    except LookupError:
        return jsonify({"message": "Không tìm thấy trường tùy chỉnh."}), 404


# ─── Customers Management & Excel Export (SCRUM-66) ──────────────────────────

@api.get("/customers")
def customers_list_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1
    try:
        per_page = min(max(int(request.args.get("per_page", "20")), 1), 100)
    except ValueError:
        per_page = 20

    # Lấy các query param có tiền tố 'cf_' làm bộ lọc trường tùy chỉnh
    cf_filters = {k[3:]: v for k, v in request.args.items() if k.startswith("cf_")}

    return jsonify(list_customers(q=q, status=status, cf_filters=cf_filters, page=page, per_page=per_page))


@api.get("/customers/export-excel")
def customers_export_excel():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    cf_filters = {k[3:]: v for k, v in request.args.items() if k.startswith("cf_")}

    stream = export_customers_excel(q=q, status=status, cf_filters=cf_filters)
    return send_file(
        stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="Danh_sach_Khach_hang.xlsx",
    )


@api.get("/customers/<int:customer_id>")
def customers_get_api(customer_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    c = get_customer(customer_id)
    if not c:
        return jsonify({"message": "Không tìm thấy khách hàng."}), 404
    return jsonify(c)


@api.post("/customers")
def customers_create_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    body = _body()
    name = str(body.get("name", "")).strip()
    if not name:
        return jsonify({"message": "Thông tin chưa hợp lệ.", "errors": {"name": "Vui lòng nhập tên khách hàng."}}), 400

    try:
        c = create_customer(
            name=name,
            phone=str(body.get("phone", "")),
            email=str(body.get("email", "")),
            address=str(body.get("address", "")),
            status=str(body.get("status", "Mới")),
            created_by=user.id,
            custom_fields=body.get("custom_fields"),
        )
        return jsonify({"message": "Tạo mới khách hàng thành công.", "customer": c}), 201
    except ValueError as e:
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        return jsonify({"message": "Tên khách hàng không được để trống."}), 400


@api.put("/customers/<int:customer_id>")
def customers_update_api(customer_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    body = _body()
    name = str(body.get("name", "")).strip()
    if not name:
        return jsonify({"message": "Thông tin chưa hợp lệ.", "errors": {"name": "Vui lòng nhập tên khách hàng."}}), 400

    try:
        c = update_customer(
            customer_id=customer_id,
            name=name,
            phone=str(body.get("phone", "")),
            email=str(body.get("email", "")),
            address=str(body.get("address", "")),
            status=str(body.get("status", "Mới")),
            custom_fields=body.get("custom_fields"),
        )
        return jsonify({"message": "Cập nhật khách hàng thành công.", "customer": c})
    except LookupError:
        return jsonify({"message": "Không tìm thấy khách hàng."}), 404
    except ValueError as e:
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        return jsonify({"message": "Dữ liệu chưa hợp lệ."}), 400


@api.delete("/customers/<int:customer_id>")
def customers_delete_api(customer_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    try:
        delete_customer(customer_id)
        return jsonify({"message": "Đã xóa khách hàng thành công."})
    except LookupError:
        return jsonify({"message": "Không tìm thấy khách hàng."}), 404


# ─── Opportunities Management & Excel Export (SCRUM-66) ──────────────────────

@api.get("/opportunities")
def opportunities_list_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    q = request.args.get("q", "").strip()
    stage = request.args.get("stage", "").strip()
    customer_id = request.args.get("customer_id")
    try:
        cid = int(customer_id) if customer_id else None
    except ValueError:
        cid = None

    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1
    try:
        per_page = min(max(int(request.args.get("per_page", "20")), 1), 100)
    except ValueError:
        per_page = 20

    cf_filters = {k[3:]: v for k, v in request.args.items() if k.startswith("cf_")}

    return jsonify(list_opportunities(q=q, stage=stage, customer_id=cid, cf_filters=cf_filters, page=page, per_page=per_page))


@api.get("/opportunities/export-excel")
def opportunities_export_excel():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    q = request.args.get("q", "").strip()
    stage = request.args.get("stage", "").strip()
    customer_id = request.args.get("customer_id")
    try:
        cid = int(customer_id) if customer_id else None
    except ValueError:
        cid = None
    cf_filters = {k[3:]: v for k, v in request.args.items() if k.startswith("cf_")}

    stream = export_opportunities_excel(q=q, stage=stage, customer_id=cid, cf_filters=cf_filters)
    return send_file(
        stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="Danh_sach_Co_hoi.xlsx",
    )


@api.get("/opportunities/<int:opportunity_id>")
def opportunities_get_api(opportunity_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    o = get_opportunity(opportunity_id)
    if not o:
        return jsonify({"message": "Không tìm thấy cơ hội kinh doanh."}), 404
    return jsonify(o)


@api.post("/opportunities")
def opportunities_create_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    body = _body()
    title = str(body.get("title", "")).strip()
    customer_id = body.get("customer_id")
    errors = {}
    if not title:
        errors["title"] = "Vui lòng nhập tên cơ hội."
    if not customer_id:
        errors["customer_id"] = "Vui lòng chọn khách hàng."

    if errors:
        return jsonify({"message": "Thông tin chưa hợp lệ.", "errors": errors}), 400

    try:
        o = create_opportunity(
            title=title,
            customer_id=int(customer_id),
            value=float(body.get("value", 0.0)),
            stage=str(body.get("stage", "Mới tạo")),
            expected_close_date=str(body.get("expected_close_date", "")),
            created_by=user.id,
            custom_fields=body.get("custom_fields"),
        )
        return jsonify({"message": "Tạo mới cơ hội thành công.", "opportunity": o}), 201
    except ValueError as e:
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        if str(e) == "customer_not_found":
            return jsonify({"message": "Khách hàng không tồn tại."}), 404
        return jsonify({"message": "Dữ liệu chưa hợp lệ."}), 400


@api.put("/opportunities/<int:opportunity_id>")
def opportunities_update_api(opportunity_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    body = _body()
    title = str(body.get("title", "")).strip()
    customer_id = body.get("customer_id")
    errors = {}
    if not title:
        errors["title"] = "Vui lòng nhập tên cơ hội."
    if not customer_id:
        errors["customer_id"] = "Vui lòng chọn khách hàng."

    if errors:
        return jsonify({"message": "Thông tin chưa hợp lệ.", "errors": errors}), 400

    try:
        o = update_opportunity(
            opportunity_id=opportunity_id,
            title=title,
            customer_id=int(customer_id),
            value=float(body.get("value", 0.0)),
            stage=str(body.get("stage", "Mới tạo")),
            expected_close_date=str(body.get("expected_close_date", "")),
            custom_fields=body.get("custom_fields"),
        )
        return jsonify({"message": "Cập nhật cơ hội thành công.", "opportunity": o})
    except LookupError:
        return jsonify({"message": "Không tìm thấy cơ hội."}), 404
    except ValueError as e:
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        if str(e) == "customer_not_found":
            return jsonify({"message": "Khách hàng không tồn tại."}), 404
        return jsonify({"message": "Dữ liệu chưa hợp lệ."}), 400


@api.delete("/opportunities/<int:opportunity_id>")
def opportunities_delete_api(opportunity_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    try:
        delete_opportunity(opportunity_id)
        return jsonify({"message": "Đã xóa cơ hội thành công."})
    except LookupError:
        return jsonify({"message": "Không tìm thấy cơ hội."}), 404


# ─── Register ────────────────────────────────────────────────────────────────

def register_routes(app: Flask) -> None:
    app.before_request(load_current_user)
    app.register_blueprint(api)

