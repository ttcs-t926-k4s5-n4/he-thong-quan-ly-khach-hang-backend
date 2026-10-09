"""
routes.py — Tất cả API endpoints (bao gồm SCRUM-86: Bộ lọc Lead nâng cao + Bộ lọc lưu sẵn)
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
from app.customer_filters import (
    create_saved_filter,
    delete_saved_filter,
    get_saved_filter,
    list_saved_filters,
    search_and_filter_customers,
    update_saved_filter,
)
from app.periodic_care import (
    list_customer_interactions,
    list_periodic_care_customers,
    record_customer_interaction,
)
from app.leads import (
    create_lead,
    delete_lead,
    get_lead,
    get_lead_activities,
    list_leads,
    update_lead,
)
from app.lead_filters import (
    apply_lead_saved_filter,
    create_lead_saved_filter,
    delete_lead_saved_filter,
    get_lead_saved_filter,
    list_lead_saved_filters,
    search_and_filter_leads,
    update_lead_saved_filter,
)
from app.support_tickets import (
    create_support_ticket,
    delete_support_ticket,
    get_customer_360,
    get_support_ticket,
    list_churn_risk_alerts,
    list_support_tickets,
    update_support_ticket,
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
from app.pipeline_stages import (
    create_pipeline_stage,
    delete_pipeline_stage,
    get_pipeline_stage,
    get_sales_forecast_summary,
    list_pipeline_stages,
    update_pipeline_stage,
)
from app.win_loss_reasons import (
    create_competitor,
    create_win_loss_reason,
    delete_competitor,
    delete_win_loss_reason,
    get_competitor,
    get_win_loss_reason,
    list_competitors,
    list_win_loss_reasons,
    update_competitor,
    update_win_loss_reason,
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
            stage_key=str(body.get("stage_key", "")),
            expected_close_date=str(body.get("expected_close_date", "")),
            meetings_count=int(body.get("meetings_count", 0)),
            win_reason_id=body.get("win_reason_id"),
            loss_reason_id=body.get("loss_reason_id"),
            competitor_id=body.get("competitor_id"),
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
            stage_key=str(body.get("stage_key", "")),
            expected_close_date=str(body.get("expected_close_date", "")),
            meetings_count=int(body.get("meetings_count", 0)),
            win_reason_id=body.get("win_reason_id"),
            loss_reason_id=body.get("loss_reason_id"),
            competitor_id=body.get("competitor_id"),
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


# ─── S2-09: Pipeline Stages & Sales Forecast APIs ───────────────────────────

@api.get("/pipeline-stages")
def pipeline_stages_list_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    is_active_only = request.args.get("active_only", "false").lower() == "true"
    stages = list_pipeline_stages(is_active_only=is_active_only)
    return jsonify({"items": stages})


@api.post("/pipeline-stages")
def pipeline_stages_create_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Chỉ Giám đốc kinh doanh hoặc Quản trị viên mới có quyền cấu hình Pipeline."}), 403

    body = _body()
    try:
        stage = create_pipeline_stage(
            stage_key=str(body.get("stage_key", "")),
            stage_name=str(body.get("stage_name", "")),
            win_probability=int(body.get("win_probability", 0)),
            display_order=int(body.get("display_order", 0)),
            required_conditions=body.get("required_conditions"),
            is_won_stage=bool(body.get("is_won_stage", False)),
            is_lost_stage=bool(body.get("is_lost_stage", False)),
            is_active=bool(body.get("is_active", True)),
        )
        return jsonify({"message": "Cấu hình giai đoạn Pipeline thành công.", "stage": stage}), 201
    except ValueError as e:
        err_map = {
            "stage_key_invalid": "Mã giai đoạn không hợp lệ.",
            "stage_name_empty": "Vui lòng nhập tên giai đoạn.",
            "duplicate_stage_key": "Mã giai đoạn này đã tồn tại.",
        }
        return jsonify({"message": err_map.get(str(e), "Dữ liệu chưa hợp lệ.")}), 400


@api.get("/pipeline-stages/<int:stage_id>")
def pipeline_stages_get_api(stage_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    s = get_pipeline_stage(stage_id)
    if not s:
        return jsonify({"message": "Không tìm thấy giai đoạn."}), 404
    return jsonify(s)


@api.put("/pipeline-stages/<int:stage_id>")
def pipeline_stages_update_api(stage_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Chỉ Giám đốc kinh doanh hoặc Quản trị viên mới có quyền cấu hình Pipeline."}), 403

    body = _body()
    try:
        stage = update_pipeline_stage(
            stage_id=stage_id,
            stage_name=str(body.get("stage_name", "")),
            win_probability=int(body.get("win_probability", 0)),
            display_order=int(body.get("display_order", 0)),
            required_conditions=body.get("required_conditions"),
            is_won_stage=bool(body.get("is_won_stage", False)),
            is_lost_stage=bool(body.get("is_lost_stage", False)),
            is_active=bool(body.get("is_active", True)),
        )
        return jsonify({"message": "Cập nhật giai đoạn Pipeline thành công.", "stage": stage})
    except LookupError:
        return jsonify({"message": "Không tìm thấy giai đoạn."}), 404
    except ValueError as e:
        err_map = {"stage_name_empty": "Vui lòng nhập tên giai đoạn."}
        return jsonify({"message": err_map.get(str(e), "Dữ liệu chưa hợp lệ.")}), 400


@api.delete("/pipeline-stages/<int:stage_id>")
def pipeline_stages_delete_api(stage_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Chỉ Giám đốc kinh doanh hoặc Quản trị viên mới có quyền cấu hình Pipeline."}), 403

    try:
        delete_pipeline_stage(stage_id)
        return jsonify({"message": "Đã xóa giai đoạn Pipeline."})
    except LookupError:
        return jsonify({"message": "Không tìm thấy giai đoạn."}), 404


@api.get("/forecast/summary")
def forecast_summary_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    return jsonify(get_sales_forecast_summary())


# ─── S2-10: Win/Loss Reasons & Competitors APIs ──────────────────────────────

@api.get("/win-loss-reasons")
def win_loss_reasons_list_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    r_type = request.args.get("type", "").strip().lower()
    is_active_only = request.args.get("active_only", "false").lower() == "true"
    items = list_win_loss_reasons(reason_type=r_type or None, is_active_only=is_active_only)
    return jsonify({"items": items})


@api.post("/win-loss-reasons")
def win_loss_reasons_create_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Chỉ Giám đốc kinh doanh hoặc Quản trị viên mới có quyền khai báo danh mục lý do."}), 403

    body = _body()
    try:
        item = create_win_loss_reason(
            reason_type=str(body.get("reason_type", "")),
            reason_code=str(body.get("reason_code", "")),
            reason_title=str(body.get("reason_title", "")),
            description=str(body.get("description", "")),
            is_active=bool(body.get("is_active", True)),
        )
        return jsonify({"message": "Khai báo lý do thắng/thua thành công.", "reason": item}), 201
    except ValueError as e:
        err_map = {
            "reason_type_invalid": "Loại lý do phải là 'win' hoặc 'loss'.",
            "reason_code_invalid": "Mã lý do không hợp lệ.",
            "reason_title_empty": "Vui lòng nhập tên/nội dung lý do.",
            "duplicate_reason_code": "Mã lý do này đã tồn tại cho loại đã chọn.",
        }
        return jsonify({"message": err_map.get(str(e), "Dữ liệu chưa hợp lệ.")}), 400


@api.put("/win-loss-reasons/<int:reason_id>")
def win_loss_reasons_update_api(reason_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Chỉ Giám đốc kinh doanh hoặc Quản trị viên mới có quyền sửa lý do."}), 403

    body = _body()
    try:
        item = update_win_loss_reason(
            reason_id=reason_id,
            reason_title=str(body.get("reason_title", "")),
            description=str(body.get("description", "")),
            is_active=bool(body.get("is_active", True)),
        )
        return jsonify({"message": "Cập nhật lý do thắng/thua thành công.", "reason": item})
    except LookupError:
        return jsonify({"message": "Không tìm thấy lý do."}), 404
    except ValueError as e:
        err_map = {"reason_title_empty": "Vui lòng nhập tên lý do."}
        return jsonify({"message": err_map.get(str(e), "Dữ liệu chưa hợp lệ.")}), 400


@api.delete("/win-loss-reasons/<int:reason_id>")
def win_loss_reasons_delete_api(reason_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Chỉ Giám đốc kinh doanh hoặc Quản trị viên mới có quyền xóa lý do."}), 403

    try:
        delete_win_loss_reason(reason_id)
        return jsonify({"message": "Đã xóa lý do thắng/thua."})
    except LookupError:
        return jsonify({"message": "Không tìm thấy lý do."}), 404


@api.get("/competitors")
def competitors_list_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    is_active_only = request.args.get("active_only", "false").lower() == "true"
    items = list_competitors(is_active_only=is_active_only)
    return jsonify({"items": items})


@api.post("/competitors")
def competitors_create_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Chỉ Giám đốc kinh doanh hoặc Quản trị viên mới có quyền khai báo đối thủ."}), 403

    body = _body()
    try:
        comp = create_competitor(
            code=str(body.get("code", "")),
            name=str(body.get("name", "")),
            website=str(body.get("website", "")),
            strengths=str(body.get("strengths", "")),
            weaknesses=str(body.get("weaknesses", "")),
            is_active=bool(body.get("is_active", True)),
        )
        return jsonify({"message": "Khai báo đối thủ cạnh tranh thành công.", "competitor": comp}), 201
    except ValueError as e:
        err_map = {
            "competitor_code_invalid": "Mã đối thủ không hợp lệ.",
            "competitor_name_empty": "Vui lòng nhập tên đối thủ.",
            "duplicate_competitor_code": "Mã đối thủ này đã tồn tại.",
        }
        return jsonify({"message": err_map.get(str(e), "Dữ liệu chưa hợp lệ.")}), 400


@api.get("/competitors/<int:competitor_id>")
def competitors_get_api(competitor_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    comp = get_competitor(competitor_id)
    if not comp:
        return jsonify({"message": "Không tìm thấy đối thủ cạnh tranh."}), 404
    return jsonify(comp)


@api.put("/competitors/<int:competitor_id>")
def competitors_update_api(competitor_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Chỉ Giám đốc kinh doanh hoặc Quản trị viên mới có quyền cập nhật đối thủ."}), 403

    body = _body()
    try:
        comp = update_competitor(
            competitor_id=competitor_id,
            name=str(body.get("name", "")),
            website=str(body.get("website", "")),
            strengths=str(body.get("strengths", "")),
            weaknesses=str(body.get("weaknesses", "")),
            is_active=bool(body.get("is_active", True)),
        )
        return jsonify({"message": "Cập nhật đối thủ cạnh tranh thành công.", "competitor": comp})
    except LookupError:
        return jsonify({"message": "Không tìm thấy đối thủ."}), 404
    except ValueError as e:
        err_map = {"competitor_name_empty": "Vui lòng nhập tên đối thủ."}
        return jsonify({"message": err_map.get(str(e), "Dữ liệu chưa hợp lệ.")}), 400


@api.delete("/competitors/<int:competitor_id>")
def competitors_delete_api(competitor_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Chỉ Giám đốc kinh doanh hoặc Quản trị viên mới có quyền xóa đối thủ."}), 403

    try:
        delete_competitor(competitor_id)
        return jsonify({"message": "Đã xóa đối thủ cạnh tranh."})
    except LookupError:
        return jsonify({"message": "Không tìm thấy đối thủ."}), 404


# ─── SCRUM-75: Customer Multi-Criteria Filter & Saved Filters ────────────────

@api.get("/customers/search-filter")
def customers_search_filter_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    q = request.args.get("q", "")
    status = request.args.get("status", "")
    industry = request.args.get("industry", "")
    scale = request.args.get("scale", "")
    region = request.args.get("region", "")
    owner_id_str = request.args.get("owner_id", "")
    owner_id = int(owner_id_str) if owner_id_str.isdigit() else None
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    sort_by = request.args.get("sort_by", "created_at")
    order = request.args.get("order", "desc")

    # Thu thập các cf_* param nếu có
    cf_filters = {}
    for k, v in request.args.items():
        if k.startswith("cf_") and v:
            cf_key = k[3:]
            cf_filters[cf_key] = v

    result = search_and_filter_customers(
        q=q,
        status=status,
        industry=industry,
        scale=scale,
        region=region,
        owner_id=owner_id,
        cf_filters=cf_filters,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        order=order,
    )
    return jsonify(result)


@api.get("/saved-filters")
def saved_filters_list_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    target = request.args.get("target", "customer")
    items = list_saved_filters(user_id=user.id, filter_target=target)
    return jsonify({"items": items})


@api.post("/saved-filters")
def saved_filters_create_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    body = _body()
    try:
        sf = create_saved_filter(
            user_id=user.id,
            name=str(body.get("name", "")),
            criteria=body.get("criteria", {}),
            filter_target=str(body.get("filter_target", "customer")),
        )
        return jsonify({"message": "Lưu bộ lọc thành công.", "saved_filter": sf}), 201
    except ValueError as e:
        err_map = {"filter_name_empty": "Vui lòng nhập tên bộ lọc.", "criteria_invalid": "Tiêu chí bộ lọc không hợp lệ."}
        return jsonify({"message": err_map.get(str(e), "Dữ liệu không hợp lệ.")}), 400


@api.get("/saved-filters/<int:filter_id>")
def saved_filters_get_api(filter_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    sf = get_saved_filter(filter_id, user_id=user.id)
    if not sf:
        return jsonify({"message": "Không tìm thấy bộ lọc đã lưu."}), 404
    return jsonify(sf)


@api.put("/saved-filters/<int:filter_id>")
def saved_filters_update_api(filter_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    body = _body()
    try:
        sf = update_saved_filter(
            filter_id=filter_id,
            user_id=user.id,
            name=str(body.get("name", "")),
            criteria=body.get("criteria", {}),
        )
        return jsonify({"message": "Cập nhật bộ lọc thành công.", "saved_filter": sf})
    except LookupError:
        return jsonify({"message": "Không tìm thấy bộ lọc đã lưu."}), 404
    except ValueError as e:
        err_map = {"filter_name_empty": "Vui lòng nhập tên bộ lọc.", "criteria_invalid": "Tiêu chí bộ lọc không hợp lệ."}
        return jsonify({"message": err_map.get(str(e), "Dữ liệu không hợp lệ.")}), 400


@api.delete("/saved-filters/<int:filter_id>")
def saved_filters_delete_api(filter_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    try:
        delete_saved_filter(filter_id, user_id=user.id)
        return jsonify({"message": "Đã xóa bộ lọc."})
    except LookupError:
        return jsonify({"message": "Không tìm thấy bộ lọc đã lưu."}), 404


# ─── SCRUM-76: Support Tickets & Customer Churn-Risk Flagging Engine ─────────

@api.get("/support-tickets")
def support_tickets_list_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    cust_id_str = request.args.get("customer_id", "")
    customer_id = int(cust_id_str) if cust_id_str.isdigit() else None
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")
    ass_id_str = request.args.get("assignee_id", "")
    assignee_id = int(ass_id_str) if ass_id_str.isdigit() else None
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    result = list_support_tickets(
        customer_id=customer_id,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        page=page,
        per_page=per_page,
    )
    return jsonify(result)


@api.post("/support-tickets")
def support_tickets_create_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    body = _body()
    try:
        ticket = create_support_ticket(
            customer_id=int(body.get("customer_id", 0)),
            title=str(body.get("title", "")),
            description=str(body.get("description", "")),
            priority=str(body.get("priority", "medium")),
            status=str(body.get("status", "open")),
            assignee_id=body.get("assignee_id"),
            created_by=user.id,
        )
        return jsonify({"message": "Tạo yêu cầu hỗ trợ thành công.", "ticket": ticket}), 201
    except LookupError:
        return jsonify({"message": "Không tìm thấy khách hàng."}), 404
    except ValueError as e:
        err_map = {
            "ticket_title_empty": "Vui lòng nhập tiêu đề yêu cầu hỗ trợ.",
            "priority_invalid": "Mức độ ưu tiên không hợp lệ (low, medium, high, urgent).",
            "status_invalid": "Trạng thái không hợp lệ (open, in_progress, resolved, closed).",
        }
        return jsonify({"message": err_map.get(str(e), "Dữ liệu chưa hợp lệ.")}), 400


@api.get("/support-tickets/<int:ticket_id>")
def support_tickets_get_api(ticket_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    ticket = get_support_ticket(ticket_id)
    if not ticket:
        return jsonify({"message": "Không tìm thấy yêu cầu hỗ trợ."}), 404
    return jsonify(ticket)


@api.put("/support-tickets/<int:ticket_id>")
def support_tickets_update_api(ticket_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    body = _body()
    try:
        ticket = update_support_ticket(
            ticket_id=ticket_id,
            title=str(body.get("title", "")),
            description=str(body.get("description", "")),
            priority=str(body.get("priority", "medium")),
            status=str(body.get("status", "open")),
            assignee_id=body.get("assignee_id"),
        )
        return jsonify({"message": "Cập nhật yêu cầu hỗ trợ thành công.", "ticket": ticket})
    except LookupError:
        return jsonify({"message": "Không tìm thấy yêu cầu hỗ trợ."}), 404
    except ValueError as e:
        err_map = {
            "ticket_title_empty": "Vui lòng nhập tiêu đề yêu cầu hỗ trợ.",
            "priority_invalid": "Mức độ ưu tiên không hợp lệ.",
            "status_invalid": "Trạng thái không hợp lệ.",
        }
        return jsonify({"message": err_map.get(str(e), "Dữ liệu chưa hợp lệ.")}), 400


@api.delete("/support-tickets/<int:ticket_id>")
def support_tickets_delete_api(ticket_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    try:
        delete_support_ticket(ticket_id)
        return jsonify({"message": "Đã xóa yêu cầu hỗ trợ."})
    except LookupError:
        return jsonify({"message": "Không tìm thấy yêu cầu hỗ trợ."}), 404


@api.get("/customers/<int:customer_id>/360")
def customer_360_api(customer_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    cust_360 = get_customer_360(customer_id)
    if not cust_360:
        return jsonify({"message": "Không tìm thấy khách hàng."}), 404
    return jsonify(cust_360)


@api.get("/churn-risk-alerts")
def churn_risk_alerts_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    alerts = list_churn_risk_alerts()
    return jsonify({"items": alerts})


# ─── SCRUM-77: Periodic Customer Care & Interaction Tracking Engine ─────────

@api.get("/customers/periodic-care")
def customers_periodic_care_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    days = request.args.get("days", 30, type=int)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    result = list_periodic_care_customers(days=days, page=page, per_page=per_page)
    return jsonify(result)


@api.get("/customers/<int:customer_id>/interactions")
def customer_interactions_list_api(customer_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    interactions = list_customer_interactions(customer_id)
    return jsonify({"items": interactions})


@api.post("/customers/<int:customer_id>/interactions")
def customer_interactions_create_api(customer_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    body = _body()
    try:
        record = record_customer_interaction(
            customer_id=customer_id,
            interaction_type=str(body.get("interaction_type", "Gọi điện chăm sóc")),
            notes=str(body.get("notes", "")),
            created_by=user.id,
        )
        return jsonify({"message": "Đã ghi nhận tương tác chăm sóc khách hàng.", "interaction": record}), 201
    except LookupError:
        return jsonify({"message": "Không tìm thấy khách hàng."}), 404


@api.post("/customers/<int:customer_id>/mark-contacted")
def customer_mark_contacted_api(customer_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    body = _body()
    try:
        record = record_customer_interaction(
            customer_id=customer_id,
            interaction_type=str(body.get("interaction_type", "Đánh dấu đã liên hệ ngay")),
            notes=str(body.get("notes", "Đã liên hệ trực tiếp từ danh sách chăm sóc định kỳ.")),
            created_by=user.id,
        )
        return jsonify({"message": "Đã đánh dấu liên hệ khách hàng thành công.", "interaction": record}), 201
    except LookupError:
        return jsonify({"message": "Không tìm thấy khách hàng."}), 404


# ─── SCRUM-86: Danh sách Lead với Bộ lọc nâng cao + Bộ lọc lưu sẵn ───────────────

@api.get("/leads")
def leads_list_api():
    """
    Danh sách lead cơ bản (SCRUM-84 compatible).
    Nhân viên chỉ thấy lead của mình; manager/admin thấy tất cả.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    assigned_to_str = request.args.get("assigned_to", "")
    assigned_to = int(assigned_to_str) if assigned_to_str.isdigit() else None
    if user.role == "employee" and assigned_to is None:
        assigned_to = user.id

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    result = list_leads(
        q=request.args.get("q", ""),
        status=request.args.get("status", ""),
        source=request.args.get("source", ""),
        classification=request.args.get("classification", ""),
        assigned_to=assigned_to,
        sla_breached_only=request.args.get("sla_breached_only", "false").lower() == "true",
        date_from=int(request.args.get("date_from")) if request.args.get("date_from", "").isdigit() else None,
        date_to=int(request.args.get("date_to")) if request.args.get("date_to", "").isdigit() else None,
        page=page,
        per_page=per_page,
        sort_by=request.args.get("sort_by", "created_at"),
        order=request.args.get("order", "desc"),
    )
    return jsonify(result)


