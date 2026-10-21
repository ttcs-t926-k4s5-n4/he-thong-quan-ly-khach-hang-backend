"""
routes.py ΓÇö Tß║Ñt cß║ú API endpoints cß╗ºa Sprint 1
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
from app.opportunity_filters import (
    create_saved_opportunity_filter,
    delete_saved_opportunity_filter,
    get_saved_opportunity_filter,
    list_saved_opportunity_filters,
    search_and_filter_opportunities,
    update_saved_opportunity_filter,
)
from app.opportunity_history import (
    can_access_opportunity,
    get_opportunity_history,
)
from app.opportunity_shares import (
    check_opportunity_access,
    list_opportunity_shares,
    remove_opportunity_share,
    share_opportunity,
    transfer_opportunity_ownership,
    update_share_permission,
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
from app.opportunity_documents import (
    delete_opportunity_document,
    get_document_by_id,
    get_upload_dir,
    list_opportunity_documents,
    save_single_document,
)
from app.tasks_reminders import (
    create_task,
    get_task_by_id,
    get_team_overdue_summary,
    get_user_reminder_settings,
    list_user_due_soon_tasks,
    list_user_notifications,
    list_user_overdue_tasks,
    mark_all_notifications_as_read,
    mark_notification_as_read,
    process_task_reminders_and_overdue,
    update_task_status,
    update_user_reminder_settings,
)
from app.call_logs import (
    get_call_log_by_id,
    list_customer_call_history,
    record_call_log,
    update_call_log,
)

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
    """
    GET /api/opportunities (SCRUM-66 & SCRUM-96)
    T├¼m kiß║┐m v├á lß╗ìc c╞í hß╗Öi kinh doanh ─æa ti├¬u ch├¡:
    - keyword: T├¼m theo t├¬n, m├ú c╞í hß╗Öi, t├¬n kh├ích h├áng
    - stage: Giai ─æoß║ín kinh doanh
    - min_value, max_value: Khoß║úng gi├í trß╗ï
    - close_date_from, close_date_to: Khoß║úng ng├áy chß╗æt dß╗▒ kiß║┐n
    - product_id: Sß║ún phß║⌐m li├¬n quan
    - owner_id: Ng╞░ß╗¥i sß╗ƒ hß╗»u
    - page, page_size: Ph├ón trang (hß╗ù trß╗ú cß║ú per_page)
    - sort_by, sort_order: Sß║»p xß║┐p
    - cf_*: Tr╞░ß╗¥ng t├╣y chß╗ënh
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    keyword = (request.args.get("keyword") or request.args.get("q") or "").strip()
    stage = request.args.get("stage", "").strip()

    min_val_str = request.args.get("min_value")
    min_val = None
    if min_val_str is not None and str(min_val_str).strip() != "":
        try:
            min_val = float(min_val_str)
        except ValueError:
            return jsonify({"message": "Gi├í trß╗ï tß╗æi thiß╗âu kh├┤ng hß╗úp lß╗ç."}), 400

    max_val_str = request.args.get("max_value")
    max_val = None
    if max_val_str is not None and str(max_val_str).strip() != "":
        try:
            max_val = float(max_val_str)
        except ValueError:
            return jsonify({"message": "Gi├í trß╗ï tß╗æi ─æa kh├┤ng hß╗úp lß╗ç."}), 400

    close_date_from = request.args.get("close_date_from", "").strip()
    close_date_to = request.args.get("close_date_to", "").strip()

    pid_str = request.args.get("product_id")
    product_id = int(pid_str) if pid_str is not None and str(pid_str).strip().isdigit() else None

    oid_str = request.args.get("owner_id")
    owner_id = int(oid_str) if oid_str is not None and str(oid_str).strip().isdigit() else None

    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1

    page_size_arg = request.args.get("page_size") or request.args.get("per_page") or "20"
    try:
        page_size = min(max(int(page_size_arg), 1), 100)
    except ValueError:
        page_size = 20

    sort_by = request.args.get("sort_by", "created_at").strip()
    sort_order = request.args.get("sort_order", "desc").strip()

    cf_filters = {k[3:]: v for k, v in request.args.items() if k.startswith("cf_")}

    try:
        result = search_and_filter_opportunities(
            user=user,
            keyword=keyword,
            stage=stage,
            min_value=min_val,
            max_value=max_val,
            close_date_from=close_date_from,
            close_date_to=close_date_to,
            product_id=product_id,
            owner_id=owner_id,
            cf_filters=cf_filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return jsonify(result)
    except ValueError as e:
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        return jsonify({"message": str(e)}), 400


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

    owner_id_raw = body.get("owner_id")
    owner_id = int(owner_id_raw) if (owner_id_raw is not None and str(owner_id_raw).isdigit()) else user.id

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
            owner_id=owner_id,
            created_by=user.id,
            custom_fields=body.get("custom_fields"),
        )
        return jsonify({"message": "Tß║ío mß╗¢i c╞í hß╗Öi th├ánh c├┤ng.", "opportunity": o}), 201
    except ValueError as e:
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        if str(e) == "customer_not_found":
            return jsonify({"message": "Kh├ích h├áng kh├┤ng tß╗ôn tß║íi."}), 404
        if str(e) == "owner_not_found":
            return jsonify({"message": "Ng╞░ß╗¥i sß╗ƒ hß╗»u kh├┤ng tß╗ôn tß║íi."}), 404
        return jsonify({"message": "Dß╗» liß╗çu ch╞░a hß╗úp lß╗ç."}), 400


