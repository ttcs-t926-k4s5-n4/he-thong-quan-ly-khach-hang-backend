"""
Lõi dùng chung cho mọi feature của epic SCRUM-19 (Lead & Marketing).

Bao gồm: cấu hình hằng số, kết nối SQLite, lược đồ dữ liệu, hàm kiểm tra dữ liệu,
bộ giới hạn tần suất (rate limiter) và các API đọc/cập nhật lead dùng chung.
"""
import json
import os
import re
import sqlite3
import threading
import time
import unicodedata
from collections import deque
from datetime import datetime, timezone

from flask import Blueprint, current_app, g, request

# ---------------------------------------------------------------------------
# Hằng số nghiệp vụ
# ---------------------------------------------------------------------------
LEAD_STATUSES = ["Mới", "Đang liên hệ", "Đủ điều kiện", "Không đạt", "Đã chuyển đổi"]
LEAD_STATUS_NEW = "Mới"
LEAD_STATUS_CONVERTED = "Đã chuyển đổi"
LEAD_STATUS_DISQUALIFIED = "Không đạt"

LEAD_SOURCES = {
    "web_form": "Biểu mẫu website",
    "su_kien": "Sự kiện",
    "hoi_thao": "Hội thảo",
    "danh_thiep": "Danh thiếp",
    "gioi_thieu": "Giới thiệu",
    "quang_cao": "Quảng cáo",
    "khac": "Khác",
}
# "web_form" chỉ được sinh ra bởi biểu mẫu nhúng, không cho nhập tay / nhập Excel
MANUAL_SOURCES = [k for k in LEAD_SOURCES if k != "web_form"]

CAMPAIGN_CHANNELS = {
    "facebook": "Facebook",
    "google_ads": "Google Ads",
    "email": "Email marketing",
    "zalo": "Zalo",
    "website": "Website / SEO",
    "su_kien": "Sự kiện",
    "hoi_thao": "Hội thảo",
    "khac": "Khác",
}

