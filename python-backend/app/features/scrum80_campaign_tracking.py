"""
SCRUM-80 — Là Nhân viên Marketing, tôi muốn theo dõi lead theo từng chiến dịch, để đo được
chiến dịch nào thực sự ra doanh thu chứ không chỉ ra nhiều lead.

Chức năng:
  * Khai báo chiến dịch: tên, kênh, ngân sách, thời gian chạy (bắt đầu - kết thúc).
  * Lead và cơ hội giữ liên kết cố định tới chiến dịch đã sinh ra chúng
    (chuyển đổi lead -> cơ hội kế thừa chiến dịch, không cho sửa chiến dịch gốc).
  * Báo cáo từng chiến dịch: số lead, số cơ hội, giá trị đã chốt, tỷ lệ chuyển đổi, chi phí/lead, ROI.
  * Báo cáo tổng hợp xếp hạng chiến dịch theo doanh thu (không chỉ theo số lead).
"""
from datetime import date

from flask import Blueprint, request

from app.core import (
    CAMPAIGN_CHANNELS,
    LEAD_SOURCES,
    LEAD_STATUS_CONVERTED,
    LEAD_STATUS_DISQUALIFIED,
    OPEN_STAGES,
    OPPORTUNITY_STAGES,
    STAGE_LOST,
    STAGE_WON,
    ApiError,
    clean_text,
    current_user,
    get_db,
    get_json_body,
    get_lead_or_404,
    is_valid_date,
    lead_to_dict,
    now_iso,
    parse_money,
    parse_optional_id,
    resolve_campaign_id,
)

FEATURE = {
    "key": "SCRUM-80",
    "branch": "feature/SCRUM-80-campaign-tracking-backend",
    "name": "Theo dõi lead theo chiến dịch và đo doanh thu",
}

bp = Blueprint("scrum80_campaign_tracking", __name__)
CAMPAIGN_FIELDS = ("name", "channel", "budget", "start_date", "end_date", "description")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def campaign_status(c, today=None):
    today = (today or date.today()).isoformat()
    if today < c["start_date"]:
        return "Sắp chạy"
    if today > c["end_date"]:
        return "Đã kết thúc"
    return "Đang chạy"


def campaign_to_dict(row):
    data = dict(row)
    data["channel_label"] = CAMPAIGN_CHANNELS.get(data["channel"], data["channel"])
    data["status"] = campaign_status(data)
    return data


def get_campaign_or_404(db, campaign_id):
    row = db.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
    if row is None:
        raise ApiError(404, f"Không tìm thấy chiến dịch #{campaign_id}")
    return row


def validate_campaign(data, existing=None):
    merged = dict(existing) if existing else {}
    merged.update({k: data[k] for k in CAMPAIGN_FIELDS if k in data})
    values, errors = {}, {}

    name = clean_text(merged.get("name"))
    if not name:
        errors["name"] = "Tên chiến dịch là bắt buộc"
    elif len(name) > 150:
        errors["name"] = "Tên chiến dịch tối đa 150 ký tự"
    values["name"] = name

    channel = clean_text(merged.get("channel")).lower()
    if channel not in CAMPAIGN_CHANNELS:
        errors["channel"] = f"Kênh phải là một trong: {', '.join(CAMPAIGN_CHANNELS)}"
    values["channel"] = channel

    budget = parse_money(merged.get("budget"))
    if budget is None:
        errors["budget"] = "Ngân sách là bắt buộc và phải là số >= 0"
    values["budget"] = budget

    for field, label in (("start_date", "Ngày bắt đầu"), ("end_date", "Ngày kết thúc")):
        value = clean_text(merged.get(field))
        if not is_valid_date(value):
            errors[field] = f"{label} phải có dạng YYYY-MM-DD"
        values[field] = value
    if "start_date" not in errors and "end_date" not in errors and values["end_date"] < values["start_date"]:
        errors["end_date"] = "Ngày kết thúc phải sau hoặc bằng ngày bắt đầu"

    description = clean_text(merged.get("description"), keep_newlines=True)
    if len(description) > 2000:
        errors["description"] = "Mô tả tối đa 2000 ký tự"
    values["description"] = description or None
    return values, errors


def _pct(part, whole):
    return round(part * 100.0 / whole, 2) if whole else 0.0