@api.put("/opportunities/<int:opportunity_id>")
def opportunities_update_api(opportunity_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    existing = get_opportunity(opportunity_id)
    if not existing:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi."}), 404

    is_allowed, msg = check_opportunity_access(user, existing, required_permission="edit")
    if not is_allowed:
        return jsonify({"message": "Bß║ín kh├┤ng c├│ quyß╗ün chß╗ënh sß╗¡a c╞í hß╗Öi n├áy."}), 403

    body = _body()
    title = str(body.get("title", "")).strip()
    customer_id = body.get("customer_id")
    errors = {}
    if not title:
        errors["title"] = "Vui l├▓ng nhß║¡p t├¬n c╞í hß╗Öi."
    if not customer_id:
        errors["customer_id"] = "Vui l├▓ng chß╗ìn kh├ích h├áng."

    owner_id_raw = body.get("owner_id")
    owner_id = None
    if owner_id_raw is not None and str(owner_id_raw).strip() != "":
        try:
            owner_id = int(owner_id_raw)
        except (ValueError, TypeError):
            errors["owner_id"] = "ID ng╞░ß╗¥i sß╗ƒ hß╗»u kh├┤ng hß╗úp lß╗ç."

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
            owner_id=owner_id,
            custom_fields=body.get("custom_fields"),
            changed_by=user.id,
        )
        return jsonify({"message": "Cß║¡p nhß║¡t c╞í hß╗Öi th├ánh c├┤ng.", "opportunity": o})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi."}), 404
    except ValueError as e:
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        if str(e) == "customer_not_found":
            return jsonify({"message": "Kh├ích h├áng kh├┤ng tß╗ôn tß║íi."}), 404
        if str(e) == "owner_not_found":
            return jsonify({"message": "Ng╞░ß╗¥i sß╗ƒ hß╗»u kh├┤ng tß╗ôn tß║íi."}), 404
        return jsonify({"message": "Dß╗» liß╗çu ch╞░a hß╗úp lß╗ç."}), 400


