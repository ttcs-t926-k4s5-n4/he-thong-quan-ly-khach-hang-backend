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


@bp.patch("/api/campaigns/<int:campaign_id>")
def update_campaign(campaign_id):
    db = get_db()
    existing = get_campaign_or_404(db, campaign_id)
    values, errors = validate_campaign(get_json_body(), existing=existing)
    if not errors and db.execute(
        "SELECT 1 FROM campaigns WHERE name = ? AND id <> ?", (values["name"], campaign_id)
    ).fetchone():
        raise ApiError(409, f"Chiến dịch '{values['name']}' đã tồn tại")
    if errors:
        raise ApiError(422, "Dữ liệu chiến dịch chưa hợp lệ", errors)
    values["updated_at"] = now_iso()
    sets = ", ".join(f"{k} = ?" for k in values)
    db.execute(f"UPDATE campaigns SET {sets} WHERE id = ?", list(values.values()) + [campaign_id])
    db.commit()
    return campaign_to_dict(get_campaign_or_404(db, campaign_id))


@bp.get("/api/campaigns/<int:campaign_id>/leads")
def campaign_leads(campaign_id):
    db = get_db()
    get_campaign_or_404(db, campaign_id)
    rows = db.execute("SELECT * FROM leads WHERE campaign_id = ? ORDER BY id DESC", (campaign_id,)).fetchall()
    return {"items": [lead_to_dict(r) for r in rows], "total": len(rows)}


@bp.get("/api/campaigns/<int:campaign_id>/report")
def campaign_report(campaign_id):
    db = get_db()
    campaign = campaign_to_dict(get_campaign_or_404(db, campaign_id))
    return campaign_metrics(db, campaign)


@bp.get("/api/reports/campaigns")
def campaigns_report():
    db = get_db()
    sort = request.args.get("sort", "won_value")
    if sort not in ("won_value", "roi_percent", "lead_count", "opportunity_count", "win_rate"):
        raise ApiError(400, "sort phải là won_value | roi_percent | lead_count | opportunity_count | win_rate")
    where, params = [], []
    channel = request.args.get("channel")
    if channel:
        where.append("channel = ?")
        params.append(channel)
    date_from, date_to = request.args.get("from"), request.args.get("to")
    for value in (date_from, date_to):
        if value and not is_valid_date(value):
            raise ApiError(400, "from/to phải có dạng YYYY-MM-DD")
    if date_from:
        where.append("end_date >= ?")
        params.append(date_from)
    if date_to:
        where.append("start_date <= ?")
        params.append(date_to)
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    campaigns = db.execute(f"SELECT * FROM campaigns {clause}", params).fetchall()
    items = [campaign_metrics(db, dict(c)) for c in campaigns]
    items.sort(key=lambda m: (m[sort] if m[sort] is not None else float("-inf"), m["won_value"]), reverse=True)
    for rank, item in enumerate(items, start=1):
        item["rank"] = rank

    unassigned_leads = db.execute("SELECT COUNT(*) AS n FROM leads WHERE campaign_id IS NULL").fetchone()["n"]
    unassigned_value = db.execute(
        "SELECT COALESCE(SUM(value), 0) AS v FROM opportunities WHERE campaign_id IS NULL AND stage = ?", (STAGE_WON,)
    ).fetchone()["v"]
    total_budget = sum(i["budget"] for i in items)
    total_won = sum(i["won_value"] for i in items)
    top_revenue = max(items, key=lambda m: m["won_value"], default=None)
    top_leads = max(items, key=lambda m: m["lead_count"], default=None)
    insight = None
    if top_revenue and top_leads and top_revenue["won_value"] > 0 and top_revenue["campaign_id"] != top_leads["campaign_id"]:
        insight = (f"'{top_leads['campaign_name']}' ra nhiều lead nhất ({top_leads['lead_count']}) nhưng "
                   f"'{top_revenue['campaign_name']}' mới là chiến dịch ra doanh thu cao nhất "
                   f"({top_revenue['won_value']:,.0f}).")
    return {
        "sort": sort,
        "items": items,
        "totals": {
            "campaign_count": len(items),
            "budget": round(total_budget, 2),
            "lead_count": sum(i["lead_count"] for i in items),
            "opportunity_count": sum(i["opportunity_count"] for i in items),
            "won_value": round(total_won, 2),
            "roi_percent": round((total_won - total_budget) * 100.0 / total_budget, 2) if total_budget else None,
        },
        "top_by_revenue": top_revenue["campaign_id"] if top_revenue and top_revenue["won_value"] > 0 else None,
        "top_by_leads": top_leads["campaign_id"] if top_leads and top_leads["lead_count"] > 0 else None,
        "insight": insight,
        "unassigned": {"lead_count": unassigned_leads, "won_value": round(float(unassigned_value), 2)},
    }


