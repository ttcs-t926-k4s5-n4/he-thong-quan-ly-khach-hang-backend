# SCRUM-29 — Phân quyền dữ liệu theo vai trò và dữ liệu sở hữu

> **User story:** Là Giám đốc kinh doanh, tôi muốn có phân quyền vừa theo vai trò vừa theo
> dữ liệu sở hữu, để nhân viên chỉ thấy khách của mình, trưởng nhóm thấy toàn nhóm, còn tôi
> thấy tất cả.

Module viết bằng **Python (Flask + SQLite + openpyxl)**, có sẵn dữ liệu mẫu và bộ kiểm thử
tự động (32 test).

## Quy tắc phân quyền

| Vai trò | Phạm vi tối đa | Được thấy |
|---|---|---|
| Nhân viên kinh doanh (`NHAN_VIEN`) | `mine` — Của tôi | Bản ghi có `owner_id` = chính mình |
| Trưởng nhóm (`TRUONG_NHOM`) | `team` — Của nhóm tôi | Bản ghi của mọi thành viên cùng `team_id` |
| Giám đốc kinh doanh (`GIAM_DOC`) | `all` — Tất cả | Toàn bộ bản ghi |

- **Vai trò** quyết định phạm vi rộng nhất được phép; **dữ liệu sở hữu** (`owner_id`, nhóm của
  người sở hữu) quyết định bản ghi nào lọt vào phạm vi đó.
- Người dùng được chọn phạm vi **hẹp hơn** (ví dụ Giám đốc lọc "Của tôi"), nhưng chọn phạm vi
  **rộng hơn** vai trò sẽ bị từ chối (HTTP 403, thông báo tiếng Việt).
- Áp dụng cho 4 danh mục: khách hàng, cơ hội, hoạt động, báo giá.

## Đối chiếu tiêu chí chấp nhận

| Tiêu chí trên Jira | Cách đáp ứng | Test chứng minh |
|---|---|---|
| Ba phạm vi dữ liệu cho khách hàng, cơ hội, hoạt động, báo giá | `app/scope.py`, `app/resources.py` | `BaPhamViDuLieu` |
| Mọi truy vấn danh sách tự lọc, kể cả tìm kiếm và xuất Excel | `app/repository.py` — mọi truy vấn đi qua `build_scope_filter()` | `TimKiemXuatExcelVaPhanTrang` |
| Truy cập bản ghi ngoài phạm vi hiển thị thông báo tiếng Việt rõ ràng | `app/messages.py` | `ThongBaoTiengViet` |
| Kiểm thử tự động chứng minh nhân viên A không đọc được khách hàng của nhân viên B | `tests/` + GitHub Actions | `NhanVienAKhongDocDuocKhachHangCuaNhanVienB` |

## Cấu trúc thư mục

```
scrum-29-phan-quyen-du-lieu/
├── app/
│   ├── __init__.py      # create_app(), xử lý lỗi -> JSON tiếng Việt
│   ├── scope.py         # ★ LÕI PHÂN QUYỀN: Role, Scope, resolve_scope, build_scope_filter
│   ├── resources.py     # Khai báo 4 danh mục (bảng, cột, cột tìm kiếm, nhãn tiếng Việt)
│   ├── repository.py    # Truy vấn danh sách / tìm kiếm / chi tiết — luôn lọc theo phạm vi
│   ├── export.py        # Xuất Excel từ dữ liệu đã lọc
│   ├── routes.py        # API REST
│   ├── auth.py          # Lấy người dùng hiện tại (demo: header X-User-Id)
│   ├── messages.py      # Toàn bộ thông báo tiếng Việt
│   └── db.py            # Schema SQLite + dữ liệu mẫu
├── tests/
│   ├── base.py                  # Khung test, id người dùng mẫu
│   ├── test_scope_unit.py       # Test đơn vị lõi phân quyền
│   └── test_data_scope_api.py   # Test API theo tiêu chí chấp nhận
├── .github/workflows/tests.yml  # Tự chạy test mỗi lần push / pull request
├── run.py
├── requirements.txt
└── pytest.ini
```

## Cài đặt và chạy

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     |  macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