@api.get("/opportunities/<int:opportunity_id>/history")
def opportunities_history_api(opportunity_id: int):
    """
    GET /api/opportunities/<opportunity_id>/history (SCRUM-95)
    Lß║Ñy lß╗ïch sß╗¡ thay ─æß╗òi cß╗ºa c╞í hß╗Öi: Stage, Value, Expected Close Date, Owner.
    Query parameters:
    - page: Trang cß║ºn lß║Ñy (mß║╖c ─æß╗ïnh: 1)
    - page_size: Sß╗æ bß║ún ghi mß╗ùi trang (mß║╖c ─æß╗ïnh: 20, hß╗ù trß╗ú cß║ú per_page)
    - field: Lß╗ìc theo tr╞░ß╗¥ng thay ─æß╗òi (stage, value, expected_close_date, owner)
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    opp = get_opportunity(opportunity_id)
    if not opp:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi kinh doanh."}), 404

    if not can_access_opportunity(user, opp):
        return jsonify({"message": "Bß║ín kh├┤ng c├│ quyß╗ün truy cß║¡p lß╗ïch sß╗¡ cß╗ºa c╞í hß╗Öi n├áy."}), 403

    try:
        page = int(request.args.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    page_size_arg = request.args.get("page_size") or request.args.get("per_page") or "20"
    try:
        page_size = int(page_size_arg)
    except (ValueError, TypeError):
        page_size = 20

    field = str(request.args.get("field", "")).strip()

    history = get_opportunity_history(
        opportunity_id=opportunity_id,
        field=field,
        page=page,
        page_size=page_size,
    )
    return jsonify(history)


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


# ΓöÇΓöÇΓöÇ Saved Opportunity Filters (SCRUM-96) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

@api.post("/opportunity-filters")
def opportunity_filters_create_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    body = _body()
    name = str(body.get("filter_name", "")).strip()
    if not name:
        name = str(body.get("name", "")).strip()

    config = body.get("filter_config")
    if config is None:
        config = body.get("criteria", {})

    try:
        saved = create_saved_opportunity_filter(
            user_id=user.id,
            filter_name=name,
            filter_config=config,
        )
        return jsonify({"message": "L╞░u bß╗Ö lß╗ìc c╞í hß╗Öi th├ánh c├┤ng.", "filter": saved}), 201
    except ValueError as e:
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        return jsonify({"message": str(e)}), 400


@api.get("/opportunity-filters")
def opportunity_filters_list_api():
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    filters = list_saved_opportunity_filters(user_id=user.id)
    return jsonify({"items": filters})


@api.get("/opportunity-filters/<int:filter_id>")
def opportunity_filters_get_api(filter_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    try:
        f = get_saved_opportunity_filter(filter_id=filter_id, user_id=user.id)
        return jsonify(f)
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy bß╗Ö lß╗ìc c╞í hß╗Öi."}), 404
    except PermissionError:
        return jsonify({"message": "Bß║ín kh├┤ng c├│ quyß╗ün truy cß║¡p bß╗Ö lß╗ìc n├áy."}), 403


@api.put("/opportunity-filters/<int:filter_id>")
def opportunity_filters_update_api(filter_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    body = _body()
    name = str(body.get("filter_name", "")).strip()
    if not name:
        name = str(body.get("name", "")).strip()

    config = body.get("filter_config")
    if config is None:
        config = body.get("criteria", {})

    try:
        updated = update_saved_opportunity_filter(
            filter_id=filter_id,
            user_id=user.id,
            filter_name=name,
            filter_config=config,
        )
        return jsonify({"message": "Cß║¡p nhß║¡t bß╗Ö lß╗ìc th├ánh c├┤ng.", "filter": updated})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy bß╗Ö lß╗ìc c╞í hß╗Öi."}), 404
    except PermissionError:
        return jsonify({"message": "Bß║ín kh├┤ng c├│ quyß╗ün chß╗ënh sß╗¡a bß╗Ö lß╗ìc n├áy."}), 403
    except ValueError as e:
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        return jsonify({"message": str(e)}), 400


@api.delete("/opportunity-filters/<int:filter_id>")
def opportunity_filters_delete_api(filter_id: int):
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    try:
        delete_saved_opportunity_filter(filter_id=filter_id, user_id=user.id)
        return jsonify({"message": "─É├ú x├│a bß╗Ö lß╗ìc c╞í hß╗Öi th├ánh c├┤ng."})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy bß╗Ö lß╗ìc c╞í hß╗Öi."}), 404
    except PermissionError:
        return jsonify({"message": "Bß║ín kh├┤ng c├│ quyß╗ün x├│a bß╗Ö lß╗ìc n├áy."}), 403


# ΓöÇΓöÇΓöÇ Opportunity Sharing & Ownership (SCRUM-97) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

@api.get("/opportunities/<int:opportunity_id>/shares")
def opportunities_shares_list_api(opportunity_id: int):
    """
    GET /api/opportunities/<opportunity_id>/shares (SCRUM-97)
    Lß║Ñy th├┤ng tin Ng╞░ß╗¥i sß╗ƒ hß╗»u ch├¡nh v├á danh s├ích th├ánh vi├¬n ─æ╞░ß╗úc chia sß║╗.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    opp = get_opportunity(opportunity_id)
    if not opp:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi kinh doanh."}), 404

    is_allowed, msg = check_opportunity_access(user, opp, required_permission="read")
    if not is_allowed:
        return jsonify({"message": msg}), 403

    try:
        shares_data = list_opportunity_shares(opportunity_id=opportunity_id)
        return jsonify(shares_data)
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi kinh doanh."}), 404