OPPORTUNITY_STAGES = ["Mới", "Đang đàm phán", "Thắng", "Thua"]
STAGE_WON = "Thắng"
STAGE_LOST = "Thua"
OPEN_STAGES = ["Mới", "Đang đàm phán"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS campaigns (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL UNIQUE,
    channel      TEXT    NOT NULL,
    budget       REAL    NOT NULL CHECK (budget >= 0),
    start_date   TEXT    NOT NULL,
    end_date     TEXT    NOT NULL,
    description  TEXT,
    created_by   TEXT,
    created_at   TEXT    NOT NULL,
    updated_at   TEXT    NOT NULL,
    CHECK (end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS web_forms (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT    NOT NULL,
    public_key       TEXT    NOT NULL UNIQUE,
    campaign_id      INTEGER REFERENCES campaigns(id),
    allowed_domains  TEXT    NOT NULL DEFAULT '[]',
    success_message  TEXT    NOT NULL,
    redirect_url     TEXT,
    is_active        INTEGER NOT NULL DEFAULT 1,
    created_by       TEXT,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS import_batches (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name       TEXT    NOT NULL,
    default_source  TEXT,
    source_detail   TEXT,
    campaign_id     INTEGER REFERENCES campaigns(id),
    total_rows      INTEGER NOT NULL,
    valid_rows      INTEGER NOT NULL,
    error_rows      INTEGER NOT NULL,
    imported_count  INTEGER NOT NULL DEFAULT 0,
    status          TEXT    NOT NULL CHECK (status IN ('preview', 'committed')),
    rows_json       TEXT    NOT NULL,
    created_by      TEXT,
    created_at      TEXT    NOT NULL,
    committed_at    TEXT
);

CREATE TABLE IF NOT EXISTS leads (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name        TEXT    NOT NULL,
    email            TEXT,
    phone            TEXT,
    company          TEXT,
    interest         TEXT,
    note             TEXT,
    status           TEXT    NOT NULL DEFAULT 'Mới',
    source           TEXT    NOT NULL CHECK (length(trim(source)) > 0),
    source_detail    TEXT,
    form_id          INTEGER REFERENCES web_forms(id),
    campaign_id      INTEGER REFERENCES campaigns(id),
    import_batch_id  INTEGER REFERENCES import_batches(id),
    ip_address       TEXT,
    created_by       TEXT,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_leads_email    ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_phone    ON leads(phone);
CREATE INDEX IF NOT EXISTS idx_leads_campaign ON leads(campaign_id);
CREATE INDEX IF NOT EXISTS idx_leads_source   ON leads(source);

CREATE TABLE IF NOT EXISTS opportunities (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 TEXT    NOT NULL,
    lead_id              INTEGER REFERENCES leads(id),
    campaign_id          INTEGER REFERENCES campaigns(id),
    stage                TEXT    NOT NULL DEFAULT 'Mới',
    value                REAL    NOT NULL DEFAULT 0 CHECK (value >= 0),
    expected_close_date  TEXT,
    closed_at            TEXT,
    created_by           TEXT,
    created_at           TEXT    NOT NULL,
    updated_at           TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_opps_campaign ON opportunities(campaign_id);
"""


# ---------------------------------------------------------------------------
# Lỗi API
# ---------------------------------------------------------------------------
class ApiError(Exception):
    """Lỗi nghiệp vụ trả về cho client dưới dạng JSON."""

    def __init__(self, status, message, details=None, headers=None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.details = details
        self.headers = headers or {}


# ---------------------------------------------------------------------------
# Cơ sở dữ liệu
# ---------------------------------------------------------------------------
def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def init_db(path):
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DB_PATH"], timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


# ---------------------------------------------------------------------------
# Tiện ích kiểm tra dữ liệu
# ---------------------------------------------------------------------------
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^0\d{9}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def clean_text(value, keep_newlines=False):
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(value).strip()
    if keep_newlines:
        return re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\s+", " ", text)


def normalize_email(value):
    return clean_text(value).lower()


def is_valid_email(value):
    return bool(value) and len(value) <= 254 and bool(EMAIL_RE.match(value))


def normalize_phone(value):
    """Chuẩn hoá số điện thoại Việt Nam về dạng 0xxxxxxxxx."""
    text = clean_text(value)
    if not text:
        return ""
    digits = re.sub(r"[\s.\-()]", "", text)
    if digits.startswith("+84"):
        digits = "0" + digits[3:]
    elif digits.startswith("84") and len(digits) == 11:
        digits = "0" + digits[2:]
    elif re.fullmatch(r"[1-9]\d{8}", digits):
        # Excel thường làm mất số 0 đầu khi cột là kiểu số
        digits = "0" + digits
    return digits


def is_valid_phone(value):
    return bool(PHONE_RE.match(value or ""))


def is_valid_date(value):
    if not isinstance(value, str) or not DATE_RE.match(value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def parse_money(value):
    """Trả về số thực >= 0 hoặc None nếu không hợp lệ."""
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        number = float(str(value).replace(",", "").strip())
    except ValueError:
        return None
    if number != number or number < 0 or number == float("inf"):
        return None
    return round(number, 2)


def strip_accents(text):
    text = (text or "").replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def normalize_key(text):
    return re.sub(r"[^a-z0-9]", "", strip_accents(str(text or "")).lower())


def parse_optional_id(value, field_name):
    if value is None or value == "":
        return None
    try:
        number = int(value)
        if number <= 0:
            raise ValueError
        return number
    except (TypeError, ValueError):
        raise ApiError(422, "Dữ liệu chưa hợp lệ", {field_name: f"{field_name} phải là số nguyên dương"})


# ---------------------------------------------------------------------------
# Request helpers
# ---------------------------------------------------------------------------
def get_json_body():
    data = request.get_json(silent=True)
    if data is None:
        if request.form:
            return request.form.to_dict()
        return {}
    if not isinstance(data, dict):
        raise ApiError(400, "Nội dung gửi lên phải là một đối tượng JSON")
    return data


def current_user():
    return request.headers.get("X-User-Id") or None


def client_ip():
    if current_app.config.get("TRUST_PROXY"):
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def parse_rate(spec):
    """'5/600' -> (5 lần, 600 giây)."""
    count, seconds = str(spec).split("/")
    return int(count), float(seconds)


class SlidingWindowLimiter:
    """Giới hạn tần suất theo cửa sổ trượt, lưu trong bộ nhớ tiến trình."""

    def __init__(self):
        self._hits = {}
        self._lock = threading.Lock()

    def hit(self, key, limit, window_seconds):
        now = time.monotonic()
        with self._lock:
            queue = self._hits.setdefault(key, deque())
            while queue and now - queue[0] >= window_seconds:
                queue.popleft()
            if len(queue) >= limit:
                retry_after = int(window_seconds - (now - queue[0])) + 1
                return False, max(retry_after, 1)
            queue.append(now)
            return True, 0

    def reset(self):
        with self._lock:
            self._hits.clear()


# ---------------------------------------------------------------------------
# Truy vấn dùng chung
# ---------------------------------------------------------------------------
def row_to_dict(row):
    return dict(row) if row is not None else None


def lead_to_dict(row):
    data = dict(row)
    data["source_label"] = LEAD_SOURCES.get(data["source"], data["source"])
    return data


def get_lead_or_404(db, lead_id):
    row = db.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if row is None:
        raise ApiError(404, f"Không tìm thấy lead #{lead_id}")
    return row


def resolve_campaign_id(db, value):
    """Trả về (campaign_id | None, thông báo lỗi | None)."""
    if value is None or value == "":
        return None, None
    try:
        campaign_id = int(value)
    except (TypeError, ValueError):
        return None, "Mã chiến dịch không hợp lệ"
    row = db.execute("SELECT id FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
    if row is None:
        return None, f"Chiến dịch #{campaign_id} không tồn tại"
    return campaign_id, None


def find_duplicate_lead(db, email=None, phone=None):
    conditions, params = [], []
    if email:
        conditions.append("email = ?")
        params.append(email)
    if phone:
        conditions.append("phone = ?")
        params.append(phone)
    if not conditions:
        return None
    sql = f"SELECT id, full_name, email, phone FROM leads WHERE {' OR '.join(conditions)} ORDER BY id LIMIT 1"
    return db.execute(sql, params).fetchone()


def insert_lead(db, data, commit=True):
    """Hàm DUY NHẤT để tạo lead — đảm bảo mọi lead đều có nguồn hợp lệ."""
    source = clean_text(data.get("source"))
    if source not in LEAD_SOURCES:
        raise ApiError(422, "Lead bắt buộc phải có nguồn hợp lệ", {"source": "Thiếu hoặc sai nguồn lead"})
    if not clean_text(data.get("full_name")):
        raise ApiError(422, "Lead bắt buộc phải có họ tên", {"full_name": "Họ tên là bắt buộc"})
    ts = now_iso()
    cur = db.execute(
        """INSERT INTO leads (full_name, email, phone, company, interest, note, status, source,
                              source_detail, form_id, campaign_id, import_batch_id, ip_address,
                              created_by, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            clean_text(data.get("full_name")),
            data.get("email") or None,
            data.get("phone") or None,
            data.get("company") or None,
            data.get("interest") or None,
            data.get("note") or None,
            data.get("status") or LEAD_STATUS_NEW,
            source,
            data.get("source_detail") or None,
            data.get("form_id"),
            data.get("campaign_id"),
            data.get("import_batch_id"),
            data.get("ip_address"),
            data.get("created_by"),
            ts,
            ts,
        ),
    )
    if commit:
        db.commit()
    return cur.lastrowid


# ---------------------------------------------------------------------------
# API dùng chung: danh mục & lead
# ---------------------------------------------------------------------------
core_bp = Blueprint("core", __name__)


@core_bp.get("/api/meta")
def meta():
    return {
        "lead_statuses": LEAD_STATUSES,
        "lead_sources": [{"code": k, "label": v} for k, v in LEAD_SOURCES.items()],
        "manual_sources": [{"code": k, "label": LEAD_SOURCES[k]} for k in MANUAL_SOURCES],
        "campaign_channels": [{"code": k, "label": v} for k, v in CAMPAIGN_CHANNELS.items()],
        "opportunity_stages": OPPORTUNITY_STAGES,
    }


@core_bp.get("/api/leads")
def list_leads():
    db = get_db()
    where, params = [], []
    for field in ("status", "source"):
        value = request.args.get(field)
        if value:
            where.append(f"{field} = ?")
            params.append(value)
    for field in ("campaign_id", "form_id", "import_batch_id"):
        value = request.args.get(field)
        if value == "none":
            where.append(f"{field} IS NULL")
        elif value:
            where.append(f"{field} = ?")
            params.append(parse_optional_id(value, field))
    keyword = clean_text(request.args.get("q"))
    if keyword:
        where.append("(full_name LIKE ? OR email LIKE ? OR phone LIKE ? OR company LIKE ?)")
        params.extend([f"%{keyword}%"] * 4)
    try:
        page = max(int(request.args.get("page", 1)), 1)
        page_size = min(max(int(request.args.get("page_size", 20)), 1), 200)
    except ValueError:
        raise ApiError(400, "page và page_size phải là số nguyên")
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    total = db.execute(f"SELECT COUNT(*) AS n FROM leads {clause}", params).fetchone()["n"]
    rows = db.execute(
        f"SELECT * FROM leads {clause} ORDER BY id DESC LIMIT ? OFFSET ?",
        params + [page_size, (page - 1) * page_size],
    ).fetchall()
    return {"items": [lead_to_dict(r) for r in rows], "total": total, "page": page, "page_size": page_size}


@core_bp.get("/api/leads/<int:lead_id>")
def get_lead(lead_id):
    return lead_to_dict(get_lead_or_404(get_db(), lead_id))


@core_bp.patch("/api/leads/<int:lead_id>")
def update_lead(lead_id):
    db = get_db()
    get_lead_or_404(db, lead_id)
    data = get_json_body()
    locked = [k for k in ("source", "campaign_id", "form_id", "import_batch_id") if k in data]
    if locked:
        raise ApiError(
            422,
            "Không được thay đổi nguồn và chiến dịch gốc đã sinh ra lead",
            {k: "Trường này không được phép sửa" for k in locked},
        )
    updates, errors = {}, {}
    if "status" in data:
        status = clean_text(data.get("status"))
        if status == LEAD_STATUS_CONVERTED:
            errors["status"] = "Hãy dùng chức năng chuyển đổi lead để tạo cơ hội"
        elif status not in LEAD_STATUSES:
            errors["status"] = f"Trạng thái phải là một trong: {', '.join(LEAD_STATUSES)}"
        else:
            updates["status"] = status
    for field, limit in (("company", 200), ("interest", 2000), ("note", 2000)):
        if field in data:
            value = clean_text(data.get(field), keep_newlines=True)
            if len(value) > limit:
                errors[field] = f"Tối đa {limit} ký tự"
            else:
                updates[field] = value or None
    if errors:
        raise ApiError(422, "Dữ liệu chưa hợp lệ", errors)
    if updates:
        updates["updated_at"] = now_iso()
        sets = ", ".join(f"{k} = ?" for k in updates)
        db.execute(f"UPDATE leads SET {sets} WHERE id = ?", list(updates.values()) + [lead_id])
        db.commit()
    return lead_to_dict(get_lead_or_404(db, lead_id))


def dumps(value):
    return json.dumps(value, ensure_ascii=False)
