# SCRUM-95: Lịch sử Thay đổi Cơ hội kinh doanh (Opportunity Change History) — Backend Python

## 📌 1. Tổng quan Feature

User Story: **"Là Trưởng nhóm kinh doanh, tôi muốn xem lịch sử thay đổi của một cơ hội kinh doanh (bao gồm giá trị cũ, giá trị mới, người thực hiện và thời điểm thay đổi) để theo dõi diễn biến đàm phán và đánh giá hiệu quả làm việc của nhân viên."**

Feature này cung cấp cơ chế kiểm toán (audit trail) nguyên tử cho cơ hội kinh doanh, tự động theo dõi và lưu trữ dài hạn mọi thay đổi trên các trường nghiệp vụ trọng yếu:
- **Stage**: Giai đoạn bán hàng trong pipeline
- **Value**: Giá trị cơ hội kinh doanh
- **Expected Close Date**: Ngày chốt dự kiến
- **Owner**: Người sở hữu cơ hội (`owner_id`)

---

## 🔥 2. Các Yêu cầu Nghiệp vụ & Giải pháp Backend

| Yêu cầu Story | Giải pháp & Đáp ứng Backend |
|---|---|
| **1. Theo dõi 4 trường trọng yếu** | Hàm `compute_opportunity_diff()` tự động so sánh chính xác `old_value` và `new_value` của: Stage, Value, Expected Close Date, Owner. |
| **2. Ghi nhận đầy đủ khi cập nhật nhiều trường** | Một request cập nhật có thể thay đổi nhiều trường; hệ thống sẽ sinh ra đầy đủ các bản ghi lịch sử tương ứng cho mỗi trường đã thay đổi. |
| **3. Chỉ ghi khi giá trị thực sự thay đổi** | Bỏ qua các trường không thay đổi (giữ nguyên giá trị cũ). Không ghi bản ghi rác vào CSDL. |
| **4. Ghi lịch sử cùng transaction (Atomicity)** | Cập nhật cơ hội và chèn lịch sử diễn ra trong cùng một transaction CSDL. Nếu có lỗi xảy ra, toàn bộ sẽ `ROLLBACK` lập tức, không để lại dữ liệu không nhất quán hoặc lịch sử giả. |
| **5. Không cho Client giả mạo người thực hiện** | `changed_by` luôn được trích xuất từ phiên xác thực an toàn phía Backend (`user.id`), loại bỏ hoàn toàn các trường `user_id` do Client tự gửi. |
| **6. Bất biến (Immutable Audit Trail)** | Lịch sử chỉ được truy xuất qua `GET /api/opportunities/<id>/history`. Không cung cấp API thêm/sửa/xóa lịch sử cho Client. |
| **7. Phân quyền chặt chẽ** | Admin và Trưởng nhóm (Manager) có quyền xem lịch sử của mọi cơ hội; Nhân viên kinh doanh (Employee) chỉ được xem lịch sử cơ hội do chính mình sở hữu hoặc tạo ra. Ngăn chặn triệt để truy cập trái phép (HTTP 403). |

---

## 📂 3. Cấu trúc thư mục Feature

```
SCRUM-95-opportunity-change-history-backend/
├── README.md                                   ← Tài liệu đặc tả và hướng dẫn chi tiết
├── database/
│   └── scrum_95_opportunity_history.sql        ← Migration CSDL: bảng opportunity_history + cột owner_id
└── backend/
    ├── app/
    │   ├── opportunity_history.py              ← ★ Module mới: Lõi quản lý & truy vấn lịch sử thay đổi cơ hội
    │   ├── opportunities.py                    ← Module Cơ hội (tích hợp diff & ghi lịch sử nguyên tử)
    │   ├── routes.py                           ← API Endpoints (GET history + PUT update opportunity)
    │   └── ...                                 ← Các module hiện có của hệ thống
    └── tests/
        ├── conftest.py
        └── test_opportunity_history.py         ← ★ Bộ kiểm thử tự động toàn diện (21 test cases)
```

---

## 🗄️ 4. Database Schema & Migration

### Bảng mới: `dbo.opportunity_history`
Lưu trữ toàn bộ các thay đổi của cơ hội theo thời gian (sử dụng epoch milliseconds UTC nhất quán):

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | `BIGINT` | `IDENTITY(1,1) PRIMARY KEY` | Khóa chính tự tăng |
| `opportunity_id` | `INT` | `FOREIGN KEY REFERENCES dbo.opportunities(id) ON DELETE CASCADE` | ID cơ hội kinh doanh |
| `field_name` | `NVARCHAR(100)` | `NOT NULL` | Tên trường (`stage`, `value`, `expected_close_date`, `owner`) |
| `old_value` | `NVARCHAR(MAX)` | `NULL` | Giá trị trước khi thay đổi |
| `new_value` | `NVARCHAR(MAX)` | `NULL` | Giá trị sau khi thay đổi |
| `changed_by` | `INT` | `FOREIGN KEY REFERENCES dbo.users(id)` | ID người thực hiện thay đổi |
| `changed_at` | `BIGINT` | `NOT NULL` | Thời điểm thay đổi (UTC epoch ms) |

### Indexes tối ưu hiệu năng:
- `IX_opp_hist_opp_id_changed_at` trên `(opportunity_id, changed_at DESC)`: Tối ưu truy vấn phân trang theo cơ hội.
- `IX_opp_hist_field_name` trên `(opportunity_id, field_name)`: Tối ưu lọc lịch sử theo trường cụ thể.

