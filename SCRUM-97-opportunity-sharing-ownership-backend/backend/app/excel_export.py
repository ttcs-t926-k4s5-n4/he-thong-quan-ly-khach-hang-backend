"""
app/excel_export.py — Xuất dữ liệu Khách hàng và Cơ hội ra Excel (.xlsx) kèm Trường tùy chỉnh (SCRUM-66)
"""
import io
from typing import Any
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.custom_fields import list_custom_fields
from app.customers import list_customers
from app.opportunities import list_opportunities


def export_customers_excel(q: str = "", status: str = "", cf_filters: dict[str, str] | None = None) -> io.BytesIO:
    """Xuất danh sách khách hàng kèm toàn bộ cột Trường tùy chỉnh ra file Excel (.xlsx)"""
    # Lấy danh sách định nghĩa trường tùy chỉnh active
    custom_fields = list_custom_fields(entity_type="customer", is_active_only=True)

    # Lấy toàn bộ danh sách khách hàng khớp điều kiện (không phân trang)
    data = list_customers(q=q, status=status, cf_filters=cf_filters, page=1, per_page=10000)
    customers = data.get("items", [])

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Danh sách Khách hàng"
    ws.views.sheetView[0].showGridLines = True

    # 1. Tạo tiêu đề cột (Standard + Custom fields)
    headers = [
        "STT",
        "ID",
        "Tên Khách hàng",
        "Số điện thoại",
        "Email",
        "Địa chỉ",
        "Trạng thái",
        "Người tạo",
    ]
    for cf in custom_fields:
        headers.append(cf["field_label"])

    # Format header styles
    header_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")  # Dark blue
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style="thin", color="D1D5DB"),
        right=Side(style="thin", color="D1D5DB"),
        top=Side(style="thin", color="D1D5DB"),
        bottom=Side(style="thin", color="D1D5DB"),
    )

    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    ws.row_dimensions[1].height = 28

    # 2. Điền dữ liệu các dòng
    for idx, c in enumerate(customers, start=1):
        row = [
            idx,
            c.get("id"),
            c.get("name", ""),
            c.get("phone", ""),
            c.get("email", ""),
            c.get("address", ""),
            c.get("status", ""),
            c.get("creator_name", ""),
        ]
        cf_values = c.get("custom_fields", {})
        for cf in custom_fields:
            key = cf["field_key"]
            row.append(cf_values.get(key, ""))

        ws.append(row)
        current_row = idx + 1
        ws.row_dimensions[current_row].height = 22
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=current_row, column=col_num)
            cell.border = thin_border
            cell.font = Font(name="Calibri", size=10)
            if col_num in (1, 2, 7):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    # Dynamic column widths
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val = str(cell.value or "")
            max_len = max(max_len, len(val))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    # Freeze header line
    ws.freeze_panes = "A2"

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def export_opportunities_excel(
    q: str = "", stage: str = "", customer_id: int | None = None, cf_filters: dict[str, str] | None = None
) -> io.BytesIO:
    """Xuất danh sách cơ hội kèm toàn bộ cột Trường tùy chỉnh ra file Excel (.xlsx)"""
    custom_fields = list_custom_fields(entity_type="opportunity", is_active_only=True)
    data = list_opportunities(q=q, stage=stage, customer_id=customer_id, cf_filters=cf_filters, page=1, per_page=10000)
    opportunities = data.get("items", [])

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Danh sách Cơ hội"
    ws.views.sheetView[0].showGridLines = True

    headers = [
        "STT",
        "ID",
        "Tên Cơ hội",
        "Khách hàng",
        "Giá trị (VNĐ)",
        "Giai đoạn",
        "Ngày dự kiến đóng",
        "Người tạo",
    ]
    for cf in custom_fields:
        headers.append(cf["field_label"])

    header_fill = PatternFill(start_color="047857", end_color="047857", fill_type="solid")  # Dark green
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style="thin", color="D1D5DB"),
        right=Side(style="thin", color="D1D5DB"),
        top=Side(style="thin", color="D1D5DB"),
        bottom=Side(style="thin", color="D1D5DB"),
    )

    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    ws.row_dimensions[1].height = 28

    for idx, o in enumerate(opportunities, start=1):
        row = [
            idx,
            o.get("id"),
            o.get("title", ""),
            o.get("customer_name", ""),
            o.get("value", 0.0),
            o.get("stage", ""),
            o.get("expected_close_date", ""),
            o.get("creator_name", ""),
        ]
        cf_values = o.get("custom_fields", {})
        for cf in custom_fields:
            key = cf["field_key"]
            row.append(cf_values.get(key, ""))

        ws.append(row)
        current_row = idx + 1
        ws.row_dimensions[current_row].height = 22
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=current_row, column=col_num)
            cell.border = thin_border
            cell.font = Font(name="Calibri", size=10)
            if col_num in (1, 2, 6, 7):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_num == 5:
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.number_format = "#,##0"
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val = str(cell.value or "")
            max_len = max(max_len, len(val))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    ws.freeze_panes = "A2"

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