@api.post("/opportunities/<int:opportunity_id>/shares")
def opportunities_shares_create_api(opportunity_id: int):
    """
    POST /api/opportunities/<opportunity_id>/shares (SCRUM-97)
    Chia sß║╗ c╞í hß╗Öi kinh doanh cho th├ánh vi├¬n mß╗¢i.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    opp = get_opportunity(opportunity_id)
    if not opp:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi kinh doanh."}), 404

    is_allowed, msg = check_opportunity_access(user, opp, required_permission="share")
    if not is_allowed:
        return jsonify({"message": msg}), 403

    body = _body()
    target_user_id = body.get("user_id")
    if not target_user_id:
        return jsonify({"message": "Vui l├▓ng chß╗ìn th├ánh vi├¬n cß║ºn chia sß║╗."}), 400

    permission_level = str(body.get("permission_level", "read")).strip().lower()

    try:
        result = share_opportunity(
            opportunity_id=opportunity_id,
            user_id=int(target_user_id),
            permission_level=permission_level,
            shared_by=user.id,
        )
        return jsonify({"message": "Chia sß║╗ c╞í hß╗Öi th├ánh c├┤ng.", "data": result}), 201
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi kinh doanh."}), 404
    except ValueError as e:
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        return jsonify({"message": str(e)}), 400


@api.patch("/opportunities/<int:opportunity_id>/shares/<int:target_user_id>")
def opportunities_shares_update_api(opportunity_id: int, target_user_id: int):
    """
    PATCH /api/opportunities/<opportunity_id>/shares/<target_user_id> (SCRUM-97)
    Cß║¡p nhß║¡t quyß╗ün chia sß║╗ cß╗ºa th├ánh vi├¬n ('read', 'edit', 'manage').
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    opp = get_opportunity(opportunity_id)
    if not opp:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi kinh doanh."}), 404

    is_allowed, msg = check_opportunity_access(user, opp, required_permission="share")
    if not is_allowed:
        return jsonify({"message": msg}), 403

    body = _body()
    permission_level = str(body.get("permission_level", "")).strip().lower()
    if not permission_level:
        return jsonify({"message": "Vui l├▓ng cung cß║Ñp quyß╗ün chia sß║╗ mß╗¢i."}), 400

    try:
        result = update_share_permission(
            opportunity_id=opportunity_id,
            user_id=target_user_id,
            permission_level=permission_level,
            updated_by=user.id,
        )
        return jsonify({"message": "Cß║¡p nhß║¡t quyß╗ün chia sß║╗ th├ánh c├┤ng.", "data": result})
    except LookupError as e:
        if str(e) == "opportunity_not_found":
            return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi kinh doanh."}), 404
        return jsonify({"message": "Th├ánh vi├¬n ch╞░a ─æ╞░ß╗úc chia sß║╗ c╞í hß╗Öi n├áy."}), 404
    except ValueError as e:
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        return jsonify({"message": str(e)}), 400


@api.delete("/opportunities/<int:opportunity_id>/shares/<int:target_user_id>")
def opportunities_shares_delete_api(opportunity_id: int, target_user_id: int):
    """
    DELETE /api/opportunities/<opportunity_id>/shares/<target_user_id> (SCRUM-97)
    Gß╗í quyß╗ün chia sß║╗ cß╗ºa th├ánh vi├¬n khß╗Åi c╞í hß╗Öi.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    opp = get_opportunity(opportunity_id)
    if not opp:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi kinh doanh."}), 404

    is_self = (user.id == target_user_id)
    if not is_self:
        is_allowed, msg = check_opportunity_access(user, opp, required_permission="share")
        if not is_allowed:
            return jsonify({"message": msg}), 403

    try:
        remove_opportunity_share(opportunity_id=opportunity_id, user_id=target_user_id, removed_by=user.id)
        return jsonify({"message": "─É├ú gß╗í quyß╗ün chia sß║╗ cß╗ºa th├ánh vi├¬n th├ánh c├┤ng."})
    except LookupError:
        return jsonify({"message": "Th├ánh vi├¬n ch╞░a ─æ╞░ß╗úc chia sß║╗ c╞í hß╗Öi n├áy."}), 404


@api.post("/opportunities/<int:opportunity_id>/transfer-ownership")
def opportunities_transfer_ownership_api(opportunity_id: int):
    """
    POST /api/opportunities/<opportunity_id>/transfer-ownership (SCRUM-97)
    Chuyß╗ân quyß╗ün sß╗ƒ hß╗»u ch├¡nh cß╗ºa c╞í hß╗Öi (Primary Owner / Manager / Admin).
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    opp = get_opportunity(opportunity_id)
    if not opp:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi kinh doanh."}), 404

    is_allowed, msg = check_opportunity_access(user, opp, required_permission="transfer")
    if not is_allowed:
        return jsonify({"message": msg}), 403

    body = _body()
    new_owner_id_raw = body.get("new_owner_id")
    if not new_owner_id_raw:
        return jsonify({"message": "Vui l├▓ng chß╗ìn chß╗º sß╗ƒ hß╗»u mß╗¢i."}), 400

    try:
        new_owner_id = int(new_owner_id_raw)
    except (ValueError, TypeError):
        return jsonify({"message": "ID chß╗º sß╗ƒ hß╗»u mß╗¢i kh├┤ng hß╗úp lß╗ç."}), 400

    try:
        result = transfer_opportunity_ownership(
            opportunity_id=opportunity_id,
            new_owner_id=new_owner_id,
            transferred_by=user.id,
        )
        return jsonify({"message": "Chuyß╗ân quyß╗ün sß╗ƒ hß╗»u c╞í hß╗Öi th├ánh c├┤ng.", "data": result})
    except LookupError:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi kinh doanh."}), 404
    except ValueError as e:
        if isinstance(e.args[0], dict):
            return jsonify(e.args[0]), 400
        return jsonify({"message": str(e)}), 400


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


# =============================================================================
# SCRUM-98: ─É├ìNH K├êM T├ÇI LIß╗åU V├ÇO C╞á Hß╗ÿI (OPPORTUNITY DOCUMENTS)
# =============================================================================

