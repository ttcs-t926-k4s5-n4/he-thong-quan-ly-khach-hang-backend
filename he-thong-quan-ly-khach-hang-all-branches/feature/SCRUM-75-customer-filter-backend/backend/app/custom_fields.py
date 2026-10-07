"""
app/custom_fields.py — Logic quản lý và xử lý Trường tùy chỉnh (SCRUM-66)
Dành cho Khách hàng (customer) và Cơ hội (opportunity)
"""
import json
import re
import time
from datetime import datetime
from typing import Any

from app.db import fetch_all, fetch_one, get_db

VALID_ENTITY_TYPES = {"customer", "opportunity"}
VALID_FIELD_TYPES = {"text", "number", "date", "select"}


def _now_ms() -> int:
    return int(time.time() * 1000)


def sanitize_field_key(key: str) -> str:
    """Tạo field_key hợp lệ từ chuỗi nhập vào (chữ thường, không dấu, nối bằng _)"""
    key = key.strip().lower()
    key = re.sub(r"[^a-z0-9_]", "_", key)
    key = re.sub(r"_+", "_", key).strip("_")
    return key


def list_custom_fields(entity_type: str | None = None, is_active_only: bool = False) -> list[dict[str, Any]]:
    conn = get_db()
    sql = "SELECT id, entity_type, field_key, field_label, field_type, options, is_required, description, display_order, is_active, created_at, updated_at FROM dbo.custom_field_definitions WHERE 1=1"
    params: list[Any] = []

    if entity_type:
        sql += " AND entity_type = ?"
        params.append(entity_type.lower())

    if is_active_only:
        sql += " AND is_active = 1"

    sql += " ORDER BY entity_type ASC, display_order ASC, id ASC"
    rows = fetch_all(conn, sql, params)

    for row in rows:
        row["is_required"] = bool(row["is_required"])
        row["is_active"] = bool(row["is_active"])
        if row["options"]:
            try:
                row["options"] = json.loads(row["options"])
            except Exception:
                row["options"] = []
        else:
            row["options"] = []

    return rows


def get_custom_field(field_id: int) -> dict[str, Any] | None:
    conn = get_db()
    row = fetch_one(
        conn,
        "SELECT id, entity_type, field_key, field_label, field_type, options, is_required, description, display_order, is_active, created_at, updated_at FROM dbo.custom_field_definitions WHERE id = ?",
        (field_id,),
    )
    if not row:
        return None

    row["is_required"] = bool(row["is_required"])
    row["is_active"] = bool(row["is_active"])
    if row["options"]:
        try:
            row["options"] = json.loads(row["options"])
        except Exception:
            row["options"] = []
    else:
        row["options"] = []
    return row


def create_custom_field(
    entity_type: str,
    field_key: str,
    field_label: str,
    field_type: str,
    options: list[str] | str | None = None,
    is_required: bool = False,
    description: str = "",
    display_order: int = 0,
    is_active: bool = True,
) -> dict[str, Any]:
    entity_type = entity_type.strip().lower()
    if entity_type not in VALID_ENTITY_TYPES:
        raise ValueError("entity_type_invalid")

    clean_key = sanitize_field_key(field_key)
    if not clean_key:
        raise ValueError("field_key_invalid")

    field_type = field_type.strip().lower()
    if field_type not in VALID_FIELD_TYPES:
        raise ValueError("field_type_invalid")

    field_label = field_label.strip()
    if not field_label:
        raise ValueError("field_label_empty")

    # Xử lý options cho kiểu 'select'
    options_json = None
    if field_type == "select":
        if isinstance(options, str):
            opts = [x.strip() for x in options.split(",") if x.strip()]
        elif isinstance(options, list):
            opts = [str(x).strip() for x in options if str(x).strip()]
        else:
            opts = []
        if not opts:
            raise ValueError("select_options_empty")
        options_json = json.dumps(opts, ensure_ascii=False)

    conn = get_db()
    existing = fetch_one(
        conn,
        "SELECT id FROM dbo.custom_field_definitions WHERE entity_type = ? AND field_key = ?",
        (entity_type, clean_key),
    )
    if existing:
        raise ValueError("duplicate_field_key")

    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.custom_field_definitions
        (entity_type, field_key, field_label, field_type, options, is_required, description, display_order, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entity_type,
            clean_key,
            field_label,
            field_type,
            options_json,
            1 if is_required else 0,
            description.strip(),
            int(display_order),
            1 if is_active else 0,
            now,
            now,
        ),
    )
    conn.commit()

    new_field = fetch_one(
        conn,
        "SELECT id FROM dbo.custom_field_definitions WHERE entity_type = ? AND field_key = ?",
        (entity_type, clean_key),
    )
    return get_custom_field(new_field["id"])  # type: ignore


def update_custom_field(
    field_id: int,
    field_label: str,
    field_type: str,
    options: list[str] | str | None = None,
    is_required: bool = False,
    description: str = "",
    display_order: int = 0,
    is_active: bool = True,
) -> dict[str, Any]:
    existing = get_custom_field(field_id)
    if not existing:
        raise LookupError("field_not_found")

    field_type = field_type.strip().lower()
    if field_type not in VALID_FIELD_TYPES:
        raise ValueError("field_type_invalid")

    field_label = field_label.strip()
    if not field_label:
        raise ValueError("field_label_empty")

    options_json = None
    if field_type == "select":
        if isinstance(options, str):
            opts = [x.strip() for x in options.split(",") if x.strip()]
        elif isinstance(options, list):
            opts = [str(x).strip() for x in options if str(x).strip()]
        else:
            opts = []
        if not opts:
            raise ValueError("select_options_empty")
        options_json = json.dumps(opts, ensure_ascii=False)

    conn = get_db()
    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.custom_field_definitions
        SET field_label = ?, field_type = ?, options = ?, is_required = ?, description = ?, display_order = ?, is_active = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            field_label,
            field_type,
            options_json,
            1 if is_required else 0,
            description.strip(),
            int(display_order),
            1 if is_active else 0,
            now,
            field_id,
        ),
    )
    conn.commit()
    return get_custom_field(field_id)  # type: ignore