@api.post("/leads")
def leads_create_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    body = _body()
    full_name = str(body.get("full_name", "")).strip()
    if not full_name:
        return jsonify({"message": "Thông tin chưa hợp lệ.", "errors": {"full_name": "Vui lòng nhập tên lead."}}), 400
    try:
        lead = create_lead(
            full_name=full_name,
            email=str(body.get("email", "")),
            phone=str(body.get("phone", "")),
            company=str(body.get("company", "")),
            source=str(body.get("source", "")),
            classification=str(body.get("classification", "cold")),
            notes=str(body.get("notes", "")),
            created_by=user.id,
        )
        return jsonify({"message": "Tạo lead thành công.", "lead": lead}), 201
    except ValueError:
        return jsonify({"message": "Dữ liệu chưa hợp lệ."}), 400


@api.get("/leads/<int:lead_id>")
def leads_get_api(lead_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    lead = get_lead(lead_id)
    if not lead:
        return jsonify({"message": "Không tìm thấy lead."}), 404
    return jsonify(lead)


@api.put("/leads/<int:lead_id>")
def leads_update_api(lead_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    body = _body()
    try:
        lead = update_lead(
            lead_id=lead_id,
            full_name=body.get("full_name"),
            email=body.get("email"),
            phone=body.get("phone"),
            company=body.get("company"),
            source=body.get("source"),
            classification=body.get("classification"),
            notes=body.get("notes"),
            updated_by=user.id,
        )
        return jsonify({"message": "Cập nhật lead thành công.", "lead": lead})
    except LookupError:
        return jsonify({"message": "Không tìm thấy lead."}), 404
    except ValueError as e:
        err_map = {
            "lead_name_empty": "Vui lòng nhập tên lead.",
            "lead_already_converted": "Lead đã chuyển đổi, không thể chỉnh sửa.",
        }
        return jsonify({"message": err_map.get(str(e), "Dữ liệu chưa hợp lệ.")}), 400


@api.delete("/leads/<int:lead_id>")
def leads_delete_api(lead_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Không có quyền xóa lead."}), 403
    try:
        delete_lead(lead_id)
        return jsonify({"message": "Đã xóa lead thành công."})
    except LookupError:
        return jsonify({"message": "Không tìm thấy lead."}), 404


@api.get("/leads/<int:lead_id>/activities")
def leads_activities_api(lead_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    lead = get_lead(lead_id)
    if not lead:
        return jsonify({"message": "Không tìm thấy lead."}), 404
    activities = get_lead_activities(lead_id)
    return jsonify({"items": activities})


# ─── SCRUM-86: Bộ lọc Lead nâng cao ───────────────────────────────────────────

@api.get("/leads/search-filter")
def leads_search_filter_api():
    """
    Lọc lead nâng cao theo nhiều tiêu chí (SCRUM-86):
    - Trạng thái, nguồn, phân loại nóng/ấm/lạnh, người phụ trách, khoảng thời gian.
    - Lead quá SLA tự động đánh dấu sla_status='breached' để hiển thị nổi bật.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    assigned_to_str = request.args.get("assigned_to", "")
    assigned_to = int(assigned_to_str) if assigned_to_str.isdigit() else None
    # Nhân viên chỉ xem lead của mình
    if user.role == "employee" and assigned_to is None:
        assigned_to = user.id

    date_from_str = request.args.get("date_from", "")
    date_to_str = request.args.get("date_to", "")

    result = search_and_filter_leads(
        q=request.args.get("q", ""),
        status=request.args.get("status", ""),
        source=request.args.get("source", ""),
        classification=request.args.get("classification", ""),
        assigned_to=assigned_to,
        date_from=int(date_from_str) if date_from_str.isdigit() else None,
        date_to=int(date_to_str) if date_to_str.isdigit() else None,
        sla_breached_only=request.args.get("sla_breached_only", "false").lower() == "true",
        page=request.args.get("page", 1, type=int),
        per_page=request.args.get("per_page", 20, type=int),
        sort_by=request.args.get("sort_by", "created_at"),
        order=request.args.get("order", "desc"),
    )
    return jsonify(result)


# ─── SCRUM-86: Bộ lọc Lead đã lưu sẵn ────────────────────────────────────────

@api.get("/lead-saved-filters")
def lead_saved_filters_list_api():
    """Danh sách bộ lọc lead đã lưu của người dùng hiện tại."""
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    items = list_lead_saved_filters(user_id=user.id)
    return jsonify({"items": items})


@api.post("/lead-saved-filters")
def lead_saved_filters_create_api():
    """
    Lưu bộ lọc lead với tên gợi nhớ (SCRUM-86).
    Cho phép nhân viên mở máy buổi sáng là biết ngay hôm nay cần gọi ai.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    body = _body()
    try:
        sf = create_lead_saved_filter(
            user_id=user.id,
            name=str(body.get("name", "")),
            criteria=body.get("criteria", {}),
        )
        return jsonify({"message": "Lưu bộ lọc lead thành công.", "saved_filter": sf}), 201
    except ValueError as e:
        err_map = {
            "filter_name_empty": "Vui lòng nhập tên bộ lọc.",
            "criteria_invalid": "Tiêu chí bộ lọc không hợp lệ.",
        }
        return jsonify({"message": err_map.get(str(e), "Dữ liệu không hợp lệ.")}), 400


@api.get("/lead-saved-filters/<int:filter_id>")
def lead_saved_filters_get_api(filter_id: int):
    """Lấy bộ lọc lead đã lưu theo id."""
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    sf = get_lead_saved_filter(filter_id, user_id=user.id)
    if not sf:
        return jsonify({"message": "Không tìm thấy bộ lọc."}), 404
    return jsonify(sf)


@api.put("/lead-saved-filters/<int:filter_id>")
def lead_saved_filters_update_api(filter_id: int):
    """Cập nhật tên/tiêu chí bộ lọc lead đã lưu."""
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    body = _body()
    try:
        sf = update_lead_saved_filter(
            filter_id=filter_id,
            user_id=user.id,
            name=str(body.get("name", "")),
            criteria=body.get("criteria", {}),
        )
        return jsonify({"message": "Cập nhật bộ lọc thành công.", "saved_filter": sf})
    except LookupError:
        return jsonify({"message": "Không tìm thấy bộ lọc."}), 404
    except ValueError as e:
        err_map = {
            "filter_name_empty": "Vui lòng nhập tên bộ lọc.",
            "criteria_invalid": "Tiêu chí bộ lọc không hợp lệ.",
        }
        return jsonify({"message": err_map.get(str(e), "Dữ liệu không hợp lệ.")}), 400


@api.delete("/lead-saved-filters/<int:filter_id>")
def lead_saved_filters_delete_api(filter_id: int):
    """Xóa bộ lọc lead đã lưu."""
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    try:
        delete_lead_saved_filter(filter_id, user_id=user.id)
        return jsonify({"message": "Đã xóa bộ lọc."})
    except LookupError:
        return jsonify({"message": "Không tìm thấy bộ lọc."}), 404


@api.get("/lead-saved-filters/<int:filter_id>/apply")
def lead_saved_filters_apply_api(filter_id: int):
    """
    Áp dụng bộ lọc đã lưu và trả về danh sách lead phù hợp (SCRUM-86).
    Cho phép mở máy buổi sáng là biết ngay hôm nay cần gọi ai.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        result = apply_lead_saved_filter(
            filter_id=filter_id,
            user_id=user.id,
            page=page,
            per_page=per_page,
        )
        return jsonify(result)
    except LookupError:
        return jsonify({"message": "Không tìm thấy bộ lọc."}), 404


# ─── Register ────────────────────────────────────────────────────────────────

def register_routes(app: Flask) -> None:
    app.before_request(load_current_user)
    app.register_blueprint(api)