@api.post("/opportunities/<int:opportunity_id>/documents")
def opportunity_upload_documents_api(opportunity_id: int):
    """
    POST /api/opportunities/<opportunity_id>/documents (SCRUM-98)
    Tß║úi l├¬n mß╗Öt hoß║╖c nhiß╗üu t├ái liß╗çu ─æ├¡nh k├¿m v├áo c╞í hß╗Öi kinh doanh.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    opp = get_opportunity(opportunity_id)
    if not opp:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi kinh doanh."}), 404

    is_allowed, msg = check_opportunity_access(user, opp, required_permission="edit")
    if not is_allowed:
        return jsonify({"message": msg}), 403

    uploaded_files = []
    if "files" in request.files:
        uploaded_files = request.files.getlist("files")
    elif "documents" in request.files:
        uploaded_files = request.files.getlist("documents")
    elif "file" in request.files:
        uploaded_files = [request.files.get("file")]

    if not uploaded_files:
        return jsonify({"message": "Vui l├▓ng chß╗ìn ├¡t nhß║Ñt mß╗Öt file t├ái liß╗çu ─æß╗â tß║úi l├¬n."}), 400

    saved_documents = []
    errors = []

    for f in uploaded_files:
        if not f or not f.filename:
            continue
        try:
            f.seek(0, 2)  # os.SEEK_END
            size = f.tell()
            f.seek(0)

            doc_info = save_single_document(
                opportunity_id=opportunity_id,
                file_storage_or_data=f,
                original_name=f.filename,
                file_size=size,
                mime_type=f.mimetype,
                uploaded_by=user.id,
            )
            saved_documents.append(doc_info)
        except ValueError as ve:
            errors.append(f"{f.filename}: {str(ve)}")
        except Exception as ex:
            errors.append(f"{f.filename}: Lß╗ùi khi l╞░u t├ái liß╗çu ({str(ex)})")

    if not saved_documents and errors:
        return jsonify({"message": "Kh├┤ng thß╗â tß║úi l├¬n t├ái liß╗çu.", "errors": errors}), 400

    return jsonify({
        "message": f"─É├ú tß║úi l├¬n th├ánh c├┤ng {len(saved_documents)} t├ái liß╗çu.",
        "documents": saved_documents,
        "errors": errors if errors else None,
    }), 201


@api.get("/opportunities/<int:opportunity_id>/documents")
def opportunity_list_documents_api(opportunity_id: int):
    """
    GET /api/opportunities/<opportunity_id>/documents (SCRUM-98)
    Lß║Ñy danh s├ích t├ái liß╗çu ─æ├¡nh k├¿m cß╗ºa c╞í hß╗Öi, sß║»p xß║┐p theo thß╗¥i gian mß╗¢i nhß║Ñt.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    opp = get_opportunity(opportunity_id)
    if not opp:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi kinh doanh."}), 404

    is_allowed, msg = check_opportunity_access(user, opp, required_permission="read")
    if not is_allowed:
        return jsonify({"message": msg}), 403

    docs = list_opportunity_documents(opportunity_id)
    return jsonify({
        "opportunity_id": opportunity_id,
        "total": len(docs),
        "documents": docs,
    })


@api.get("/documents/<int:document_id>/download")
def document_download_api(document_id: int):
    """
    GET /api/documents/<document_id>/download (SCRUM-98)
    Tß║úi xuß╗æng file t├ái liß╗çu sau khi x├íc thß╗▒c quyß╗ün truy cß║¡p c╞í hß╗Öi.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    doc = get_document_by_id(document_id)
    if not doc:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy t├ái liß╗çu y├¬u cß║ºu."}), 404

    opp = get_opportunity(doc["opportunity_id"])
    if not opp:
        return jsonify({"message": "C╞í hß╗Öi li├¬n kß║┐t vß╗¢i t├ái liß╗çu n├áy kh├┤ng tß╗ôn tß║íi."}), 404

    is_allowed, msg = check_opportunity_access(user, opp, required_permission="read")
    if not is_allowed:
        return jsonify({"message": "Bß║ín kh├┤ng c├│ quyß╗ün tß║úi xuß╗æng t├ái liß╗çu n├áy."}), 403

    upload_dir = get_upload_dir()
    full_path = os.path.join(upload_dir, doc["stored_filename"])
    if not os.path.exists(full_path):
        return jsonify({"message": "Tß║¡p tin kh├┤ng tß╗ôn tß║íi tr├¬n m├íy chß╗º l╞░u trß╗»."}), 404

    return send_file(
        full_path,
        as_attachment=True,
        download_name=doc["original_name"],
        mimetype=doc["mime_type"],
    )


@api.delete("/documents/<int:document_id>")
def document_delete_api(document_id: int):
    """
    DELETE /api/documents/<document_id> (SCRUM-98)
    X├│a t├ái liß╗çu ─æ├¡nh k├¿m (ng╞░ß╗¥i tß║úi l├¬n, chß╗º c╞í hß╗Öi hoß║╖c quß║ún l├╜).
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    doc = get_document_by_id(document_id)
    if not doc:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy t├ái liß╗çu."}), 404

    opp = get_opportunity(doc["opportunity_id"])
    if not opp:
        return jsonify({"message": "C╞í hß╗Öi li├¬n kß║┐t vß╗¢i t├ái liß╗çu kh├┤ng tß╗ôn tß║íi."}), 404

    if user.id != doc["uploaded_by"]:
        is_allowed, msg = check_opportunity_access(user, opp, required_permission="manage")
        if not is_allowed:
            return jsonify({"message": "Bß║ín kh├┤ng c├│ quyß╗ün x├│a t├ái liß╗çu n├áy."}), 403

    delete_opportunity_document(document_id, deleted_by=user.id)
    return jsonify({"message": "─É├ú x├│a t├ái liß╗çu th├ánh c├┤ng."})


