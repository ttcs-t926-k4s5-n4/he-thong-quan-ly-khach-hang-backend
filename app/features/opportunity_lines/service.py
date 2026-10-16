"""SCRUM-89 – Thêm sản phẩm/dịch vụ vào cơ hội để ra giá trị hợp đồng.

Tiêu chí:
- Chọn sản phẩm từ danh mục, nhập số lượng và đơn giá; đơn giá mặc định lấy từ bảng giá niêm yết.
- Giá trị cơ hội được tính lại tự động từ các dòng sản phẩm.
- Với dịch vụ thuê bao, khai báo được số kỳ và giá trị hợp đồng theo năm.

Cách tính:
- Sản phẩm / dịch vụ một lần: thành tiền = số lượng × đơn giá × (1 − chiết khấu%).
- Thuê bao: giá trị mỗi kỳ = số lượng × đơn giá/kỳ × (1 − chiết khấu%);
  tổng giá trị hợp đồng = giá trị mỗi kỳ × số kỳ;
  giá trị hợp đồng theo năm = giá trị mỗi kỳ × số kỳ trong 1 năm (tháng: 12, quý: 4, năm: 1),
  kèm bảng phân bổ giá trị theo từng năm hợp đồng.
- Giá trị cơ hội = tổng thành tiền các dòng. Xoá hết dòng thì quay về giá trị dự kiến nhập tay.
"""
from __future__ import annotations

from decimal import Decimal

from app import clock
from app.common.access import get_visible_opportunity
from app.db import execute, row, rows
from app.errors import Conflict, NotFound, ValidationFailed
from app.labels import (AMOUNT_SOURCES, BILLING_PERIODS, MONTHS_PER_PERIOD, OPPORTUNITY_STATUSES,
                        PERIODS_PER_YEAR, PRODUCT_TYPES, format_number, format_vnd, number_out, round_vnd,
                        search_text)
from app.validation import Bool, Choice, Int, Number, Str, field_error, invalid, validate

MAX_PRICE = 10**13

LINE_CREATE_SCHEMA = {
    "product_id": Int("Sản phẩm", required=True, min_value=1),
    "quantity": Number("Số lượng", required=True, gt=0, max_value=1_000_000, max_decimals=2),
    "unit_price": Int("Đơn giá", min_value=0, max_value=MAX_PRICE),
    "discount_percent": Number("Chiết khấu (%)", min_value=0, max_value=100, max_decimals=2,
                               default=Decimal("0")),
    "periods": Int("Số kỳ", min_value=1, max_value=120),
    "note": Str("Ghi chú", max_len=500),
}

LINE_UPDATE_SCHEMA = {
    "quantity": Number("Số lượng", gt=0, max_value=1_000_000, max_decimals=2, nullable=False),
    "unit_price": Int("Đơn giá", min_value=0, max_value=MAX_PRICE),
    "discount_percent": Number("Chiết khấu (%)", min_value=0, max_value=100, max_decimals=2, nullable=False),
    "periods": Int("Số kỳ", min_value=1, max_value=120),
    "note": Str("Ghi chú", max_len=500),
}
LINE_UPDATE_FORBIDDEN = {
    "product_id": "Không đổi sản phẩm của một dòng. Hãy xoá dòng này và thêm dòng mới với sản phẩm khác.",
}


# ============================================================ Danh mục & bảng giá

def current_price_list(on_date=None) -> dict | None:
    day = (on_date or clock.today()).isoformat()
    return row("SELECT * FROM price_lists WHERE is_active = 1 AND is_default = 1 AND valid_from <= ? "
               "AND (valid_to IS NULL OR valid_to >= ?) ORDER BY valid_from DESC, id DESC LIMIT 1", (day, day))


def list_price_of(product_id: int, price_list: dict | None) -> int | None:
    if price_list is None:
        return None
    item = row("SELECT unit_price FROM price_list_items WHERE price_list_id = ? AND product_id = ?",
               (price_list["id"], product_id))
    return item["unit_price"] if item else None


def _price_display(price, product: dict) -> str | None:
    if price is None:
        return None
    text = format_vnd(price)
    if product["product_type"] == "subscription" and product["billing_period"]:
        text += f"/{product['unit']}/{BILLING_PERIODS[product['billing_period']].lower()}"
    else:
        text += f"/{product['unit']}"
    return text


