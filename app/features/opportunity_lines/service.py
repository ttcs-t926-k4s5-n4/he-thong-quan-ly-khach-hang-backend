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