# =============================================================================
# SCRUM-103: NHß║«C VIß╗åC Sß║«P ─Éß║╛N Hß║áN & VIß╗åC QU├ü Hß║áN (TASKS & REMINDERS)
# =============================================================================

@api.get("/tasks/reminders")
def tasks_reminders_list_api():
    """
    GET /api/tasks/reminders (SCRUM-103)
    Lß║Ñy danh s├ích c├┤ng viß╗çc sß║»p ─æß║┐n hß║ín cß╗ºa ng╞░ß╗¥i d├╣ng hiß╗çn tß║íi.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    reminders = list_user_due_soon_tasks(user.id)
    return jsonify({
        "total": len(reminders),
        "reminders": reminders,
    })


@api.get("/tasks/overdue")
def tasks_overdue_list_api():
    """
    GET /api/tasks/overdue (SCRUM-103)
    Lß║Ñy danh s├ích c├┤ng viß╗çc qu├í hß║ín cß╗ºa ng╞░ß╗¥i d├╣ng hiß╗çn tß║íi ─æß╗â hiß╗ân thß╗ï nß╗òi bß║¡t.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    overdue_tasks = list_user_overdue_tasks(user.id)
    return jsonify({
        "total": len(overdue_tasks),
        "overdue_tasks": overdue_tasks,
    })


@api.get("/notifications")
def notifications_list_api():
    """
    GET /api/notifications (SCRUM-103)
    Lß║Ñy danh s├ích th├┤ng b├ío cß╗ºa ng╞░ß╗¥i d├╣ng vß╗¢i ph├ón trang v├á lß╗ìc ch╞░a ─æß╗ìc.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))
    unread_only = request.args.get("unread_only", "").lower() in {"1", "true", "yes"}

    data = list_user_notifications(user.id, page=page, per_page=per_page, unread_only=unread_only)
    return jsonify(data)


@api.patch("/notifications/<int:notification_id>/read")
def notification_mark_read_api(notification_id: int):
    """
    PATCH /api/notifications/<notification_id>/read (SCRUM-103)
    ─É├ính dß║Ñu th├┤ng b├ío l├á ─æ├ú ─æß╗ìc.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    success = mark_notification_as_read(notification_id, user.id)
    if not success:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy th├┤ng b├ío hoß║╖c bß║ín kh├┤ng c├│ quyß╗ün."}), 404

    return jsonify({"message": "─É├ú ─æ├ính dß║Ñu th├┤ng b├ío ─æ├ú ─æß╗ìc."})


@api.patch("/notifications/mark-all-read")
def notifications_mark_all_read_api():
    """
    PATCH /api/notifications/mark-all-read (SCRUM-103)
    ─É├ính dß║Ñu tß║Ñt cß║ú th├┤ng b├ío cß╗ºa ng╞░ß╗¥i d├╣ng l├á ─æ├ú ─æß╗ìc.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    count = mark_all_notifications_as_read(user.id)
    return jsonify({"message": f"─É├ú ─æ├ính dß║Ñu {count} th├┤ng b├ío l├á ─æ├ú ─æß╗ìc."})


@api.get("/teams/overdue-summary")
def teams_overdue_summary_api():
    """
    GET /api/teams/overdue-summary (SCRUM-103)
    Thß╗æng k├¬ tß╗òng sß╗æ c├┤ng viß╗çc qu├í hß║ín theo tß╗½ng th├ánh vi├¬n (Tr╞░ß╗ƒng nh├│m / Quß║ún trß╗ï vi├¬n).
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    try:
        summary = get_team_overdue_summary(user)
        return jsonify({
            "total_members": len(summary),
            "members": summary,
        })
    except PermissionError as pe:
        return jsonify({"message": str(pe)}), 403