def campaign_metrics(db, campaign):
    cid = campaign["id"]
    budget = float(campaign["budget"])
    lead_count = db.execute("SELECT COUNT(*) AS n FROM leads WHERE campaign_id = ?", (cid,)).fetchone()["n"]
    converted = db.execute(
        "SELECT COUNT(*) AS n FROM leads WHERE campaign_id = ? AND status = ?", (cid, LEAD_STATUS_CONVERTED)
    ).fetchone()["n"]
    by_source = db.execute(
        "SELECT source, COUNT(*) AS n FROM leads WHERE campaign_id = ? GROUP BY source ORDER BY n DESC", (cid,)
    ).fetchall()
    placeholders = ",".join("?" * len(OPEN_STAGES))
    opp = db.execute(
        f"""SELECT COUNT(*) AS total,
                   COALESCE(SUM(CASE WHEN stage = ? THEN 1 END), 0) AS won,
                   COALESCE(SUM(CASE WHEN stage = ? THEN 1 END), 0) AS lost,
                   COALESCE(SUM(CASE WHEN stage = ? THEN value END), 0) AS won_value,
                   COALESCE(SUM(CASE WHEN stage IN ({placeholders}) THEN value END), 0) AS pipeline_value
            FROM opportunities WHERE campaign_id = ?""",
        (STAGE_WON, STAGE_LOST, STAGE_WON, *OPEN_STAGES, cid),
    ).fetchone()
    won_value = round(float(opp["won_value"]), 2)
    return {
        "campaign_id": cid,
        "campaign_name": campaign["name"],
        "channel": campaign["channel"],
        "channel_label": CAMPAIGN_CHANNELS.get(campaign["channel"], campaign["channel"]),
        "status": campaign_status(campaign),
        "start_date": campaign["start_date"],
        "end_date": campaign["end_date"],
        "budget": budget,
        "lead_count": lead_count,
        "converted_lead_count": converted,
        "opportunity_count": opp["total"],
        "open_opportunity_count": opp["total"] - opp["won"] - opp["lost"],
        "won_count": opp["won"],
        "lost_count": opp["lost"],
        "won_value": won_value,
        "pipeline_value": round(float(opp["pipeline_value"]), 2),
        "lead_to_opportunity_rate": _pct(opp["total"], lead_count),
        "win_rate": _pct(opp["won"], opp["won"] + opp["lost"]),
        "cost_per_lead": round(budget / lead_count, 2) if lead_count else None,
        "cost_per_won_deal": round(budget / opp["won"], 2) if opp["won"] else None,
        "roi_percent": round((won_value - budget) * 100.0 / budget, 2) if budget else None,
        "leads_by_source": [
            {"source": r["source"], "source_label": LEAD_SOURCES.get(r["source"], r["source"]), "count": r["n"]}
            for r in by_source
        ],
    }


def opportunity_to_dict(row):
    data = dict(row)
    data["is_closed"] = data["stage"] in (STAGE_WON, STAGE_LOST)
    return data


def get_opportunity_or_404(db, opp_id):
    row = db.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,)).fetchone()
    if row is None:
        raise ApiError(404, f"Không tìm thấy cơ hội #{opp_id}")
    return row


def validate_stage_value(stage, value, errors):
    if stage not in OPPORTUNITY_STAGES:
        errors["stage"] = f"Giai đoạn phải là một trong: {', '.join(OPPORTUNITY_STAGES)}"
    if value is None:
        errors["value"] = "Giá trị phải là số >= 0"
    elif stage == STAGE_WON and value <= 0:
        errors["value"] = "Cơ hội đã Thắng phải có giá trị chốt > 0"


# ---------------------------------------------------------------------------
# Chiến dịch
# ---------------------------------------------------------------------------
@bp.post("/api/campaigns")
def create_campaign():
    db = get_db()
    values, errors = validate_campaign(get_json_body())
    if not errors and db.execute("SELECT 1 FROM campaigns WHERE name = ?", (values["name"],)).fetchone():
        raise ApiError(409, f"Chiến dịch '{values['name']}' đã tồn tại")
    if errors:
        raise ApiError(422, "Dữ liệu chiến dịch chưa hợp lệ", errors)
    ts = now_iso()
    cur = db.execute(
        """INSERT INTO campaigns (name, channel, budget, start_date, end_date, description,
                                  created_by, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (values["name"], values["channel"], values["budget"], values["start_date"], values["end_date"],
         values["description"], current_user(), ts, ts),
    )
    db.commit()
    return campaign_to_dict(get_campaign_or_404(db, cur.lastrowid)), 201


@bp.get("/api/campaigns")
def list_campaigns():
    db = get_db()
    where, params = [], []
    channel = request.args.get("channel")
    if channel:
        where.append("channel = ?")
        params.append(channel)
    keyword = clean_text(request.args.get("q"))
    if keyword:
        where.append("name LIKE ?")
        params.append(f"%{keyword}%")
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    items = [campaign_to_dict(r) for r in db.execute(f"SELECT * FROM campaigns {clause} ORDER BY start_date DESC, id DESC", params)]
    status = request.args.get("status")
    if status:
        items = [c for c in items if c["status"] == status]
    return {"items": items, "total": len(items)}


@bp.get("/api/campaigns/<int:campaign_id>")
def get_campaign(campaign_id):
    db = get_db()
    data = campaign_to_dict(get_campaign_or_404(db, campaign_id))
    data["summary"] = campaign_metrics(db, data)
    return data