def product_out(product: dict, price_list: dict | None) -> dict:
    price = list_price_of(product["id"], price_list)
    return {
        "id": product["id"],
        "code": product["code"],
        "name": product["name"],
        "product_type": product["product_type"],
        "product_type_label": PRODUCT_TYPES[product["product_type"]],
        "unit": product["unit"],
        "billing_period": product["billing_period"],
        "billing_period_label": BILLING_PERIODS.get(product["billing_period"]) if product["billing_period"] else None,
        "list_price": price,
        "list_price_display": _price_display(price, product),
        "description": product["description"],
        "is_active": bool(product["is_active"]),
    }


def list_products(args: dict) -> dict:
    params = validate(args, {"q": Str("Từ khoá", max_len=100),
                             "product_type": Choice("Loại sản phẩm", PRODUCT_TYPES),
                             "include_inactive": Bool("Gồm cả sản phẩm ngừng kinh doanh", default=False)})
    sql, values = "SELECT * FROM products WHERE 1=1", []
    if not params["include_inactive"]:
        sql += " AND is_active = 1"
    if params["product_type"]:
        sql += " AND product_type = ?"
        values.append(params["product_type"])
    if params["q"]:
        sql += " AND (search_text(name) LIKE ? OR search_text(code) LIKE ?)"
        keyword = f"%{search_text(params['q'])}%"
        values += [keyword, keyword]
    price_list = current_price_list()
    items = [product_out(p, price_list) for p in rows(sql + " ORDER BY name", values)]
    return {
        "price_list": ({"id": price_list["id"], "name": price_list["name"], "valid_from": price_list["valid_from"],
                        "valid_to": price_list["valid_to"]} if price_list else None),
        "items": items,
    }


# ============================================================ Tính toán

def compute_line(product_type: str, billing_period: str | None, quantity, unit_price: int,
                 discount_percent, periods: int | None) -> dict:
    base = Decimal(str(quantity)) * Decimal(unit_price) * (Decimal(100) - Decimal(str(discount_percent))) / 100
    if product_type != "subscription":
        return {"line_total": round_vnd(base), "annual_value": None, "term_months": None, "yearly_breakdown": None}
    per_year = PERIODS_PER_YEAR[billing_period]
    total = round_vnd(base * periods)
    breakdown, remaining, year, allocated = [], periods, 1, 0
    while remaining > 0:
        in_year = min(per_year, remaining)
        remaining -= in_year
        value = total - allocated if remaining == 0 else round_vnd(base * in_year)
        allocated += value
        breakdown.append({"contract_year": year, "periods": in_year, "value": value,
                          "label": f"Năm thứ {year}: {in_year} {BILLING_PERIODS[billing_period].lower()}"})
        year += 1
    return {
        "line_total": total,
        "annual_value": round_vnd(base * per_year),
        "term_months": periods * MONTHS_PER_PERIOD[billing_period],
        "yearly_breakdown": breakdown,
    }


def _formula_text(line: dict, calc: dict) -> str:
    quantity = f"{format_number(line['quantity'])} {line['unit']}"
    if line["product_type"] == "subscription":
        period = BILLING_PERIODS[line["billing_period"]].lower()
        text = (f"{quantity} × {format_vnd(line['unit_price'])}/{period} × {line['periods']} {period}")
    else:
        text = f"{quantity} × {format_vnd(line['unit_price'])}"
    if Decimal(str(line["discount_percent"])) > 0:
        text += f" − chiết khấu {format_number(line['discount_percent'])}%"
    text += f" = {format_vnd(calc['line_total'])}"
    if calc["annual_value"] is not None:
        text += f" (giá trị hợp đồng theo năm: {format_vnd(calc['annual_value'])})"
    return text


def line_out(line: dict) -> dict:
    calc = compute_line(line["product_type"], line["billing_period"], line["quantity"], line["unit_price"],
                        line["discount_percent"], line["periods"])
    return {
        "id": line["id"],
        "product": {"id": line["product_id"], "code": line["product_code"], "name": line["product_name"],
                    "product_type": line["product_type"], "product_type_label": PRODUCT_TYPES[line["product_type"]],
                    "unit": line["unit"]},
        "quantity": number_out(line["quantity"]),
        "list_price": line["list_price"],
        "unit_price": line["unit_price"],
        "price_overridden": line["list_price"] is not None and line["unit_price"] != line["list_price"],
        "discount_percent": number_out(line["discount_percent"]),
        "billing_period": line["billing_period"],
        "billing_period_label": BILLING_PERIODS.get(line["billing_period"]) if line["billing_period"] else None,
        "periods": line["periods"],
        "term_months": calc["term_months"],
        "line_total": line["line_total"],
        "annual_value": line["annual_value"],
        "yearly_breakdown": calc["yearly_breakdown"],
        "formula": _formula_text(line, calc),
        "note": line["note"],
        "created_at": clock.iso(line["created_at"]),
        "updated_at": clock.iso(line["updated_at"]),
    }