@api.get("/tasks/reminder-settings")
def tasks_reminder_settings_get_api():
    """
    GET /api/tasks/reminder-settings (SCRUM-103)
    Lß║Ñy cß║Ñu h├¼nh c├íc mß╗æc nhß║»c tr╞░ß╗¢c hß║ín cß╗ºa ng╞░ß╗¥i d├╣ng.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    milestones = get_user_reminder_settings(user.id)
    return jsonify({"user_id": user.id, "milestones": milestones})


@api.put("/tasks/reminder-settings")
def tasks_reminder_settings_update_api():
    """
    PUT /api/tasks/reminder-settings (SCRUM-103)
    Cß║¡p nhß║¡t c├íc mß╗æc nhß║»c tr╞░ß╗¢c hß║ín cho ng╞░ß╗¥i d├╣ng.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    body = _body()
    milestones = body.get("milestones")
    if not isinstance(milestones, list):
        return jsonify({"message": "Tr╞░ß╗¥ng 'milestones' phß║úi l├á mß╗Öt danh s├ích chuß╗ùi, v├¡ dß╗Ñ: ['24h', '1h']."}), 400

    updated = update_user_reminder_settings(user.id, milestones)
    return jsonify({"message": "Cß║¡p nhß║¡t cß║Ñu h├¼nh nhß║»c viß╗çc th├ánh c├┤ng.", "milestones": updated})


@api.post("/tasks")
def tasks_create_api():
    """
    POST /api/tasks (SCRUM-103)
    Tß║ío mß╗¢i mß╗Öt c├┤ng viß╗çc trong hß╗ç thß╗æng CRM.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    body = _body()
    title = str(body.get("title", "")).strip()
    if not title:
        return jsonify({"message": "Ti├¬u ─æß╗ü c├┤ng viß╗çc kh├┤ng ─æ╞░ß╗úc ─æß╗â trß╗æng."}), 400

    due_date = body.get("due_date")
    if not due_date:
        return jsonify({"message": "Vui l├▓ng nhß║¡p thß╗¥i hß║ín ho├án th├ánh (due_date)."}), 400

    assigned_to = int(body.get("assigned_to", user.id))
    customer_id = body.get("customer_id")
    opportunity_id = body.get("opportunity_id")
    priority = str(body.get("priority", "medium")).strip().lower()
    description = str(body.get("description", "")).strip()

    try:
        task = create_task(
            title=title,
            due_date=int(due_date),
            assigned_to=assigned_to,
            created_by=user.id,
            description=description,
            customer_id=int(customer_id) if customer_id else None,
            opportunity_id=int(opportunity_id) if opportunity_id else None,
            priority=priority,
            status=str(body.get("status", "pending")),
        )
        return jsonify({"message": "Tß║ío c├┤ng viß╗çc th├ánh c├┤ng.", "task": task}), 201
    except ValueError as ve:
        return jsonify({"message": str(ve)}), 400


@api.get("/tasks/<int:task_id>")
def tasks_get_api(task_id: int):
    """GET /api/tasks/<task_id>"""
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    task = get_task_by_id(task_id)
    if not task:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c├┤ng viß╗çc."}), 404
    return jsonify(task)


@api.patch("/tasks/<int:task_id>/status")
def tasks_update_status_api(task_id: int):
    """PATCH /api/tasks/<task_id>/status"""
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    body = _body()
    status = str(body.get("status", "")).strip().lower()
    if not status:
        return jsonify({"message": "Vui l├▓ng cung cß║Ñp trß║íng th├íi mß╗¢i."}), 400

    updated = update_task_status(task_id, status)
    if not updated:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy c├┤ng viß╗çc."}), 404
    return jsonify({"message": "Cß║¡p nhß║¡t trß║íng th├íi c├┤ng viß╗çc th├ánh c├┤ng.", "task": updated})


# =============================================================================
# SCRUM-104: GHI NHANH Kß║╛T QUß║ó CUß╗ÿC Gß╗îI (CALL LOGS & QUICK RECORD)
# =============================================================================

@api.post("/calls")
def calls_record_api():
    """
    POST /api/calls (SCRUM-104)
    Ghi nhanh kß║┐t quß║ú cuß╗Öc gß╗ìi ngay tr├¬n ─æiß╗çn thoß║íi (tß╗▒ ─æß╗Öng li├¬n kß║┐t c╞í hß╗Öi mß╗ƒ gß║ºn nhß║Ñt).
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    body = _body()
    customer_id = body.get("customer_id")
    if not customer_id:
        return jsonify({"message": "Vui l├▓ng chß╗ìn kh├ích h├áng ─æ╞░ß╗úc li├¬n hß╗ç."}), 400

    call_result = body.get("call_result")
    if not call_result:
        return jsonify({"message": "Vui l├▓ng chß╗ìn kß║┐t quß║ú cuß╗Öc gß╗ìi."}), 400

    notes = body.get("notes", "")
    opportunity_id = body.get("opportunity_id")
    called_at = body.get("called_at")
    callback_at = body.get("callback_at")

    try:
        record = record_call_log(
            customer_id=int(customer_id),
            call_result=str(call_result),
            user_id=user.id,
            user_role=user.role,
            notes=str(notes) if notes else "",
            opportunity_id=int(opportunity_id) if opportunity_id else None,
            called_at=int(called_at) if called_at else None,
            callback_at=int(callback_at) if callback_at else None,
        )
        return jsonify({
            "message": "Ghi nhß║¡n kß║┐t quß║ú cuß╗Öc gß╗ìi th├ánh c├┤ng.",
            "call_log": record,
        }), 201
    except ValueError as ve:
        return jsonify({"message": str(ve)}), 400


