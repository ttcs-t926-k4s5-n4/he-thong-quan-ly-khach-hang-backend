"""
routes.py ΓÇö Tß║Ñt cß║ú API endpoints (bao gß╗ôm SCRUM-85: Chuyß╗ân Lead th├ánh Kh├ích h├áng + C╞í hß╗Öi)
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
    accept_lead,
    assign_lead,
    check_and_flag_sla_breached_leads,
    create_lead,
    delete_lead,
    get_lead,
    get_lead_activities,
    get_sla_breached_leads,
    list_leads,
    reject_lead,
    update_lead,
)
from app.lead_convert import (
    convert_lead_to_customer,
    get_lead_contact,
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
        return None, (jsonify({"message": "Phi├¬n ─æ─âng nhß║¡p ─æ├ú hß║┐t hß║ín. Vui l├▓ng ─æ─âng nhß║¡p lß║íi.", "code": "session_expired"}), 401)
    return user, None


# ΓöÇΓöÇΓöÇ Health ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

@api.get("/health")
def health():
    return jsonify({"status": "ok", "service": "sprint1-backend", "version": "1.0.0"})


# ΓöÇΓöÇΓöÇ Auth (S1-01, S1-02, S1-10) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

@api.post("/auth/login")
def auth_login():
    body = _body()
    email = str(body.get("email", "")).strip()
    password = str(body.get("password", ""))
    if not email or not password:
        return jsonify({"message": "Email hoß║╖c mß║¡t khß║⌐u kh├┤ng ─æ├║ng."}), 401
    status_code, payload = login(email, password)
    return jsonify(payload), status_code


@api.get("/auth/me")
def auth_me():
    user = get_current_user()
    if user is None:
        return jsonify({"message": "Ch╞░a ─æ─âng nhß║¡p.", "code": "unauthenticated"}), 401
    return jsonify(get_user_profile(user))


@api.post("/auth/logout")
def auth_logout():
    logout_current_user()
    return jsonify({"message": "─É├ú ─æ─âng xuß║Ñt an to├án."})


# ΓöÇΓöÇΓöÇ Reset password (S1-03) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

@api.post("/auth/forgot-password")
def forgot_password():
    body = _body()
    email = str(body.get("email", "")).strip()
    if not email:
        return jsonify({"message": "Vui l├▓ng nhß║¡p email."}), 400
    msg = request_password_reset(email)
    return jsonify({"message": msg})


@api.get("/auth/reset-password/<token>")
def check_reset_token(token: str):
    valid = inspect_reset_token(token)
    if not valid:
        return jsonify({"valid": False, "message": "Li├¬n kß║┐t kh├┤ng hß╗úp lß╗ç hoß║╖c ─æ├ú hß║┐t hß║ín."}), 400
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
        errors["new_password_confirmation"] = "Vui l├▓ng x├íc nhß║¡n mß║¡t khß║⌐u mß╗¢i."
    elif new_password != confirm:
        errors["new_password_confirmation"] = "Mß║¡t khß║⌐u x├íc nhß║¡n kh├┤ng khß╗¢p."
    if errors:
        return jsonify({"message": "Dß╗» liß╗çu kh├┤ng hß╗úp lß╗ç.", "errors": errors}), 400

    result = reset_password(token, new_password)
    if result is ResetPasswordResult.INVALID_LINK:
        return jsonify({"message": "Li├¬n kß║┐t kh├┤ng hß╗úp lß╗ç, ─æ├ú hß║┐t hß║ín hoß║╖c ─æ├ú ─æ╞░ß╗úc sß╗¡ dß╗Ñng."}), 400
    return jsonify({"message": "Mß║¡t khß║⌐u ─æ├ú ─æ╞░ß╗úc ─æß║╖t lß║íi. Vui l├▓ng ─æ─âng nhß║¡p vß╗¢i mß║¡t khß║⌐u mß╗¢i."})


# ΓöÇΓöÇΓöÇ Change password (S1-04) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

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
        errors["current_password"] = "Vui l├▓ng nhß║¡p mß║¡t khß║⌐u hiß╗çn tß║íi."
    pw_err = password_rule_error(new_password)
    if pw_err:
        errors["new_password"] = pw_err
    if not confirm:
        errors["new_password_confirmation"] = "Vui l├▓ng x├íc nhß║¡n mß║¡t khß║⌐u mß╗¢i."
    elif new_password != confirm:
        errors["new_password_confirmation"] = "Mß║¡t khß║⌐u x├íc nhß║¡n kh├┤ng khß╗¢p."
    if errors:
        return jsonify({"message": "Dß╗» liß╗çu kh├┤ng hß╗úp lß╗ç.", "errors": errors}), 400

    raw = session.get("auth_token", "")
    result = change_password(user.id, str(raw), current_password, new_password)

    if result is ChangePasswordResult.WRONG_CURRENT:
        return jsonify({"message": "Mß║¡t khß║⌐u hiß╗çn tß║íi kh├┤ng ─æ├║ng.", "errors": {"current_password": "Mß║¡t khß║⌐u hiß╗çn tß║íi kh├┤ng ─æ├║ng."}}), 400
    if result is ChangePasswordResult.INVALID_NEW:
        return jsonify({"message": "Mß║¡t khß║⌐u mß╗¢i kh├┤ng ─æ├íp ß╗⌐ng y├¬u cß║ºu.", "errors": {"new_password": "Mß║¡t khß║⌐u mß╗¢i kh├┤ng ─æ├íp ß╗⌐ng y├¬u cß║ºu."}}), 400
    if result is ChangePasswordResult.SESSION_EXPIRED:
        logout_current_user()
        return jsonify({"message": "Phi├¬n ─æ─âng nhß║¡p ─æ├ú hß║┐t hß║ín. Vui l├▓ng ─æ─âng nhß║¡p lß║íi.", "code": "session_expired"}), 401

    return jsonify({"message": "Mß║¡t khß║⌐u ─æ├ú ─æ╞░ß╗úc cß║¡p nhß║¡t th├ánh c├┤ng.", "other_sessions_revoked": True})


# ΓöÇΓöÇΓöÇ User management (S1-05, S1-06, S1-08) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

@api.get("/users")
def users_list():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role != "admin":
        return jsonify({"message": "Kh├┤ng c├│ quyß╗ün truy cß║¡p."}), 403

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
        return jsonify({"message": "Kh├┤ng c├│ quyß╗ün truy cß║¡p."}), 403

    body = _body()
    values = {
        "full_name": str(body.get("full_name", "")).strip(),
        "email": str(body.get("email", "")).strip(),
        "group_name": str(body.get("group_name", "")).strip(),
        "role_name": str(body.get("role_name", "")).strip(),
    }
    errors: dict[str, str] = {}
    if not values["full_name"]:
        errors["full_name"] = "Vui l├▓ng nhß║¡p hß╗ì v├á t├¬n."
    if not values["email"]:
        errors["email"] = "Vui l├▓ng nhß║¡p email."
    elif not valid_email(values["email"]):
        errors["email"] = "Email kh├┤ng hß╗úp lß╗ç."
    if not values["group_name"]:
        errors["group_name"] = "Vui l├▓ng chß╗ìn nh├│m."
    if not values["role_name"]:
        errors["role_name"] = "Vui l├▓ng chß╗ìn vai tr├▓."
    if errors:
        return jsonify({"message": "Th├┤ng tin ch╞░a hß╗úp lß╗ç.", "errors": errors}), 400

    try:
        result = create_user(**values)
    except ValueError as e:
        if str(e) == "duplicate_email":
            return jsonify({"message": "Email ─æ├ú tß╗ôn tß║íi. Vui l├▓ng d├╣ng email kh├íc."}), 409
        raise
    return jsonify({"message": "Tß║ío t├ái khoß║ún th├ánh c├┤ng. Email k├¡ch hoß║ít k├¿m mß║¡t khß║⌐u tß║ím ─æ├ú ─æ╞░ß╗úc gß╗¡i.", "user": result}), 201


@api.put("/users/<int:user_id>")
def users_update(user_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role != "admin":
        return jsonify({"message": "Kh├┤ng c├│ quyß╗ün truy cß║¡p."}), 403

    body = _body()
    values = {
        "full_name": str(body.get("full_name", "")).strip(),
        "email": str(body.get("email", "")).strip(),
        "group_name": str(body.get("group_name", "")).strip(),
        "role_name": str(body.get("role_name", "")).strip(),
    }
    errors: dict[str, str] = {}
    if not values["full_name"]:
        errors["full_name"] = "Vui l├▓ng nhß║¡p hß╗ì v├á t├¬n."
    if not values["email"]:
        errors["email"] = "Vui l├▓ng nhß║¡p email."
    elif not valid_email(values["email"]):
        errors["email"] = "Email kh├┤ng hß╗úp lß╗ç."
    if errors:
        return jsonify({"message": "Th├┤ng tin ch╞░a hß╗úp lß╗ç.", "errors": errors}), 400

    try:
        update_user(user_id, **values)
    except ValueError as e:
        if str(e) == "duplicate_email":
            return jsonify({"message": "Email ─æ├ú tß╗ôn tß║íi."}), 409
        raise
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy t├ái khoß║ún."}), 404
    return jsonify({"message": "─É├ú cß║¡p nhß║¡t t├ái khoß║ún."})


@api.post("/users/activate")
def users_activate():
    body = _body()
    token = str(body.get("token", "")).strip()
    if not token:
        return jsonify({"message": "Thiß║┐u m├ú k├¡ch hoß║ít."}), 400
    ok = activate_account(token)
    if not ok:
        return jsonify({"message": "Li├¬n kß║┐t k├¡ch hoß║ít kh├┤ng hß╗úp lß╗ç, ─æ├ú hß║┐t hß║ín hoß║╖c ─æ├ú d├╣ng."}), 400
    return jsonify({"message": "K├¡ch hoß║ít t├ái khoß║ún th├ánh c├┤ng! Vui l├▓ng ─æ─âng nhß║¡p."})


# ΓöÇΓöÇΓöÇ Custom Fields Management (SCRUM-66) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

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
        return jsonify({"message": "Loß║íi ─æß╗æi t╞░ß╗úng kh├┤ng hß╗úp lß╗ç."}), 400
    schema = get_form_schema(entity_type)
    return jsonify({"entity_type": entity_type, "fields": schema})


@api.post("/custom-fields")
def custom_fields_create():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role != "admin":
        return jsonify({"message": "Chß╗ë Quß║ún trß╗ï hß╗ç thß╗æng mß╗¢i c├│ quyß╗ün khai b├ío tr╞░ß╗¥ng t├╣y chß╗ënh."}), 403

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
        return jsonify({"message": "Khai b├ío tr╞░ß╗¥ng t├╣y chß╗ënh th├ánh c├┤ng.", "field": field}), 201
    except ValueError as e:
        err_code = str(e)
        msg_map = {
            "entity_type_invalid": "Loß║íi ─æß╗æi t╞░ß╗úng phß║úi l├á 'customer' hoß║╖c 'opportunity'.",
            "field_key_invalid": "M├ú tr╞░ß╗¥ng kh├┤ng hß╗úp lß╗ç.",
            "field_type_invalid": "Kiß╗âu dß╗» liß╗çu phß║úi l├á 'text', 'number', 'date' hoß║╖c 'select'.",
            "field_label_empty": "Vui l├▓ng nhß║¡p t├¬n/nh├ún tr╞░ß╗¥ng.",
            "select_options_empty": "Tr╞░ß╗¥ng kiß╗âu danh s├ích chß╗ìn (select) cß║ºn ├¡t nhß║Ñt mß╗Öt t├╣y chß╗ìn.",
            "duplicate_field_key": "M├ú tr╞░ß╗¥ng t├╣y chß╗ënh n├áy ─æ├ú tß╗ôn tß║íi cho ─æß╗æi t╞░ß╗úng.",
        }
        return jsonify({"message": msg_map.get(err_code, "Dß╗» liß╗çu khai b├ío ch╞░a hß╗úp lß╗ç.")}), 400


@api.get("/custom-fields/<int:field_id>")
def custom_fields_get(field_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    field = get_custom_field(field_id)
    if not field:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy tr╞░ß╗¥ng t├╣y chß╗ënh."}), 404
    return jsonify(field)


@api.put("/custom-fields/<int:field_id>")
def custom_fields_update(field_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role != "admin":
        return jsonify({"message": "Chß╗ë Quß║ún trß╗ï hß╗ç thß╗æng mß╗¢i c├│ quyß╗ün cß║¡p nhß║¡t tr╞░ß╗¥ng t├╣y chß╗ënh."}), 403

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
        return jsonify({"message": "Cß║¡p nhß║¡t tr╞░ß╗¥ng t├╣y chß╗ënh th├ánh c├┤ng.", "field": field})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy tr╞░ß╗¥ng t├╣y chß╗ënh."}), 404
    except ValueError as e:
        err_code = str(e)
        msg_map = {
            "field_type_invalid": "Kiß╗âu dß╗» liß╗çu phß║úi l├á 'text', 'number', 'date' hoß║╖c 'select'.",
            "field_label_empty": "Vui l├▓ng nhß║¡p t├¬n/nh├ún tr╞░ß╗¥ng.",
            "select_options_empty": "Tr╞░ß╗¥ng kiß╗âu danh s├ích chß╗ìn (select) cß║ºn ├¡t nhß║Ñt mß╗Öt t├╣y chß╗ìn.",
        }
        return jsonify({"message": msg_map.get(err_code, "Dß╗» liß╗çu cß║¡p nhß║¡t ch╞░a hß╗úp lß╗ç.")}), 400


@api.delete("/custom-fields/<int:field_id>")
def custom_fields_delete(field_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role != "admin":
        return jsonify({"message": "Chß╗ë Quß║ún trß╗ï hß╗ç thß╗æng mß╗¢i c├│ quyß╗ün x├│a tr╞░ß╗¥ng t├╣y chß╗ënh."}), 403

    try:
        delete_custom_field(field_id)
        return jsonify({"message": "─É├ú x├│a tr╞░ß╗¥ng t├╣y chß╗ënh v├á c├íc dß╗» liß╗çu li├¬n quan."})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy tr╞░ß╗¥ng t├╣y chß╗ënh."}), 404


# ΓöÇΓöÇΓöÇ Customers Management & Excel Export (SCRUM-66) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

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

    # Lß║Ñy c├íc query param c├│ tiß╗ün tß╗æ 'cf_' l├ám bß╗Ö lß╗ìc tr╞░ß╗¥ng t├╣y chß╗ënh
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
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy kh├ích h├áng."}), 404
    return jsonify(c)


@api.post("/customers")
def customers_create_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    body = _body()
    name = str(body.get("name", "")).strip()
    if not name:
        return jsonify({"message": "Th├┤ng tin ch╞░a hß╗úp lß╗ç.", "errors": {"name": "Vui l├▓ng nhß║¡p t├¬n kh├ích h├áng."}}), 400

    try:
        c = create_customer(
            name=name,
            phone=str(body.get("phone", "")),
            email=str(body.get("email", "")),
            address=str(body.get("address", "")),
            status=str(body.get("status", "Mß╗¢i")),
            created_by=user.id,
            custom_fields=body.get("custom_fields"),
        )
        return jsonify({"message": "Tß║ío mß╗¢i kh├ích h├áng th├ánh c├┤ng.", "customer": c}), 201
    except ValueError as e:
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        return jsonify({"message": "T├¬n kh├ích h├áng kh├┤ng ─æ╞░ß╗úc ─æß╗â trß╗æng."}), 400


@api.put("/customers/<int:customer_id>")
def customers_update_api(customer_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    body = _body()
    name = str(body.get("name", "")).strip()
    if not name:
        return jsonify({"message": "Th├┤ng tin ch╞░a hß╗úp lß╗ç.", "errors": {"name": "Vui l├▓ng nhß║¡p t├¬n kh├ích h├áng."}}), 400

    try:
        c = update_customer(
            customer_id=customer_id,
            name=name,
            phone=str(body.get("phone", "")),
            email=str(body.get("email", "")),
            address=str(body.get("address", "")),
            status=str(body.get("status", "Mß╗¢i")),
            custom_fields=body.get("custom_fields"),
        )
        return jsonify({"message": "Cß║¡p nhß║¡t kh├ích h├áng th├ánh c├┤ng.", "customer": c})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy kh├ích h├áng."}), 404
    except ValueError as e:
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        return jsonify({"message": "Dß╗» liß╗çu ch╞░a hß╗úp lß╗ç."}), 400


@api.delete("/customers/<int:customer_id>")
def customers_delete_api(customer_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    try:
        delete_customer(customer_id)
        return jsonify({"message": "─É├ú x├│a kh├ích h├áng th├ánh c├┤ng."})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy kh├ích h├áng."}), 404


# ΓöÇΓöÇΓöÇ Opportunities Management & Excel Export (SCRUM-66) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

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
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi kinh doanh."}), 404
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
        errors["title"] = "Vui l├▓ng nhß║¡p t├¬n c╞í hß╗Öi."
    if not customer_id:
        errors["customer_id"] = "Vui l├▓ng chß╗ìn kh├ích h├áng."

    if errors:
        return jsonify({"message": "Th├┤ng tin ch╞░a hß╗úp lß╗ç.", "errors": errors}), 400

    try:
        o = create_opportunity(
            title=title,
            customer_id=int(customer_id),
            value=float(body.get("value", 0.0)),
            stage=str(body.get("stage", "Mß╗¢i tß║ío")),
            stage_key=str(body.get("stage_key", "")),
            expected_close_date=str(body.get("expected_close_date", "")),
            meetings_count=int(body.get("meetings_count", 0)),
            win_reason_id=body.get("win_reason_id"),
            loss_reason_id=body.get("loss_reason_id"),
            competitor_id=body.get("competitor_id"),
            created_by=user.id,
            custom_fields=body.get("custom_fields"),
        )
        return jsonify({"message": "Tß║ío mß╗¢i c╞í hß╗Öi th├ánh c├┤ng.", "opportunity": o}), 201
    except ValueError as e:
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        if str(e) == "customer_not_found":
            return jsonify({"message": "Kh├ích h├áng kh├┤ng tß╗ôn tß║íi."}), 404
        return jsonify({"message": "Dß╗» liß╗çu ch╞░a hß╗úp lß╗ç."}), 400


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
        errors["title"] = "Vui l├▓ng nhß║¡p t├¬n c╞í hß╗Öi."
    if not customer_id:
        errors["customer_id"] = "Vui l├▓ng chß╗ìn kh├ích h├áng."

    if errors:
        return jsonify({"message": "Th├┤ng tin ch╞░a hß╗úp lß╗ç.", "errors": errors}), 400

    try:
        o = update_opportunity(
            opportunity_id=opportunity_id,
            title=title,
            customer_id=int(customer_id),
            value=float(body.get("value", 0.0)),
            stage=str(body.get("stage", "Mß╗¢i tß║ío")),
            stage_key=str(body.get("stage_key", "")),
            expected_close_date=str(body.get("expected_close_date", "")),
            meetings_count=int(body.get("meetings_count", 0)),
            win_reason_id=body.get("win_reason_id"),
            loss_reason_id=body.get("loss_reason_id"),
            competitor_id=body.get("competitor_id"),
            custom_fields=body.get("custom_fields"),
        )
        return jsonify({"message": "Cß║¡p nhß║¡t c╞í hß╗Öi th├ánh c├┤ng.", "opportunity": o})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi."}), 404
    except ValueError as e:
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        if str(e) == "customer_not_found":
            return jsonify({"message": "Kh├ích h├áng kh├┤ng tß╗ôn tß║íi."}), 404
        return jsonify({"message": "Dß╗» liß╗çu ch╞░a hß╗úp lß╗ç."}), 400


@api.delete("/opportunities/<int:opportunity_id>")
def opportunities_delete_api(opportunity_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    try:
        delete_opportunity(opportunity_id)
        return jsonify({"message": "─É├ú x├│a c╞í hß╗Öi th├ánh c├┤ng."})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi."}), 404


# ΓöÇΓöÇΓöÇ S2-09: Pipeline Stages & Sales Forecast APIs ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

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
        return jsonify({"message": "Chß╗ë Gi├ím ─æß╗æc kinh doanh hoß║╖c Quß║ún trß╗ï vi├¬n mß╗¢i c├│ quyß╗ün cß║Ñu h├¼nh Pipeline."}), 403

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
        return jsonify({"message": "Cß║Ñu h├¼nh giai ─æoß║ín Pipeline th├ánh c├┤ng.", "stage": stage}), 201
    except ValueError as e:
        err_map = {
            "stage_key_invalid": "M├ú giai ─æoß║ín kh├┤ng hß╗úp lß╗ç.",
            "stage_name_empty": "Vui l├▓ng nhß║¡p t├¬n giai ─æoß║ín.",
            "duplicate_stage_key": "M├ú giai ─æoß║ín n├áy ─æ├ú tß╗ôn tß║íi.",
        }
        return jsonify({"message": err_map.get(str(e), "Dß╗» liß╗çu ch╞░a hß╗úp lß╗ç.")}), 400


@api.get("/pipeline-stages/<int:stage_id>")
def pipeline_stages_get_api(stage_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    s = get_pipeline_stage(stage_id)
    if not s:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy giai ─æoß║ín."}), 404
    return jsonify(s)


@api.put("/pipeline-stages/<int:stage_id>")
def pipeline_stages_update_api(stage_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Chß╗ë Gi├ím ─æß╗æc kinh doanh hoß║╖c Quß║ún trß╗ï vi├¬n mß╗¢i c├│ quyß╗ün cß║Ñu h├¼nh Pipeline."}), 403

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
        return jsonify({"message": "Cß║¡p nhß║¡t giai ─æoß║ín Pipeline th├ánh c├┤ng.", "stage": stage})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy giai ─æoß║ín."}), 404
    except ValueError as e:
        err_map = {"stage_name_empty": "Vui l├▓ng nhß║¡p t├¬n giai ─æoß║ín."}
        return jsonify({"message": err_map.get(str(e), "Dß╗» liß╗çu ch╞░a hß╗úp lß╗ç.")}), 400


@api.delete("/pipeline-stages/<int:stage_id>")
def pipeline_stages_delete_api(stage_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Chß╗ë Gi├ím ─æß╗æc kinh doanh hoß║╖c Quß║ún trß╗ï vi├¬n mß╗¢i c├│ quyß╗ün cß║Ñu h├¼nh Pipeline."}), 403

    try:
        delete_pipeline_stage(stage_id)
        return jsonify({"message": "─É├ú x├│a giai ─æoß║ín Pipeline."})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy giai ─æoß║ín."}), 404


@api.get("/forecast/summary")
def forecast_summary_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    return jsonify(get_sales_forecast_summary())


# ΓöÇΓöÇΓöÇ S2-10: Win/Loss Reasons & Competitors APIs ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

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
        return jsonify({"message": "Chß╗ë Gi├ím ─æß╗æc kinh doanh hoß║╖c Quß║ún trß╗ï vi├¬n mß╗¢i c├│ quyß╗ün khai b├ío danh mß╗Ñc l├╜ do."}), 403

    body = _body()
    try:
        item = create_win_loss_reason(
            reason_type=str(body.get("reason_type", "")),
            reason_code=str(body.get("reason_code", "")),
            reason_title=str(body.get("reason_title", "")),
            description=str(body.get("description", "")),
            is_active=bool(body.get("is_active", True)),
        )
        return jsonify({"message": "Khai b├ío l├╜ do thß║»ng/thua th├ánh c├┤ng.", "reason": item}), 201
    except ValueError as e:
        err_map = {
            "reason_type_invalid": "Loß║íi l├╜ do phß║úi l├á 'win' hoß║╖c 'loss'.",
            "reason_code_invalid": "M├ú l├╜ do kh├┤ng hß╗úp lß╗ç.",
            "reason_title_empty": "Vui l├▓ng nhß║¡p t├¬n/nß╗Öi dung l├╜ do.",
            "duplicate_reason_code": "M├ú l├╜ do n├áy ─æ├ú tß╗ôn tß║íi cho loß║íi ─æ├ú chß╗ìn.",
        }
        return jsonify({"message": err_map.get(str(e), "Dß╗» liß╗çu ch╞░a hß╗úp lß╗ç.")}), 400


@api.put("/win-loss-reasons/<int:reason_id>")
def win_loss_reasons_update_api(reason_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Chß╗ë Gi├ím ─æß╗æc kinh doanh hoß║╖c Quß║ún trß╗ï vi├¬n mß╗¢i c├│ quyß╗ün sß╗¡a l├╜ do."}), 403

    body = _body()
    try:
        item = update_win_loss_reason(
            reason_id=reason_id,
            reason_title=str(body.get("reason_title", "")),
            description=str(body.get("description", "")),
            is_active=bool(body.get("is_active", True)),
        )
        return jsonify({"message": "Cß║¡p nhß║¡t l├╜ do thß║»ng/thua th├ánh c├┤ng.", "reason": item})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy l├╜ do."}), 404
    except ValueError as e:
        err_map = {"reason_title_empty": "Vui l├▓ng nhß║¡p t├¬n l├╜ do."}
        return jsonify({"message": err_map.get(str(e), "Dß╗» liß╗çu ch╞░a hß╗úp lß╗ç.")}), 400


@api.delete("/win-loss-reasons/<int:reason_id>")
def win_loss_reasons_delete_api(reason_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Chß╗ë Gi├ím ─æß╗æc kinh doanh hoß║╖c Quß║ún trß╗ï vi├¬n mß╗¢i c├│ quyß╗ün x├│a l├╜ do."}), 403

    try:
        delete_win_loss_reason(reason_id)
        return jsonify({"message": "─É├ú x├│a l├╜ do thß║»ng/thua."})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy l├╜ do."}), 404


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
        return jsonify({"message": "Chß╗ë Gi├ím ─æß╗æc kinh doanh hoß║╖c Quß║ún trß╗ï vi├¬n mß╗¢i c├│ quyß╗ün khai b├ío ─æß╗æi thß╗º."}), 403

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
        return jsonify({"message": "Khai b├ío ─æß╗æi thß╗º cß║ính tranh th├ánh c├┤ng.", "competitor": comp}), 201
    except ValueError as e:
        err_map = {
            "competitor_code_invalid": "M├ú ─æß╗æi thß╗º kh├┤ng hß╗úp lß╗ç.",
            "competitor_name_empty": "Vui l├▓ng nhß║¡p t├¬n ─æß╗æi thß╗º.",
            "duplicate_competitor_code": "M├ú ─æß╗æi thß╗º n├áy ─æ├ú tß╗ôn tß║íi.",
        }
        return jsonify({"message": err_map.get(str(e), "Dß╗» liß╗çu ch╞░a hß╗úp lß╗ç.")}), 400


@api.get("/competitors/<int:competitor_id>")
def competitors_get_api(competitor_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    comp = get_competitor(competitor_id)
    if not comp:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy ─æß╗æi thß╗º cß║ính tranh."}), 404
    return jsonify(comp)


@api.put("/competitors/<int:competitor_id>")
def competitors_update_api(competitor_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Chß╗ë Gi├ím ─æß╗æc kinh doanh hoß║╖c Quß║ún trß╗ï vi├¬n mß╗¢i c├│ quyß╗ün cß║¡p nhß║¡t ─æß╗æi thß╗º."}), 403

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
        return jsonify({"message": "Cß║¡p nhß║¡t ─æß╗æi thß╗º cß║ính tranh th├ánh c├┤ng.", "competitor": comp})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy ─æß╗æi thß╗º."}), 404
    except ValueError as e:
        err_map = {"competitor_name_empty": "Vui l├▓ng nhß║¡p t├¬n ─æß╗æi thß╗º."}
        return jsonify({"message": err_map.get(str(e), "Dß╗» liß╗çu ch╞░a hß╗úp lß╗ç.")}), 400


@api.delete("/competitors/<int:competitor_id>")
def competitors_delete_api(competitor_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Chß╗ë Gi├ím ─æß╗æc kinh doanh hoß║╖c Quß║ún trß╗ï vi├¬n mß╗¢i c├│ quyß╗ün x├│a ─æß╗æi thß╗º."}), 403

    try:
        delete_competitor(competitor_id)
        return jsonify({"message": "─É├ú x├│a ─æß╗æi thß╗º cß║ính tranh."})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy ─æß╗æi thß╗º."}), 404


# ΓöÇΓöÇΓöÇ SCRUM-75: Customer Multi-Criteria Filter & Saved Filters ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

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

    # Thu thß║¡p c├íc cf_* param nß║┐u c├│
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
        return jsonify({"message": "L╞░u bß╗Ö lß╗ìc th├ánh c├┤ng.", "saved_filter": sf}), 201
    except ValueError as e:
        err_map = {"filter_name_empty": "Vui l├▓ng nhß║¡p t├¬n bß╗Ö lß╗ìc.", "criteria_invalid": "Ti├¬u ch├¡ bß╗Ö lß╗ìc kh├┤ng hß╗úp lß╗ç."}
        return jsonify({"message": err_map.get(str(e), "Dß╗» liß╗çu kh├┤ng hß╗úp lß╗ç.")}), 400


@api.get("/saved-filters/<int:filter_id>")
def saved_filters_get_api(filter_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    sf = get_saved_filter(filter_id, user_id=user.id)
    if not sf:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy bß╗Ö lß╗ìc ─æ├ú l╞░u."}), 404
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
        return jsonify({"message": "Cß║¡p nhß║¡t bß╗Ö lß╗ìc th├ánh c├┤ng.", "saved_filter": sf})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy bß╗Ö lß╗ìc ─æ├ú l╞░u."}), 404
    except ValueError as e:
        err_map = {"filter_name_empty": "Vui l├▓ng nhß║¡p t├¬n bß╗Ö lß╗ìc.", "criteria_invalid": "Ti├¬u ch├¡ bß╗Ö lß╗ìc kh├┤ng hß╗úp lß╗ç."}
        return jsonify({"message": err_map.get(str(e), "Dß╗» liß╗çu kh├┤ng hß╗úp lß╗ç.")}), 400


@api.delete("/saved-filters/<int:filter_id>")
def saved_filters_delete_api(filter_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    try:
        delete_saved_filter(filter_id, user_id=user.id)
        return jsonify({"message": "─É├ú x├│a bß╗Ö lß╗ìc."})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy bß╗Ö lß╗ìc ─æ├ú l╞░u."}), 404


# ΓöÇΓöÇΓöÇ SCRUM-76: Support Tickets & Customer Churn-Risk Flagging Engine ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

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
        return jsonify({"message": "Tß║ío y├¬u cß║ºu hß╗ù trß╗ú th├ánh c├┤ng.", "ticket": ticket}), 201
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy kh├ích h├áng."}), 404
    except ValueError as e:
        err_map = {
            "ticket_title_empty": "Vui l├▓ng nhß║¡p ti├¬u ─æß╗ü y├¬u cß║ºu hß╗ù trß╗ú.",
            "priority_invalid": "Mß╗⌐c ─æß╗Ö ╞░u ti├¬n kh├┤ng hß╗úp lß╗ç (low, medium, high, urgent).",
            "status_invalid": "Trß║íng th├íi kh├┤ng hß╗úp lß╗ç (open, in_progress, resolved, closed).",
        }
        return jsonify({"message": err_map.get(str(e), "Dß╗» liß╗çu ch╞░a hß╗úp lß╗ç.")}), 400


@api.get("/support-tickets/<int:ticket_id>")
def support_tickets_get_api(ticket_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    ticket = get_support_ticket(ticket_id)
    if not ticket:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy y├¬u cß║ºu hß╗ù trß╗ú."}), 404
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
        return jsonify({"message": "Cß║¡p nhß║¡t y├¬u cß║ºu hß╗ù trß╗ú th├ánh c├┤ng.", "ticket": ticket})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy y├¬u cß║ºu hß╗ù trß╗ú."}), 404
    except ValueError as e:
        err_map = {
            "ticket_title_empty": "Vui l├▓ng nhß║¡p ti├¬u ─æß╗ü y├¬u cß║ºu hß╗ù trß╗ú.",
            "priority_invalid": "Mß╗⌐c ─æß╗Ö ╞░u ti├¬n kh├┤ng hß╗úp lß╗ç.",
            "status_invalid": "Trß║íng th├íi kh├┤ng hß╗úp lß╗ç.",
        }
        return jsonify({"message": err_map.get(str(e), "Dß╗» liß╗çu ch╞░a hß╗úp lß╗ç.")}), 400


@api.delete("/support-tickets/<int:ticket_id>")
def support_tickets_delete_api(ticket_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    try:
        delete_support_ticket(ticket_id)
        return jsonify({"message": "─É├ú x├│a y├¬u cß║ºu hß╗ù trß╗ú."})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy y├¬u cß║ºu hß╗ù trß╗ú."}), 404


@api.get("/customers/<int:customer_id>/360")
def customer_360_api(customer_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    cust_360 = get_customer_360(customer_id)
    if not cust_360:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy kh├ích h├áng."}), 404
    return jsonify(cust_360)


@api.get("/churn-risk-alerts")
def churn_risk_alerts_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    alerts = list_churn_risk_alerts()
    return jsonify({"items": alerts})


# ΓöÇΓöÇΓöÇ SCRUM-77: Periodic Customer Care & Interaction Tracking Engine ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

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
            interaction_type=str(body.get("interaction_type", "Gß╗ìi ─æiß╗çn ch─âm s├│c")),
            notes=str(body.get("notes", "")),
            created_by=user.id,
        )
        return jsonify({"message": "─É├ú ghi nhß║¡n t╞░╞íng t├íc ch─âm s├│c kh├ích h├áng.", "interaction": record}), 201
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy kh├ích h├áng."}), 404


@api.post("/customers/<int:customer_id>/mark-contacted")
def customer_mark_contacted_api(customer_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    body = _body()
    try:
        record = record_customer_interaction(
            customer_id=customer_id,
            interaction_type=str(body.get("interaction_type", "─É├ính dß║Ñu ─æ├ú li├¬n hß╗ç ngay")),
            notes=str(body.get("notes", "─É├ú li├¬n hß╗ç trß╗▒c tiß║┐p tß╗½ danh s├ích ch─âm s├│c ─æß╗ïnh kß╗│.")),
            created_by=user.id,
        )
        return jsonify({"message": "─É├ú ─æ├ính dß║Ñu li├¬n hß╗ç kh├ích h├áng th├ánh c├┤ng.", "interaction": record}), 201
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy kh├ích h├áng."}), 404


# ΓöÇΓöÇΓöÇ SCRUM-84: Lead CRUD + Nhß║¡n/Tß╗½ chß╗æi Lead vß╗¢i SLA ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

@api.get("/leads")
def leads_list_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    q = request.args.get("q", "")
    status = request.args.get("status", "")
    source = request.args.get("source", "")
    classification = request.args.get("classification", "")
    assigned_to_str = request.args.get("assigned_to", "")
    assigned_to = int(assigned_to_str) if assigned_to_str.isdigit() else None
    if user.role == "employee" and assigned_to is None:
        assigned_to = user.id
    sla_breached_only = request.args.get("sla_breached_only", "false").lower() == "true"
    date_from_str = request.args.get("date_from", "")
    date_to_str = request.args.get("date_to", "")
    date_from = int(date_from_str) if date_from_str.isdigit() else None
    date_to = int(date_to_str) if date_to_str.isdigit() else None
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    sort_by = request.args.get("sort_by", "created_at")
    order = request.args.get("order", "desc")
    result = list_leads(
        q=q, status=status, source=source, classification=classification,
        assigned_to=assigned_to, sla_breached_only=sla_breached_only,
        date_from=date_from, date_to=date_to,
        page=page, per_page=per_page, sort_by=sort_by, order=order,
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
        return jsonify({"message": "Th├┤ng tin ch╞░a hß╗úp lß╗ç.", "errors": {"full_name": "Vui l├▓ng nhß║¡p t├¬n lead."}}), 400
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
        return jsonify({"message": "Tß║ío lead th├ánh c├┤ng.", "lead": lead}), 201
    except ValueError:
        return jsonify({"message": "Dß╗» liß╗çu ch╞░a hß╗úp lß╗ç."}), 400


@api.get("/leads/<int:lead_id>")
def leads_get_api(lead_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    lead = get_lead(lead_id)
    if not lead:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy lead."}), 404
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
        return jsonify({"message": "Cß║¡p nhß║¡t lead th├ánh c├┤ng.", "lead": lead})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy lead."}), 404
    except ValueError as e:
        err_map = {
            "lead_name_empty": "Vui l├▓ng nhß║¡p t├¬n lead.",
            "lead_already_converted": "Lead ─æ├ú chuyß╗ân ─æß╗òi, kh├┤ng thß╗â chß╗ënh sß╗¡a.",
        }
        return jsonify({"message": err_map.get(str(e), "Dß╗» liß╗çu ch╞░a hß╗úp lß╗ç.")}), 400


@api.delete("/leads/<int:lead_id>")
def leads_delete_api(lead_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Kh├┤ng c├│ quyß╗ün x├│a lead."}), 403
    try:
        delete_lead(lead_id)
        return jsonify({"message": "─É├ú x├│a lead th├ánh c├┤ng."})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy lead."}), 404


@api.post("/leads/<int:lead_id>/assign")
def leads_assign_api(lead_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    if user.role not in {"admin", "manager"}:
        return jsonify({"message": "Chß╗ë Tr╞░ß╗ƒng nh├│m hoß║╖c Quß║ún trß╗ï vi├¬n mß╗¢i c├│ thß╗â ph├ón c├┤ng lead."}), 403
    body = _body()
    assigned_to = body.get("assigned_to")
    if not assigned_to:
        return jsonify({"message": "Vui l├▓ng chß╗ìn nh├ón vi├¬n nhß║¡n lead.", "errors": {"assigned_to": "Bß║»t buß╗Öc."}}), 400
    try:
        lead = assign_lead(lead_id=lead_id, assigned_to=int(assigned_to), assigned_by=user.id)
        return jsonify({"message": "Ph├ón c├┤ng lead th├ánh c├┤ng.", "lead": lead})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy lead."}), 404
    except ValueError:
        return jsonify({"message": "Lead ─æ├ú ─æ╞░ß╗úc chuyß╗ân ─æß╗òi, kh├┤ng thß╗â ph├ón c├┤ng."}), 409


@api.post("/leads/<int:lead_id>/accept")
def leads_accept_api(lead_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    try:
        lead = accept_lead(lead_id=lead_id, user_id=user.id)
        return jsonify({"message": "─É├ú nhß║¡n lead. Lead chuyß╗ân sang trß║íng th├íi ─Éang ch─âm s├│c.", "lead": lead})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy lead."}), 404
    except PermissionError:
        return jsonify({"message": "Lead n├áy kh├┤ng ─æ╞░ß╗úc ph├ón c├┤ng cho bß║ín."}), 403
    except ValueError as e:
        err_map = {"lead_status_not_assignable": "Trß║íng th├íi lead hiß╗çn tß║íi kh├┤ng cho ph├⌐p nhß║¡n."}
        return jsonify({"message": err_map.get(str(e), "Kh├┤ng thß╗â nhß║¡n lead n├áy.")}), 409


@api.post("/leads/<int:lead_id>/reject")
def leads_reject_api(lead_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    body = _body()
    reason = str(body.get("reason", "")).strip()
    if not reason:
        return jsonify({"message": "Vui l├▓ng nhß║¡p l├╜ do tß╗½ chß╗æi.", "errors": {"reason": "L├╜ do tß╗½ chß╗æi l├á bß║»t buß╗Öc."}}), 400
    try:
        lead = reject_lead(lead_id=lead_id, user_id=user.id, reason=reason)
        return jsonify({"message": "─É├ú tß╗½ chß╗æi lead. Lead quay vß╗ü h├áng chß╗¥ ph├ón bß╗ò.", "lead": lead})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy lead."}), 404
    except PermissionError:
        return jsonify({"message": "Lead n├áy kh├┤ng ─æ╞░ß╗úc ph├ón c├┤ng cho bß║ín."}), 403
    except ValueError as e:
        return jsonify({"message": "Trß║íng th├íi lead hiß╗çn tß║íi kh├┤ng cho ph├⌐p tß╗½ chß╗æi."}), 409


@api.get("/leads/<int:lead_id>/activities")
def leads_activities_api(lead_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    lead = get_lead(lead_id)
    if not lead:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy lead."}), 404
    activities = get_lead_activities(lead_id)
    return jsonify({"items": activities})


# ΓöÇΓöÇΓöÇ SCRUM-85: Chuyß╗ân Lead th├ánh Kh├ích h├áng + Ng╞░ß╗¥i li├¬n hß╗ç + C╞í hß╗Öi ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

@api.post("/leads/<int:lead_id>/convert")
def leads_convert_api(lead_id: int):
    """
    Chuyß╗ân lead th├ánh Kh├ích h├áng + Ng╞░ß╗¥i li├¬n hß╗ç + C╞í hß╗Öi b├ín h├áng (SCRUM-85).
    - Mß╗Öt thao t├íc ─æß╗ông thß╗¥i tß║ío cß║ú 3 (─æß╗ông bß╗Ö).
    - Dß╗» liß╗çu lead ─æ╞░ß╗úc chuyß╗ân sang ΓåÆ kh├┤ng phß║úi nhß║¡p lß║íi.
    - Lead chuyß╗ân sang '─É├ú chuyß╗ân ─æß╗òi' v├á bß╗ï kh├│a chß╗ënh sß╗¡a.
    - To├án bß╗Ö hoß║ít ─æß╗Öng lead ─æ╞░ß╗úc giß╗» lß║íi tr├¬n kh├ích h├áng mß╗¢i.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    body = _body()
    try:
        result = convert_lead_to_customer(
            lead_id=lead_id,
            converted_by=user.id,
            company_name=str(body.get("company_name", "") or ""),
            company_phone=str(body.get("company_phone", "") or ""),
            company_email=str(body.get("company_email", "") or ""),
            company_address=str(body.get("company_address", "") or ""),
            opportunity_title=str(body.get("opportunity_title", "") or ""),
            opportunity_value=float(body.get("opportunity_value", 0.0) or 0.0),
            opportunity_stage=str(body.get("opportunity_stage", "Mß╗¢i tß║ío") or "Mß╗¢i tß║ío"),
            opportunity_stage_key=str(body.get("opportunity_stage_key", "new") or "new"),
            opportunity_expected_close_date=str(body.get("opportunity_expected_close_date", "") or ""),
            contact_position=str(body.get("contact_position", "") or ""),
        )
        return jsonify({
            "message": (
                f"Lead ─æ├ú chuyß╗ân ─æß╗òi th├ánh c├┤ng. "
                f"Kh├ích h├áng #{result['customer_id']}, C╞í hß╗Öi #{result['opportunity_id']} ─æ╞░ß╗úc tß║ío."
            ),
            "result": result,
        }), 201
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy lead."}), 404
    except ValueError as e:
        err_map = {"lead_already_converted": "Lead n├áy ─æ├ú ─æ╞░ß╗úc chuyß╗ân ─æß╗òi rß╗ôi, kh├┤ng thß╗â thao t├íc lß║íi."}
        return jsonify({"message": err_map.get(str(e), "Dß╗» liß╗çu kh├┤ng hß╗úp lß╗ç.")}), 409


@api.get("/customers/<int:customer_id>/contacts")
def customer_contacts_api(customer_id: int):
    """Lß║Ñy danh s├ích ng╞░ß╗¥i li├¬n hß╗ç cß╗ºa mß╗Öt kh├ích h├áng doanh nghiß╗çp."""
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp
    contacts = get_lead_contact(customer_id)
    return jsonify({"items": contacts})


# ΓöÇΓöÇΓöÇ Register ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def register_routes(app: Flask) -> None:
    app.before_request(load_current_user)
    app.register_blueprint(api)