python run.py            # tự tạo CSDL mẫu ở instance/crm.db, chạy tại http://127.0.0.1:5000
pytest -v                # chạy toàn bộ kiểm thử
```

Tạo lại CSDL mẫu bất cứ lúc nào: `flask --app app init-db`

## Dữ liệu mẫu

| Id | Tài khoản | Họ tên | Vai trò | Nhóm | Sở hữu khách hàng |
|---|---|---|---|---|---|
| 1 | giamdoc | Trần Văn Giám | Giám đốc KD | — | 8 |
| 2 | truongnhom_bac | Lê Thị Hoa | Trưởng nhóm | Miền Bắc | 6 |
| 3 | nhanvien_a | Nguyễn Văn An | Nhân viên | Miền Bắc | 1, 2 |
| 4 | nhanvien_b | Phạm Thị Bình | Nhân viên | Miền Bắc | 3, 4 |
| 5 | truongnhom_nam | Hoàng Văn Nam | Trưởng nhóm | Miền Nam | 7 |
| 6 | nhanvien_c | Đỗ Minh Châu | Nhân viên | Miền Nam | 5 |

Mỗi khách hàng có kèm 1 cơ hội, 1 hoạt động, 1 báo giá cùng người phụ trách.

## API

Bản demo xác định người đăng nhập qua header `X-User-Id`.

| Phương thức | Đường dẫn | Mô tả |
|---|---|---|
| GET | `/api/me` | Thông tin người dùng + các phạm vi được chọn (để frontend dựng bộ lọc) |
| GET | `/api/{danh-muc}?scope=&q=&page=&page_size=` | Danh sách, tìm kiếm, phân trang |
| GET | `/api/{danh-muc}/export?scope=&q=` | Xuất Excel đúng phạm vi và từ khóa |
| GET | `/api/{danh-muc}/{id}` | Xem chi tiết (403 nếu ngoài phạm vi, 404 nếu không tồn tại) |

`{danh-muc}` là `customers`, `opportunities`, `activities` hoặc `quotes`.
`scope` là `mine`, `team` hoặc `all`; bỏ trống thì lấy phạm vi rộng nhất của vai trò.

Ví dụ:

```bash
# Nhân viên A xem danh sách khách hàng -> chỉ thấy khách hàng 1, 2
curl -H "X-User-Id: 3" http://127.0.0.1:5000/api/customers

# Nhân viên A mở khách hàng của nhân viên B -> 403
curl -H "X-User-Id: 3" http://127.0.0.1:5000/api/customers/3
```

```json
{
  "error": "NGOAI_PHAM_VI_DU_LIEU",
  "message": "Bạn không có quyền xem khách hàng #3. Bản ghi này nằm ngoài phạm vi dữ liệu của bạn (Của tôi). Nếu cần truy cập, vui lòng liên hệ trưởng nhóm hoặc Giám đốc kinh doanh."
}
```

```bash
# Trưởng nhóm Miền Bắc xuất Excel khách hàng của cả nhóm
curl -H "X-User-Id: 2" -o khach-hang.xlsx http://127.0.0.1:5000/api/customers/export
```

## Ghép vào dự án chung của nhóm

1. **Đăng nhập thật:** sửa `load_current_user()` trong `app/auth.py` để lấy user từ JWT/session
   của hệ thống. Chỉ cần trả về đối tượng `User(id, username, full_name, role, team_id)`.
2. **Bảng dữ liệu thật:** mỗi bảng cần cột `owner_id` (người phụ trách); bảng `users` cần
   `role` và `team_id`. Sửa tên bảng/cột trong `app/resources.py` cho khớp.
3. **Thêm danh mục mới** (ví dụ hợp đồng): thêm một `Resource` vào `RESOURCES` — danh sách,
   tìm kiếm, xuất Excel và xem chi tiết tự được phân quyền.
4. **Dùng ORM khác** (SQLAlchemy, Django): giữ nguyên `resolve_scope()`; viết lại
   `build_scope_filter()` để trả về điều kiện lọc của ORM đó.

Nguyên tắc quan trọng khi mở rộng: **không viết truy vấn đọc dữ liệu nào bỏ qua
`build_scope_filter()`**. Mỗi endpoint mới nên có test kiểu "nhân viên A không đọc được dữ
liệu của nhân viên B".