def delete_custom_field(field_id: int) -> bool:
    conn = get_db()
    existing = get_custom_field(field_id)
    if not existing:
        raise LookupError("field_not_found")

    cur = conn.cursor()
    # Xóa cả giá trị đã lưu
    cur.execute("DELETE FROM dbo.custom_field_values WHERE field_id = ?", (field_id,))
    cur.execute("DELETE FROM dbo.custom_field_definitions WHERE id = ?", (field_id,))
    conn.commit()
    return True


def get_form_schema(entity_type: str) -> list[dict[str, Any]]:
    """Trả về cấu hình biểu mẫu (Form Schema) cho frontend render linh hoạt"""
    fields = list_custom_fields(entity_type=entity_type, is_active_only=True)
    schema = []
    for f in fields:
        schema.append(
            {
                "id": f["id"],
                "key": f["field_key"],
                "label": f["field_label"],
                "type": f["field_type"],
                "options": f["options"],
                "required": f["is_required"],
                "description": f["description"],
                "order": f["display_order"],
            }
        )
    return schema


def validate_custom_fields(
    entity_type: str, custom_fields_input: dict[str, Any]
) -> tuple[bool, dict[str, Any], dict[str, str]]:
    """
    Kiểm tra tính hợp lệ của dữ liệu trường tùy chỉnh:
    - Bắt buộc (is_required)
    - Đúng kiểu dữ liệu (text, number, date ISO, select option)
    Trả về: (is_valid, clean_values, error_dict)
    """
    active_fields = list_custom_fields(entity_type=entity_type, is_active_only=True)

    clean_values: dict[str, Any] = {}
    errors: dict[str, str] = {}

    for f in active_fields:
        key = f["field_key"]
        label = f["field_label"]
        f_type = f["field_type"]
        required = f["is_required"]
        options = f["options"] or []

        val = custom_fields_input.get(key)

        # Kiểm tra bắt buộc
        if required:
            if val is None or str(val).strip() == "":
                errors[key] = f"Trường '{label}' là bắt buộc."
                continue

        if val is None or str(val).strip() == "":
            clean_values[key] = None
            continue

        str_val = str(val).strip()

        # Kiểm tra kiểu dữ liệu
        if f_type == "number":
            try:
                num_val = float(str_val) if "." in str_val else int(str_val)
                clean_values[key] = str_val
            except ValueError:
                errors[key] = f"Trường '{label}' phải là số hợp lệ."
        elif f_type == "date":
            # Chấp nhận định dạng YYYY-MM-DD
            try:
                datetime.strptime(str_val, "%Y-%m-%d")
                clean_values[key] = str_val
            except ValueError:
                errors[key] = f"Trường '{label}' phải có định dạng ngày YYYY-MM-DD."
        elif f_type == "select":
            if str_val not in options:
                opts_str = ", ".join(options)
                errors[key] = f"Gía trị của '{label}' không hợp lệ. Chọn một trong: {opts_str}"
            else:
                clean_values[key] = str_val
        else:  # text
            clean_values[key] = str_val

    is_valid = len(errors) == 0
    return is_valid, clean_values, errors


def save_custom_field_values(conn, entity_type: str, entity_id: int, custom_values: dict[str, Any]) -> None:
    """Lưu các giá trị trường tùy chỉnh cho entity vào database"""
    active_fields = {f["field_key"]: f["id"] for f in list_custom_fields(entity_type=entity_type, is_active_only=True)}
    now = _now_ms()
    cur = conn.cursor()

    for key, val in custom_values.items():
        if key not in active_fields:
            continue
        field_id = active_fields[key]
        str_val = None if val is None else str(val)

        # Upsert: kiểm tra đã tồn tại hay chưa
        existing = fetch_one(
            conn,
            "SELECT id FROM dbo.custom_field_values WHERE entity_type = ? AND entity_id = ? AND field_id = ?",
            (entity_type, entity_id, field_id),
        )
        if existing:
            cur.execute(
                "UPDATE dbo.custom_field_values SET field_value = ?, updated_at = ? WHERE id = ?",
                (str_val, now, existing["id"]),
            )
        else:
            cur.execute(
                "INSERT INTO dbo.custom_field_values (entity_type, entity_id, field_id, field_value, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (entity_type, entity_id, field_id, str_val, now, now),
            )


def batch_get_custom_field_values(conn, entity_type: str, entity_ids: list[int]) -> dict[int, dict[str, Any]]:
    """Lấy toàn bộ các trường tùy chỉnh cho danh sách entity_ids để tối ưu performance"""
    if not entity_ids:
        return {}

    placeholders = ",".join(["?"] * len(entity_ids))
    sql = f"""
        SELECT cfv.entity_id, cfd.field_key, cfv.field_value
        FROM dbo.custom_field_values cfv
        INNER JOIN dbo.custom_field_definitions cfd ON cfv.field_id = cfd.id
        WHERE cfv.entity_type = ? AND cfv.entity_id IN ({placeholders})
    """
    params = [entity_type] + list(entity_ids)
    rows = fetch_all(conn, sql, params)

    result: dict[int, dict[str, Any]] = {eid: {} for eid in entity_ids}
    for r in rows:
        eid = r["entity_id"]
        key = r["field_key"]
        val = r["field_value"]
        if eid in result:
            result[eid][key] = val

    return result