# ---------------------------------------------------------------------------
# Chuyển đổi lead -> cơ hội & quản lý cơ hội
# ---------------------------------------------------------------------------
@bp.post("/api/leads/<int:lead_id>/convert")
def convert_lead(lead_id):
    db = get_db()
    lead = get_lead_or_404(db, lead_id)
    if lead["status"] == LEAD_STATUS_CONVERTED:
        raise ApiError(409, "Lead này đã được chuyển đổi thành cơ hội")
    if lead["status"] == LEAD_STATUS_DISQUALIFIED:
        raise ApiError(409, "Lead ở trạng thái 'Không đạt' không thể chuyển đổi")
    data = get_json_body()
    if "campaign_id" in data:
        raise ApiError(422, "Cơ hội tự kế thừa chiến dịch của lead, không được chỉ định chiến dịch khác",
                       {"campaign_id": "Không được phép gửi trường này"})
    errors = {}
    name = clean_text(data.get("name")) or f"Cơ hội - {lead['company'] or lead['full_name']}"
    if len(name) > 200:
        errors["name"] = "Tên cơ hội tối đa 200 ký tự"
    value = parse_money(data.get("value", 0))
    stage = clean_text(data.get("stage")) or OPPORTUNITY_STAGES[0]
    validate_stage_value(stage, value, errors)
    close_date = clean_text(data.get("expected_close_date"))
    if close_date and not is_valid_date(close_date):
        errors["expected_close_date"] = "Ngày dự kiến chốt phải có dạng YYYY-MM-DD"
    if errors:
        raise ApiError(422, "Dữ liệu cơ hội chưa hợp lệ", errors)
    ts = now_iso()
    try:
        cur = db.execute(
            """INSERT INTO opportunities (name, lead_id, campaign_id, stage, value, expected_close_date,
                                          closed_at, created_by, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, lead_id, lead["campaign_id"], stage, value, close_date or None,
             ts if stage in (STAGE_WON, STAGE_LOST) else None, current_user(), ts, ts),
        )
        db.execute("UPDATE leads SET status = ?, updated_at = ? WHERE id = ?", (LEAD_STATUS_CONVERTED, ts, lead_id))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "message": "Đã chuyển đổi lead thành cơ hội",
        "opportunity": opportunity_to_dict(get_opportunity_or_404(db, cur.lastrowid)),
        "lead": lead_to_dict(get_lead_or_404(db, lead_id)),
    }, 201


@bp.post("/api/opportunities")
def create_opportunity():
    db = get_db()
    data = get_json_body()
    errors = {}
    name = clean_text(data.get("name"))
    if not name:
        errors["name"] = "Tên cơ hội là bắt buộc"
    lead_id = parse_optional_id(data.get("lead_id"), "lead_id")
    campaign_id, campaign_err = resolve_campaign_id(db, data.get("campaign_id"))
    if campaign_err:
        errors["campaign_id"] = campaign_err
    if lead_id:
        lead = get_lead_or_404(db, lead_id)
        if data.get("campaign_id") not in (None, "") and campaign_id != lead["campaign_id"]:
            errors["campaign_id"] = "Chiến dịch của cơ hội phải trùng với chiến dịch đã sinh ra lead"
        campaign_id = lead["campaign_id"]
    value = parse_money(data.get("value", 0))
    stage = clean_text(data.get("stage")) or OPPORTUNITY_STAGES[0]
    validate_stage_value(stage, value, errors)
    close_date = clean_text(data.get("expected_close_date"))
    if close_date and not is_valid_date(close_date):
        errors["expected_close_date"] = "Ngày dự kiến chốt phải có dạng YYYY-MM-DD"
    if errors:
        raise ApiError(422, "Dữ liệu cơ hội chưa hợp lệ", errors)
    ts = now_iso()
    cur = db.execute(
        """INSERT INTO opportunities (name, lead_id, campaign_id, stage, value, expected_close_date,
                                      closed_at, created_by, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, lead_id, campaign_id, stage, value, close_date or None,
         ts if stage in (STAGE_WON, STAGE_LOST) else None, current_user(), ts, ts),
    )
    db.commit()
    return opportunity_to_dict(get_opportunity_or_404(db, cur.lastrowid)), 201