### Bổ sung cột vào `dbo.opportunities`:
- `owner_id INT NULL`: Lưu trữ người sở hữu cơ hội (mặc định nhận giá trị từ `created_by` nếu chưa gán).

---

## 📡 5. Chi tiết API Endpoints

### 1. `GET /api/opportunities/<opportunity_id>/history`
Lấy lịch sử thay đổi của một cơ hội kinh doanh.

#### Query Parameters:
| Tham số | Kiểu | Mặc định | Mô tả |
|---|---|---|---|
| `page` | `int` | `1` | Số trang cần lấy (từ 1) |
| `page_size` | `int` | `20` | Số bản ghi mỗi trang (hỗ trợ cả alias `per_page`) |
| `field` | `string` | `""` | Lọc theo tên trường thay đổi (`stage`, `value`, `expected_close_date`, `owner`) |

#### Phân quyền:
- `admin`, `manager`: Toàn quyền xem mọi cơ hội.
- `employee`: Chỉ xem cơ hội do mình sở hữu (`owner_id` hoặc `created_by`).

#### Response Success (HTTP 200):
```json
{
  "items": [
    {
      "id": 15,
      "opportunity_id": 1,
      "field_name": "stage",
      "field_label": "Giai đoạn",
      "old_value": "Mới tạo",
      "new_value": "Đàm phán",
      "changed_by": 2,
      "changed_by_name": "Trần Thị B",
      "changed_by_email": "manager@company.vn",
      "changed_at": 1729158000000,
      "changed_at_iso": "2026-10-17T09:40:00Z"
    },
    {
      "id": 16,
      "opportunity_id": 1,
      "field_name": "value",
      "field_label": "Giá trị cơ hội",
      "old_value": "50000000",
      "new_value": "80000000",
      "changed_by": 2,
      "changed_by_name": "Trần Thị B",
      "changed_by_email": "manager@company.vn",
      "changed_at": 1729158000000,
      "changed_at_iso": "2026-10-17T09:40:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 2,
  "total_pages": 1
}
```

#### Response Errors:
- `401 Unauthorized`: Chưa đăng nhập hoặc session đã hết hạn.
- `403 Forbidden`: Người dùng không có quyền truy cập cơ hội này.
- `404 Not Found`: Không tìm thấy cơ hội kinh doanh.

---

### 2. `PUT /api/opportunities/<opportunity_id>` (Tích hợp tự động ghi lịch sử)
Cập nhật cơ hội kinh doanh. Backend tự động so sánh dữ liệu trước và sau cập nhật, sau đó ghi các thay đổi vào `dbo.opportunity_history` trong cùng một transaction.

#### Request Body (JSON):
```json
{
  "title": "Hợp đồng phần mềm ERP",
  "customer_id": 10,
  "value": 150000000,
  "stage": "Đàm phán",
  "expected_close_date": "2026-12-31",
  "owner_id": 5
}
```

#### Quy tắc xử lý:
- Tự động phát hiện thay đổi trên `stage`, `value`, `expected_close_date`, `owner`.
- `changed_by` được gán bằng `user.id` từ session đã đăng nhập.
- Nếu không có trường nào thay đổi, không tạo bản ghi lịch sử giả.
- Nếu cập nhật CSDL lỗi, toàn bộ thao tác update và lịch sử được rollback ngay lập tức.

---

## 🧪 6. Hướng dẫn Chạy Migration & Kiểm thử (Testing)

### 1. Chạy Migration SQL Server:
```sql
-- Chạy file script trong Sql Server Management Studio hoặc sqlcmd:
sqlcmd -S localhost -d crm_db -U sa -P YourPassword -i database/scrum_95_opportunity_history.sql
```
*Lưu ý: Hệ thống cũng tích hợp cơ chế tự động khởi tạo bảng (`ensure_opportunity_history_table`) ngay khi chạy ứng dụng.*

### 2. Chạy Automated Tests:
```bash
cd backend
python -m unittest tests/test_opportunity_history.py -v
```

Kết quả kiểm thử thực tế:
```
test_update_opportunity_commits_both_opp_and_history ... ok
test_admin_can_access_any_opportunity ... ok
test_employee_can_access_own_opportunity ... ok
test_employee_cannot_access_other_opportunity ... ok
test_manager_can_access_any_opportunity ... ok
test_diff_expected_close_date_changed ... ok
test_diff_multiple_fields_changed ... ok
test_diff_owner_changed ... ok
test_diff_stage_changed ... ok
test_diff_value_changed ... ok
test_no_diff_when_data_unchanged ... ok
test_get_history_empty ... ok
test_get_history_with_field_filter ... ok
test_employee_can_access_own_opportunity_history ... ok
test_history_endpoint_forbidden_for_other_employee_returns_403 ... ok
test_history_endpoint_opportunity_not_found_returns_404 ... ok
test_history_endpoint_success_for_manager ... ok
test_history_endpoint_unauthenticated_returns_401 ... ok
test_update_opportunity_owner_not_found_returns_404 ... ok
test_update_opportunity_tracks_changed_by_from_session ... ok
test_rollback_on_update_failure ... ok

----------------------------------------------------------------------
Ran 21 tests in 0.449s

OK
```
