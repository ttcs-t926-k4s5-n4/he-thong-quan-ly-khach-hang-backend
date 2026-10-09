"""
SCRUM-79 — Là Nhân viên Marketing, tôi muốn tạo lead thủ công và nhập lead hàng loạt từ Excel,
để đưa danh sách thu được từ hội thảo vào hệ thống ngay hôm sau.

Chức năng:
  * Nhập tay một lead (từ sự kiện, danh thiếp...) — bắt buộc có nguồn, cảnh báo trùng.
  * Tải tệp mẫu Excel.
  * Nhập hàng loạt 2 bước: (1) xem trước + báo lỗi theo từng dòng, (2) xác nhận nhập.
  * Mọi lead nhập vào đều bắt buộc có nguồn (cột "Nguồn" hoặc nguồn mặc định của lô).
"""
import csv
import io
import json
import os
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, current_app, request, send_file
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill

from app.core import (
    LEAD_SOURCES,
    LEAD_STATUS_NEW,
    MANUAL_SOURCES,
    ApiError,
    clean_text,
    current_user,
    find_duplicate_lead,
    get_db,
    get_json_body,
    get_lead_or_404,
    insert_lead,
    is_valid_email,
    is_valid_phone,
    lead_to_dict,
    normalize_email,
    normalize_key,
    normalize_phone,
    now_iso,
    resolve_campaign_id,
)

FEATURE = {
    "key": "SCRUM-79",
    "branch": "feature/SCRUM-79-lead-import-excel-backend",
    "name": "Tạo lead thủ công và nhập lead hàng loạt từ Excel",
}

bp = Blueprint("scrum79_lead_import", __name__)

TEMPLATE_HEADERS = ["Họ tên*", "Email", "Số điện thoại", "Công ty", "Nhu cầu quan tâm", "Nguồn", "Chi tiết nguồn", "Ghi chú"]

HEADER_ALIASES = {
    "full_name": ["hoten", "hovaten", "ten", "tenkhachhang", "fullname", "name"],
    "email": ["email", "thudientu", "mail"],
    "phone": ["sodienthoai", "sdt", "dienthoai", "phone", "mobile", "didong"],
    "company": ["congty", "tencongty", "company", "donvi"],
    "interest": ["nhucauquantam", "nhucau", "quantam", "interest"],
    "source": ["nguon", "nguonlead", "source"],
    "source_detail": ["chitietnguon", "tensukien", "sukien", "sourcedetail"],
    "note": ["ghichu", "note"],
}
HEADER_LOOKUP = {alias: field for field, aliases in HEADER_ALIASES.items() for alias in aliases}
SOURCE_LOOKUP = {}
for _code in MANUAL_SOURCES:
    SOURCE_LOOKUP[normalize_key(_code)] = _code
    SOURCE_LOOKUP[normalize_key(LEAD_SOURCES[_code])] = _code
SOURCE_HINT = ", ".join(LEAD_SOURCES[c] for c in MANUAL_SOURCES)
FIELD_LIMITS = {"company": 200, "interest": 2000, "note": 2000, "source_detail": 200}


# ---------------------------------------------------------------------------
# Kiểm tra dữ liệu một lead (dùng chung cho nhập tay và từng dòng Excel)
# ---------------------------------------------------------------------------
def validate_lead_input(raw, default_source="", default_detail=""):
    values, errors = {}, {}
    full_name = clean_text(raw.get("full_name"))
    if not full_name:
        errors["full_name"] = "Họ tên là bắt buộc"
    elif len(full_name) > 150:
        errors["full_name"] = "Họ tên tối đa 150 ký tự"
    values["full_name"] = full_name

    email = normalize_email(raw.get("email"))
    if email and not is_valid_email(email):
        errors["email"] = f"Email '{email}' không hợp lệ"
    values["email"] = email

    phone_raw = clean_text(raw.get("phone"))
    phone = normalize_phone(phone_raw)
    if phone_raw and not is_valid_phone(phone):
        errors["phone"] = f"Số điện thoại '{phone_raw}' không hợp lệ (VD: 0912345678)"
    values["phone"] = phone if phone_raw else ""

    if not email and not phone_raw:
        errors["contact"] = "Cần ít nhất email hoặc số điện thoại"

    for field, limit in FIELD_LIMITS.items():
        value = clean_text(raw.get(field), keep_newlines=field in ("interest", "note"))
        if len(value) > limit:
            errors[field] = f"Tối đa {limit} ký tự"
        values[field] = value

    source_raw = clean_text(raw.get("source")) or clean_text(default_source)
    values["source"] = ""
    if not source_raw:
        errors["source"] = f"Nguồn là bắt buộc. Chọn một trong: {SOURCE_HINT}"
    else:
        code = SOURCE_LOOKUP.get(normalize_key(source_raw))
        if code is None:
            errors["source"] = f"Nguồn '{source_raw}' không hợp lệ. Chọn một trong: {SOURCE_HINT}"
        values["source"] = code or source_raw
    if not values["source_detail"]:
        values["source_detail"] = clean_text(default_detail)
    return values, errors


