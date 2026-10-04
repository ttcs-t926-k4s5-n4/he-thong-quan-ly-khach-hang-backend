# S2-10: Khai báo Danh mục Lý do Thắng/Thua & Đối thủ cạnh tranh (Backend Python)

## 📌 Tổng quan Feature

User Story này phục vụ nhu cầu của **Giám đốc kinh doanh (Sales Manager)** nhằm chuẩn hóa dữ liệu đóng cơ hội (Sales Closure Intelligence):
1. Khai báo danh mục **Lý do Thắng (`win_reasons`)** và **Lý do Thua (`loss_reasons`)** riêng biệt.
2. Khai báo danh mục **Đối thủ cạnh tranh (`competitors`)**.
3. Áp dụng quy tắc ràng buộc bắt buộc khi chốt cơ hội:
   - Khi chốt cơ hội thành công (`closed_won`): Bắt buộc phải nhập **Lý do Thắng**.
   - Khi chốt cơ hội thất bại (`closed_lost`): Bắt buộc phải nhập **Lý do Thua** và chọn **Đối thủ cạnh tranh** chiến thắng.

---

## 🔥 Các Yêu cầu & Giải pháp Đáp ứng

| Yêu cầu Story | Giải pháp Backend |
|---|---|
| **1. Khai báo danh mục Lý do Thắng / Thua riêng biệt** | Bảng `dbo.win_loss_reasons` lưu các lý do với `reason_type = 'win'` hoặc `'loss'`, `reason_code`, `reason_title`. |
| **2. Danh mục Đối thủ cạnh tranh** | Bảng `dbo.competitors` lưu tên đối thủ, website, điểm mạnh, điểm yếu. |
| **3. Ràng buộc dữ liệu bắt buộc khi đóng cơ hội** | Hàm `validate_opportunity_closure` kiểm tra khi cập nhật giai đoạn cơ hội: Won bắt buộc có `win_reason_id`, Lost bắt buộc có `loss_reason_id` và `competitor_id`. |

---

## 📂 Cấu trúc thư mục Feature

```
S2-10-win-loss-reasons-backend/
├── README.md                           ← Tài liệu hướng dẫn & API Spec
├── database/
│   └── s2_10_win_loss_reasons.sql      ← SQL Schema cho SQL Server 2019+
└── backend/
    ├── app/
    │   ├── win_loss_reasons.py         ← Module quản lý lý do thắng/thua & đối thủ cạnh tranh
    │   ├── opportunities.py            ← Tích hợp validation đóng cơ hội kinh doanh
    │   ├── routes.py                   ← API Endpoints
    │   └── ...
    └── tests/
        └── test_win_loss_reasons.py    ← Automated integration tests
```

---

## 📡 Chi tiết API Endpoints

### 1. Lý do Thắng / Thua
- `GET /api/win-loss-reasons?type=win|loss` — Danh sách lý do thắng/thua
- `POST /api/win-loss-reasons` — Khai báo lý do mới (Sales Manager / Admin)
- `PUT /api/win-loss-reasons/<id>` — Cập nhật lý do (Sales Manager / Admin)
- `DELETE /api/win-loss-reasons/<id>` — Xóa lý do (Sales Manager / Admin)

### 2. Đối thủ Cạnh tranh
- `GET /api/competitors` — Danh sách đối thủ cạnh tranh
- `POST /api/competitors` — Khai báo đối thủ mới (Sales Manager / Admin)
- `GET /api/competitors/<id>` — Xem chi tiết đối thủ
- `PUT /api/competitors/<id>` — Cập nhật đối thủ (Sales Manager / Admin)
- `DELETE /api/competitors/<id>` — Xóa đối thủ (Sales Manager / Admin)