def recalc_opportunity_amount(opp_id: int) -> dict:
    """Tính lại giá trị cơ hội từ các dòng sản phẩm."""
    agg = row("SELECT COUNT(*) AS n, COALESCE(SUM(line_total), 0) AS total, "
              "COALESCE(SUM(CASE WHEN product_type = 'subscription' THEN annual_value ELSE 0 END), 0) AS arr "
              "FROM opportunity_lines WHERE opportunity_id = ?", (opp_id,))
    now_text = clock.to_db(clock.now())
    if agg["n"]:
        execute("UPDATE opportunities SET amount = ?, amount_source = 'lines', recurring_annual_value = ?, "
                "updated_at = ? WHERE id = ?", (agg["total"], agg["arr"], now_text, opp_id))
    else:
        execute("UPDATE opportunities SET amount = estimated_value, amount_source = 'manual', "
                "recurring_annual_value = 0, updated_at = ? WHERE id = ?", (now_text, opp_id))
    return opportunity_value(opp_id)


def opportunity_value(opp_id: int) -> dict:
    opp = row("SELECT id, name, estimated_value, amount, amount_source, recurring_annual_value "
              "FROM opportunities WHERE id = ?", (opp_id,))
    opp["amount_source_label"] = AMOUNT_SOURCES[opp["amount_source"]]
    return opp


# ============================================================ Thao tác dòng sản phẩm

def _editable_opportunity(user: dict, opp_id: int) -> dict:
    opp = get_visible_opportunity(user, opp_id)
    if opp["stage_is_won"] or opp["stage_is_lost"]:
        status = OPPORTUNITY_STATUSES["won" if opp["stage_is_won"] else "lost"].lower()
        raise Conflict(f"Cơ hội \"{opp['name']}\" đã đóng ({status}), không thể thay đổi dòng sản phẩm.")
    return opp


def _get_line(opp_id: int, line_id: int) -> dict:
    line = row("SELECT * FROM opportunity_lines WHERE id = ? AND opportunity_id = ?", (line_id, opp_id))
    if line is None:
        raise NotFound("Không tìm thấy dòng sản phẩm trong cơ hội này.")
    return line


def _check_periods(product_type: str, periods, product_name: str) -> list[dict]:
    if product_type == "subscription" and periods is None:
        return [field_error("periods", "Số kỳ",
                            f"\"{product_name}\" là dịch vụ thuê bao, vui lòng khai báo số kỳ (periods).")]
    if product_type != "subscription" and periods is not None:
        return [field_error("periods", "Số kỳ", "Chỉ dịch vụ thuê bao mới khai báo số kỳ.")]
    return []


def list_lines(user: dict, opp_id: int) -> dict:
    get_visible_opportunity(user, opp_id)
    lines = [line_out(r) for r in rows("SELECT * FROM opportunity_lines WHERE opportunity_id = ? ORDER BY id",
                                       (opp_id,))]
    one_time = sum(item["line_total"] for item in lines if item["product"]["product_type"] != "subscription")
    subscription = sum(item["line_total"] for item in lines if item["product"]["product_type"] == "subscription")
    return {
        "opportunity": opportunity_value(opp_id),
        "lines": lines,
        "totals": {
            "line_count": len(lines),
            "one_time_total": one_time,
            "subscription_total": subscription,
            "total_contract_value": one_time + subscription,
            "recurring_annual_value": sum(item["annual_value"] or 0 for item in lines),
        },
    }