def _truthy(value):
    return value is True or str(value).strip().lower() in ("1", "true", "yes", "co", "có")


# ---------------------------------------------------------------------------
# Nhập tay một lead
# ---------------------------------------------------------------------------
@bp.post("/api/leads")
def create_lead():
    db = get_db()
    data = get_json_body()
    values, errors = validate_lead_input(data)
    campaign_id, campaign_err = resolve_campaign_id(db, data.get("campaign_id"))
    if campaign_err:
        errors["campaign_id"] = campaign_err
    if errors:
        raise ApiError(422, "Dữ liệu lead chưa hợp lệ", errors)

    duplicate = find_duplicate_lead(db, values["email"], values["phone"])
    if duplicate and not _truthy(data.get("allow_duplicate")):
        raise ApiError(
            409,
            f"Lead đã tồn tại (#{duplicate['id']} - {duplicate['full_name']}). "
            "Gửi allow_duplicate=true nếu vẫn muốn tạo.",
            {"duplicate_lead_id": duplicate["id"]},
        )
    lead_id = insert_lead(db, {**values, "status": LEAD_STATUS_NEW, "campaign_id": campaign_id,
                               "created_by": current_user()})
    return lead_to_dict(get_lead_or_404(db, lead_id)), 201


# ---------------------------------------------------------------------------
# Tệp mẫu
# ---------------------------------------------------------------------------
@bp.get("/api/leads/import/template")
def download_template():
    wb = Workbook()
    ws = wb.active
    ws.title = "Danh sách lead"
    ws.append(TEMPLATE_HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F6FEB")
    for col, width in zip("ABCDEFGH", (26, 30, 16, 28, 40, 16, 28, 30)):
        ws.column_dimensions[col].width = width
    ws.column_dimensions["C"].number_format = "@"   # giữ số 0 đầu của SĐT
    ws.freeze_panes = "A2"

    guide = wb.create_sheet("Hướng dẫn")
    guide.append(["Hướng dẫn nhập lead"])
    guide["A1"].font = Font(bold=True, size=13)
    for line in [
        "1. Điền dữ liệu từ dòng 2 của sheet 'Danh sách lead', không đổi tên cột.",
        "2. Bắt buộc: Họ tên và ít nhất một trong Email / Số điện thoại.",
        "3. Cột Nguồn: để trống nếu đã chọn nguồn mặc định khi tải tệp lên.",
        "4. Hệ thống sẽ xem trước và báo lỗi theo từng dòng trước khi nhập thật.",
        "",
        "Giá trị hợp lệ cho cột Nguồn:",
    ]:
        guide.append([line])
    for code in MANUAL_SOURCES:
        guide.append([LEAD_SOURCES[code], code])
    guide.column_dimensions["A"].width = 70

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="mau-nhap-lead.xlsx",
    )