@api.get("/customers/<int:customer_id>/calls")
def customers_calls_history_api(customer_id: int):
    """
    GET /api/customers/<customer_id>/calls (SCRUM-104)
    Lß║Ñy lß╗ïch sß╗¡ cuß╗Öc gß╗ìi cß╗ºa kh├ích h├áng vß╗¢i ph├ón trang v├á bß╗Ö lß╗ìc.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))
    call_result = request.args.get("call_result")
    from_date = request.args.get("from_date", type=int)
    to_date = request.args.get("to_date", type=int)
    user_id_param = request.args.get("user_id", type=int)

    final_user_id = user_id_param if user.role in {"admin", "manager"} else user_id_param

    data = list_customer_call_history(
        customer_id=customer_id,
        user_id=final_user_id,
        call_result=call_result,
        from_date=from_date,
        to_date=to_date,
        page=page,
        per_page=per_page,
    )
    return jsonify(data)


@api.get("/calls/<int:call_id>")
def calls_get_api(call_id: int):
    """
    GET /api/calls/<call_id> (SCRUM-104)
    Xem chi tiß║┐t bß║ún ghi cuß╗Öc gß╗ìi.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    record = get_call_log_by_id(call_id)
    if not record:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy bß║ún ghi cuß╗Öc gß╗ìi."}), 404

    if user.role not in {"admin", "manager"} and record["user_id"] != user.id:
        return jsonify({"message": "Bß║ín kh├┤ng c├│ quyß╗ün xem bß║ún ghi cuß╗Öc gß╗ìi cß╗ºa ng╞░ß╗¥i kh├íc."}), 403

    return jsonify(record)


@api.patch("/calls/<int:call_id>")
def calls_update_api(call_id: int):
    """
    PATCH /api/calls/<call_id> (SCRUM-104)
    Cß║¡p nhß║¡t th├┤ng tin bß║ún ghi cuß╗Öc gß╗ìi.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    body = _body()
    try:
        updated = update_call_log(
            call_id=call_id,
            user_id=user.id,
            user_role=user.role,
            notes=body.get("notes"),
            call_result=body.get("call_result"),
            callback_at=body.get("callback_at"),
        )
        return jsonify({"message": "Cß║¡p nhß║¡t bß║ún ghi cuß╗Öc gß╗ìi th├ánh c├┤ng.", "call_log": updated})
    except LookupError as le:
        return jsonify({"message": str(le)}), 404
    except PermissionError as pe:
        return jsonify({"message": str(pe)}), 403
    except ValueError as ve:
        return jsonify({"message": str(ve)}), 400


@api.post("/calls/<int:call_id>/callback-task")
def calls_create_callback_task_api(call_id: int):
    """
    POST /api/calls/<call_id>/callback-task (SCRUM-104)
    Tß║ío hoß║╖c li├¬n kß║┐t c├┤ng viß╗çc gß╗ìi lß║íi cho bß║ún ghi cuß╗Öc gß╗ìi.
    """
    user, err_resp = _require_auth()
    if err_resp:
        return err_resp

    record = get_call_log_by_id(call_id)
    if not record:
        return jsonify({"message": "Kh├┤ng t├¼m thß║Ñy bß║ún ghi cuß╗Öc gß╗ìi."}), 404

    body = _body()
    callback_at = body.get("callback_at") or record.get("callback_at")
    if not callback_at:
        return jsonify({"message": "Vui l├▓ng cung cß║Ñp thß╗¥i ─æiß╗âm gß╗ìi lß║íi (callback_at)."}), 400

    task_title = f"Gß╗ìi lß║íi cho kh├ích h├áng: {record['customer_name']}"
    task = create_task(
        title=task_title,
        due_date=int(callback_at),
        assigned_to=user.id,
        created_by=user.id,
        description=f"Cuß╗Öc gß╗ìi l├║c {record['called_at']}. Ghi ch├║: {record['notes']}",
        customer_id=record["customer_id"],
        opportunity_id=record["opportunity_id"],
        priority="high",
    )
    return jsonify({"message": "Tß║ío c├┤ng viß╗çc gß╗ìi lß║íi th├ánh c├┤ng.", "task": task}), 201


# ΓöÇΓöÇΓöÇ Register ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def register_routes(app: Flask) -> None:
    app.before_request(load_current_user)
    app.register_blueprint(api)






