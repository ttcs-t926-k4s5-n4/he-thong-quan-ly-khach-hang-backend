# SCRUM-97: Chia sẻ Cơ hội kinh doanh & Quản lý Sở hữu (Opportunity Sharing & Ownership) — Backend Python

## 📌 1. Tổng quan Feature

User Story: **"Là Trưởng nhóm kinh doanh, tôi muốn chia sẻ một cơ hội cho nhiều thành viên cùng theo dõi và ghi nhận hoạt động, đồng thời duy trì một người sở hữu chính chịu trách nhiệm về cơ hội."**

Feature này mở rộng mô hình phân quyền dữ liệu của hệ thống CRM, cho phép phân tách vai trò **Người sở hữu chính (Primary Owner)** và **Thành viên được chia sẻ (Shared Members)** với các cấp độ quyền hạn chi tiết (`read`, `edit`, `manage`), hỗ trợ chuyển giao quyền sở hữu nguyên tử và lưu vết lịch sử kiểm toán (SCRUM-95).

---

## 🔥 2. Ma trận Phân quyền & Quy tắc Nghiệp vụ

| Thao tác | Admin / Manager | Primary Owner | Shared Member (`manage`) | Shared Member (`edit`) | Shared Member (`read`) | Người dùng khác |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Xem cơ hội** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Cập nhật thông tin cơ hội** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Thêm / Gỡ thành viên chia sẻ** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Thay đổi quyền thành viên** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Chuyển quyền sở hữu chính** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

### Quy tắc quan trọng:
1. **Primary Owner duy nhất**: Mỗi cơ hội chỉ có một Người sở hữu chính (`owner_id`), là người chịu trách nhiệm cao nhất.
2. **Không chia sẻ cho Primary Owner**: Ngăn chặn thêm trùng Người sở hữu chính vào danh sách chia sẻ.
3. **Ngăn chia sẻ trùng lặp**: Ràng buộc duy nhất `UNIQUE (opportunity_id, user_id)` bảo đảm tính toàn vẹn dữ liệu.
4. **Chuyển quyền sở hữu nguyên tử**:
   - Chỉ Primary Owner, Manager hoặc Admin mới có quyền chuyển quyền sở hữu chính.
   - Cập nhật `owner_id` trong `dbo.opportunities`.
   - Nếu chủ sở hữu mới trước đó là Shared Member, tự động xóa khỏi bảng chia sẻ.
   - Tự động thêm chủ sở hữu cũ vào bảng chia sẻ với quyền `edit` để không bị mất quyền truy cập.
   - Tự động ghi nhật ký vào `dbo.opportunity_history` (SCRUM-95) trong cùng transaction.

---

## 📂 3. Cấu trúc thư mục Feature

```
SCRUM-97-opportunity-sharing-ownership-backend/
├── README.md                                    ← Tài liệu đặc tả và hướng dẫn chi tiết
├── database/
│   └── scrum_97_opportunity_shares.sql         ← Migration CSDL: bảng opportunity_shares + Unique constraint
└── backend/
    ├── app/
    │   ├── opportunity_shares.py                ← ★ Module mới: Quản lý chia sẻ & chuyển quyền sở hữu
    │   ├── opportunity_history.py               ← Tích hợp kiểm toán lịch sử thay đổi (SCRUM-95)
    │   ├── opportunities.py                     ← Module Cơ hội
    │   ├── routes.py                            ← API Endpoints (/shares + /transfer-ownership)
    │   └── ...                                  ← Các module hiện có của hệ thống
    └── tests/
        ├── conftest.py
        └── test_opportunity_shares.py          ← ★ Bộ kiểm thử tự động toàn diện (15 test cases)
```

---

## 🗄️ 4. Database Schema & Migration

### Bảng mới: `dbo.opportunity_shares`
Lưu trữ danh sách các thành viên được chia sẻ quyền truy cập cơ hội:

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | `BIGINT` | `IDENTITY(1,1) PRIMARY KEY` | Khóa chính tự tăng |
| `opportunity_id` | `INT` | `FOREIGN KEY REFERENCES dbo.opportunities(id) ON DELETE CASCADE` | ID cơ hội kinh doanh |
| `user_id` | `INT` | `FOREIGN KEY REFERENCES dbo.users(id)` | ID thành viên được chia sẻ |
| `shared_by` | `INT` | `FOREIGN KEY REFERENCES dbo.users(id)` | ID người thực hiện chia sẻ |
| `permission_level` | `NVARCHAR(50)` | `NOT NULL DEFAULT 'read'` | Cấp độ quyền: `read`, `edit`, `manage` |
| `created_at` | `BIGINT` | `NOT NULL` | Thời điểm chia sẻ (UTC epoch ms) |
| `updated_at` | `BIGINT` | `NOT NULL` | Thời điểm cập nhật (UTC epoch ms) |

### Ràng buộc & Indexes:
- `UQ_opp_share_user UNIQUE (opportunity_id, user_id)`: Ngăn chặn chia sẻ trùng một thành viên trong cùng một cơ hội.
- `IX_opp_shares_opp_id`: Tối ưu truy vấn danh sách thành viên theo cơ hội.
- `IX_opp_shares_user_id`: Tối ưu lọc các cơ hội được chia sẻ cho một người dùng.

---

## 📡 5. Chi tiết API Endpoints

### 1. `GET /api/opportunities/<opportunity_id>/shares`
Lấy thông tin Người sở hữu chính (`primary_owner`) và danh sách các thành viên được chia sẻ (`shares`).

### 2. `POST /api/opportunities/<opportunity_id>/shares`
Chia sẻ cơ hội cho thành viên mới.
- **Request Body**: `{"user_id": 8, "permission_level": "edit"}`
- **Validation**: Kiểm tra người dùng tồn tại, đang hoạt động, không phải là Primary Owner và chưa từng được chia sẻ.

### 3. `PATCH /api/opportunities/<opportunity_id>/shares/<user_id>`
Cập nhật cấp độ quyền hạn của thành viên (`read`, `edit`, `manage`).

### 4. `DELETE /api/opportunities/<opportunity_id>/shares/<user_id>`
Gỡ thành viên khỏi cơ hội (cho phép người quản lý hoặc chính thành viên tự rời đi).

### 5. `POST /api/opportunities/<opportunity_id>/transfer-ownership`
Chuyển quyền sở hữu chính cho người dùng mới.
- **Request Body**: `{"new_owner_id": 7}`
- **Validation**: Người gọi phải là Primary Owner / Manager / Admin. Chủ sở hữu mới phải tồn tại và đang hoạt động.
- **Transaction**: Thực hiện cập nhật `owner_id`, cập nhật bảng shares, ghi lịch sử kiểm toán `dbo.opportunity_history` trong cùng 1 transaction nguyên tử.

---

## 🧪 6. Hướng dẫn Chạy Kiểm thử (Testing)

```bash
cd backend
python -m unittest tests/test_opportunity_shares.py -v
```

Kết quả: **15/15 tests passed (100% OK)**.