# ---------------------------------------------------------------------------
# Đọc tệp
# ---------------------------------------------------------------------------
def cell_to_text(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")
    return str(value).strip()


def read_table(content, ext):
    if ext == ".csv":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("cp1258", errors="replace")
        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        return [[cell_to_text(c) for c in row] for row in csv.reader(io.StringIO(text), dialect)]
    wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    try:
        ws = wb.worksheets[0]
        return [[cell_to_text(c) for c in row] for row in ws.iter_rows(values_only=True)]
    finally:
        wb.close()


def batch_to_dict(row, include_rows=True):
    data = dict(row)
    rows = json.loads(data.pop("rows_json"))
    data["source_label"] = LEAD_SOURCES.get(data["default_source"] or "", None)
    data["expires_at"] = _expires_at(data["created_at"]).strftime("%Y-%m-%dT%H:%M:%SZ")
    if include_rows:
        data["rows"] = rows
        data["errors"] = [
            {"row_number": r["row_number"], **err} for r in rows for err in r["errors"]
        ]
    return data


def _expires_at(created_at):
    created = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return created + timedelta(minutes=current_app.config["IMPORT_PREVIEW_TTL_MINUTES"])


# ---------------------------------------------------------------------------
# Bước 1: tải tệp lên & xem trước
# ---------------------------------------------------------------------------
@bp.post("/api/leads/import/preview")
def import_preview():
    db = get_db()
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        raise ApiError(400, "Vui lòng chọn tệp Excel (.xlsx) hoặc CSV ở trường 'file'")
    ext = os.path.splitext(upload.filename)[1].lower()
    if ext not in (".xlsx", ".xlsm", ".csv"):
        raise ApiError(400, "Chỉ hỗ trợ tệp .xlsx hoặc .csv")
    content = upload.read()
    if not content:
        raise ApiError(400, "Tệp rỗng")

    errors = {}
    default_source = clean_text(request.form.get("default_source"))
    if default_source:
        code = SOURCE_LOOKUP.get(normalize_key(default_source))
        if code is None:
            errors["default_source"] = f"Nguồn mặc định không hợp lệ. Chọn một trong: {SOURCE_HINT}"
        default_source = code or ""
    default_detail = clean_text(request.form.get("source_detail"))
    campaign_id, campaign_err = resolve_campaign_id(db, request.form.get("campaign_id"))
    if campaign_err:
        errors["campaign_id"] = campaign_err
    if errors:
        raise ApiError(422, "Thông tin lô nhập chưa hợp lệ", errors)

    try:
        table = read_table(content, ext)
    except Exception:
        raise ApiError(400, "Không đọc được tệp. Hãy dùng đúng tệp mẫu (.xlsx) hoặc CSV UTF-8.")
    if not table:
        raise ApiError(400, "Tệp không có dữ liệu")

    mapping, ignored = {}, []
    for index, header in enumerate(table[0]):
        field = HEADER_LOOKUP.get(normalize_key(header))
        if field and field not in mapping.values():
            mapping[index] = field
        elif clean_text(header):
            ignored.append(clean_text(header))
    fields = set(mapping.values())
    if "full_name" not in fields:
        raise ApiError(400, "Thiếu cột bắt buộc 'Họ tên'. Hãy tải tệp mẫu để dùng đúng định dạng.")
    if "email" not in fields and "phone" not in fields:
        raise ApiError(400, "Tệp cần có ít nhất cột 'Email' hoặc 'Số điện thoại'")

    data_rows = [(n, row) for n, row in enumerate(table[1:], start=2) if any(clean_text(c) for c in row)]
    if not data_rows:
        raise ApiError(400, "Tệp không có dòng dữ liệu nào")
    max_rows = current_app.config["MAX_IMPORT_ROWS"]
    if len(data_rows) > max_rows:
        raise ApiError(400, f"Mỗi lần chỉ nhập tối đa {max_rows} dòng (tệp có {len(data_rows)} dòng)")

    seen_email, seen_phone, results = {}, {}, []
    for row_number, row in data_rows:
        raw = {field: (row[i] if i < len(row) else "") for i, field in mapping.items()}
        values, errs = validate_lead_input(raw, default_source, default_detail)
        row_errors = [{"field": k, "message": m} for k, m in errs.items()]
        email = values["email"] if "email" not in errs else ""
        phone = values["phone"] if "phone" not in errs else ""
        if email:
            if email in seen_email:
                row_errors.append({"field": "email", "message": f"Email trùng với dòng {seen_email[email]} trong tệp"})
            else:
                seen_email[email] = row_number
        if phone:
            if phone in seen_phone:
                row_errors.append({"field": "phone", "message": f"SĐT trùng với dòng {seen_phone[phone]} trong tệp"})
            else:
                seen_phone[phone] = row_number
        duplicate = find_duplicate_lead(db, email, phone)
        if duplicate:
            row_errors.append({
                "field": "email" if email and duplicate["email"] == email else "phone",
                "message": f"Đã tồn tại trong hệ thống (lead #{duplicate['id']} - {duplicate['full_name']})",
            })
        values["source_label"] = LEAD_SOURCES.get(values["source"])
        results.append({"row_number": row_number, "valid": not row_errors, "data": values, "errors": row_errors})

    valid_count = sum(1 for r in results if r["valid"])
    cur = db.execute(
        """INSERT INTO import_batches (file_name, default_source, source_detail, campaign_id, total_rows,
                                       valid_rows, error_rows, status, rows_json, created_by, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'preview', ?, ?, ?)""",
        (upload.filename, default_source or None, default_detail or None, campaign_id, len(results),
         valid_count, len(results) - valid_count, json.dumps(results, ensure_ascii=False), current_user(), now_iso()),
    )
    db.commit()
    batch = db.execute("SELECT * FROM import_batches WHERE id = ?", (cur.lastrowid,)).fetchone()
    body = batch_to_dict(batch)
    body["preview_id"] = body["id"]
    body["ignored_columns"] = ignored
    body["message"] = (
        f"Đọc được {len(results)} dòng: {valid_count} hợp lệ, {len(results) - valid_count} lỗi. "
        "Kiểm tra rồi gọi API xác nhận để nhập."
    )
    return body, 201


@bp.get("/api/leads/import/<int:batch_id>")
def get_batch(batch_id):
    row = get_db().execute("SELECT * FROM import_batches WHERE id = ?", (batch_id,)).fetchone()
    if row is None:
        raise ApiError(404, f"Không tìm thấy lô nhập #{batch_id}")
    return batch_to_dict(row)


# ---------------------------------------------------------------------------
# Bước 2: xác nhận nhập
# ---------------------------------------------------------------------------
@bp.post("/api/leads/import/<int:batch_id>/commit")
def import_commit(batch_id):
    db = get_db()
    batch = db.execute("SELECT * FROM import_batches WHERE id = ?", (batch_id,)).fetchone()
    if batch is None:
        raise ApiError(404, f"Không tìm thấy lô nhập #{batch_id}")
    if batch["status"] == "committed":
        raise ApiError(409, "Lô nhập này đã được xác nhận trước đó")
    if datetime.now(timezone.utc) > _expires_at(batch["created_at"]):
        raise ApiError(410, "Bản xem trước đã hết hạn, vui lòng tải tệp lên lại")

    body = get_json_body()
    mode = clean_text(body.get("mode")) or "valid_only"
    if mode not in ("valid_only", "all_or_nothing"):
        raise ApiError(422, "mode phải là 'valid_only' hoặc 'all_or_nothing'")
    if mode == "all_or_nothing" and batch["error_rows"] > 0:
        raise ApiError(422, f"Tệp còn {batch['error_rows']} dòng lỗi. Sửa tệp hoặc dùng mode 'valid_only'.")

    rows = json.loads(batch["rows_json"])
    imported, skipped = [], []
    try:
        cur = db.execute(
            "UPDATE import_batches SET status = 'committed', committed_at = ? WHERE id = ? AND status = 'preview'",
            (now_iso(), batch_id),
        )
        if cur.rowcount == 0:
            raise ApiError(409, "Lô nhập này đã được xác nhận trước đó")
        for row in rows:
            if not row["valid"]:
                skipped.append({"row_number": row["row_number"], "reason": "; ".join(e["message"] for e in row["errors"])})
                continue
            data = row["data"]
            duplicate = find_duplicate_lead(db, data["email"], data["phone"])
            if duplicate:
                skipped.append({"row_number": row["row_number"],
                                "reason": f"Đã tồn tại trong hệ thống (lead #{duplicate['id']})"})
                continue
            lead_id = insert_lead(db, {
                **data,
                "status": LEAD_STATUS_NEW,
                "campaign_id": batch["campaign_id"],
                "import_batch_id": batch_id,
                "created_by": current_user(),
            }, commit=False)
            imported.append({"row_number": row["row_number"], "lead_id": lead_id})
        db.execute("UPDATE import_batches SET imported_count = ? WHERE id = ?", (len(imported), batch_id))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "message": f"Đã nhập {len(imported)} lead, bỏ qua {len(skipped)} dòng.",
        "batch_id": batch_id,
        "imported_count": len(imported),
        "skipped_count": len(skipped),
        "imported": imported,
        "skipped": skipped,
    }, 201
