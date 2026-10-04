"""Khai báo 4 loại dữ liệu áp dụng phân quyền: khách hàng, cơ hội, hoạt động, báo giá.

Muốn thêm loại dữ liệu mới chỉ cần thêm một Resource vào RESOURCES —
danh sách, tìm kiếm, xuất Excel, xem chi tiết tự động được phân quyền.
"""
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class Resource:
    name: str                          # tên trên URL
    table: str                         # tên bảng SQL
    label: str                         # tên tiếng Việt dùng trong thông báo
    sheet_title: str                   # tên sheet Excel
    columns: List[Tuple[str, str]]     # (cột SQL của bảng, tiêu đề tiếng Việt)
    search_fields: List[str]           # cột dùng cho tìm kiếm ?q=


RESOURCES = {
    "customers": Resource(
        name="customers", table="customers", label="khách hàng",
        sheet_title="Khách hàng",
        columns=[("id", "Mã"), ("name", "Tên khách hàng"), ("phone", "Điện thoại"),
                 ("email", "Email"), ("address", "Địa chỉ")],
        search_fields=["name", "phone", "email"],
    ),
    "opportunities": Resource(
        name="opportunities", table="opportunities", label="cơ hội",
        sheet_title="Cơ hội",
        columns=[("id", "Mã"), ("title", "Tên cơ hội"), ("customer_id", "Mã KH"),
                 ("value", "Giá trị (VNĐ)"), ("stage", "Giai đoạn")],
        search_fields=["title", "stage"],
    ),
    "activities": Resource(
        name="activities", table="activities", label="hoạt động",
        sheet_title="Hoạt động",
        columns=[("id", "Mã"), ("subject", "Nội dung"), ("customer_id", "Mã KH"),
                 ("type", "Loại"), ("activity_date", "Ngày")],
        search_fields=["subject", "type"],
    ),
    "quotes": Resource(
        name="quotes", table="quotes", label="báo giá",
        sheet_title="Báo giá",
        columns=[("id", "Mã"), ("code", "Số báo giá"), ("customer_id", "Mã KH"),
                 ("amount", "Tổng tiền (VNĐ)"), ("status", "Trạng thái")],
        search_fields=["code", "status"],
    ),
}

# Cột người phụ trách luôn được thêm vào kết quả
OWNER_COLUMNS = [("owner_id", "Mã NV phụ trách"), ("owner_name", "Người phụ trách")]