@bp.get("/api/opportunities")
def list_opportunities():
    db = get_db()
    where, params = [], []
    for field in ("campaign_id", "lead_id"):
        value = request.args.get(field)
        if value:
            where.append(f"{field} = ?")
            params.append(parse_optional_id(value, field))
    stage = request.args.get("stage")
    if stage:
        where.append("stage = ?")
        params.append(stage)
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    rows = db.execute(f"SELECT * FROM opportunities {clause} ORDER BY id DESC", params).fetchall()
    return {"items": [opportunity_to_dict(r) for r in rows], "total": len(rows)}


@bp.get("/api/opportunities/<int:opp_id>")
def get_opportunity(opp_id):
    return opportunity_to_dict(get_opportunity_or_404(get_db(), opp_id))


@bp.patch("/api/opportunities/<int:opp_id>")
def update_opportunity(opp_id):
    db = get_db()
    current = get_opportunity_or_404(db, opp_id)
    data = get_json_body()
    locked = [k for k in ("campaign_id", "lead_id") if k in data]
    if locked:
        raise ApiError(422, "Không được thay đổi chiến dịch / lead gốc của cơ hội",
                       {k: "Trường này không được phép sửa" for k in locked})
    errors = {}
    name = clean_text(data["name"]) if "name" in data else current["name"]
    if not name:
        errors["name"] = "Tên cơ hội là bắt buộc"
    stage = clean_text(data["stage"]) if "stage" in data else current["stage"]
    value = parse_money(data["value"]) if "value" in data else current["value"]
    validate_stage_value(stage, value, errors)
    close_date = clean_text(data["expected_close_date"]) if "expected_close_date" in data else current["expected_close_date"]
    if close_date and not is_valid_date(close_date):
        errors["expected_close_date"] = "Ngày dự kiến chốt phải có dạng YYYY-MM-DD"
    if errors:
        raise ApiError(422, "Dữ liệu cơ hội chưa hợp lệ", errors)
    ts = now_iso()
    closed_at = current["closed_at"]
    if stage in (STAGE_WON, STAGE_LOST) and current["stage"] != stage:
        closed_at = ts
    elif stage not in (STAGE_WON, STAGE_LOST):
        closed_at = None
    db.execute(
        """UPDATE opportunities SET name = ?, stage = ?, value = ?, expected_close_date = ?, closed_at = ?, updated_at = ?
           WHERE id = ?""",
        (name, stage, value, close_date or None, closed_at, ts, opp_id),
    )
    db.commit()
    return opportunity_to_dict(get_opportunity_or_404(db, opp_id))