def add_line(user: dict, opp_id: int, payload: dict) -> dict:
    opp = _editable_opportunity(user, opp_id)
    data = validate(payload, LINE_CREATE_SCHEMA)
    product = row("SELECT * FROM products WHERE id = ?", (data["product_id"],))
    if product is None or not product["is_active"]:
        raise invalid("product_id", "Sản phẩm", "Sản phẩm không có trong danh mục hoặc đã ngừng kinh doanh.")

    errors = _check_periods(product["product_type"], data["periods"], product["name"])
    list_price = list_price_of(product["id"], current_price_list())
    unit_price = data["unit_price"] if data["unit_price"] is not None else list_price
    if unit_price is None:
        errors.append(field_error("unit_price", "Đơn giá",
                                  f"\"{product['name']}\" chưa có trong bảng giá niêm yết, vui lòng nhập đơn giá."))
    if errors:
        raise ValidationFailed(errors)

    calc = compute_line(product["product_type"], product["billing_period"], data["quantity"], unit_price,
                        data["discount_percent"], data["periods"])
    now_text = clock.to_db(clock.now())
    line_id = execute(
        "INSERT INTO opportunity_lines (opportunity_id, product_id, product_code, product_name, product_type, unit, "
        "quantity, list_price, unit_price, discount_percent, billing_period, periods, line_total, annual_value, "
        "note, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (opp_id, product["id"], product["code"], product["name"], product["product_type"], product["unit"],
         float(data["quantity"]), list_price, unit_price, float(data["discount_percent"]),
         product["billing_period"] if product["product_type"] == "subscription" else None, data["periods"],
         calc["line_total"], calc["annual_value"], data["note"], user["id"], now_text, now_text))
    value = recalc_opportunity_amount(opp_id)
    return {
        "message": (f"Đã thêm \"{product['name']}\" vào cơ hội \"{opp['name']}\". "
                    f"Giá trị cơ hội được tính lại: {format_vnd(value['amount'])}."),
        "line": line_out(_get_line(opp_id, line_id)),
        "opportunity": value,
    }


def update_line(user: dict, opp_id: int, line_id: int, payload: dict) -> dict:
    opp = _editable_opportunity(user, opp_id)
    line = _get_line(opp_id, line_id)
    data = validate(payload, LINE_UPDATE_SCHEMA, partial=True, forbidden=LINE_UPDATE_FORBIDDEN)
    if not data:
        raise invalid("body", "Dữ liệu", "Không có thông tin nào để cập nhật.")

    merged = dict(line)
    for key in ("quantity", "discount_percent", "periods", "note"):
        if key in data:
            merged[key] = data[key]
    if "unit_price" in data:
        # Gửi unit_price = null để quay về giá niêm yết hiện hành
        if data["unit_price"] is None:
            merged["list_price"] = list_price_of(line["product_id"], current_price_list())
            merged["unit_price"] = merged["list_price"]
            if merged["unit_price"] is None:
                raise invalid("unit_price", "Đơn giá",
                              "Sản phẩm chưa có trong bảng giá niêm yết, không thể quay về giá niêm yết.")
        else:
            merged["unit_price"] = data["unit_price"]
    errors = _check_periods(line["product_type"], merged["periods"], line["product_name"])
    if errors:
        raise ValidationFailed(errors)

    calc = compute_line(line["product_type"], line["billing_period"], merged["quantity"], merged["unit_price"],
                        merged["discount_percent"], merged["periods"])
    execute("UPDATE opportunity_lines SET quantity = ?, list_price = ?, unit_price = ?, discount_percent = ?, "
            "periods = ?, line_total = ?, annual_value = ?, note = ?, updated_at = ? WHERE id = ?",
            (float(merged["quantity"]), merged["list_price"], merged["unit_price"], float(merged["discount_percent"]),
             merged["periods"], calc["line_total"], calc["annual_value"], merged["note"],
             clock.to_db(clock.now()), line_id))
    value = recalc_opportunity_amount(opp_id)
    return {
        "message": (f"Đã cập nhật dòng \"{line['product_name']}\" của cơ hội \"{opp['name']}\". "
                    f"Giá trị cơ hội: {format_vnd(value['amount'])}."),
        "line": line_out(_get_line(opp_id, line_id)),
        "opportunity": value,
    }


def delete_line(user: dict, opp_id: int, line_id: int) -> dict:
    opp = _editable_opportunity(user, opp_id)
    line = _get_line(opp_id, line_id)
    execute("DELETE FROM opportunity_lines WHERE id = ?", (line_id,))
    value = recalc_opportunity_amount(opp_id)
    message = f"Đã xoá dòng \"{line['product_name']}\" khỏi cơ hội \"{opp['name']}\". "
    if value["amount_source"] == "manual":
        message += (f"Cơ hội không còn dòng sản phẩm nào, giá trị quay về giá trị dự kiến nhập tay: "
                    f"{format_vnd(value['amount'])}.")
    else:
        message += f"Giá trị cơ hội được tính lại: {format_vnd(value['amount'])}."
    return {"message": message, "line": None, "opportunity": value}
