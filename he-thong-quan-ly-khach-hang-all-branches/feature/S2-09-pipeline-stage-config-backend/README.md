# S2-09: Cấu hình các giai đoạn Pipeline & Xác suất thắng (Backend Python)

## 📌 Tổng quan Feature

User Story này phục vụ nhu cầu của **Giám đốc kinh doanh (Sales Manager)** để cấu hình quy trình bán hàng chuẩn (Sales Pipeline), thiết lập xác suất thắng mặc định cho từng giai đoạn và định nghĩa các điều kiện bắt buộc khi chuyển giai đoạn, giúp tính toán con số dự báo doanh số (`forecast_amount`) chính xác và có cơ sở khoa học.

---

## 🔥 Các Yêu cầu & Giải pháp Đáp ứng

| Yêu cầu Story | Giải pháp Backend |
|---|---|
| **1. Khai báo chuỗi giai đoạn** | Quản lý các giai đoạn (VD: Tiếp cận [10%] → Xác định nhu cầu [25%] → Đề xuất giải pháp [50%] → Báo giá [70%] → Đàm phán [85%] → Won [100%] / Lost [0%]). |
| **2. Xác suất thắng mặc định & Dự báo** | Mỗi giai đoạn lưu `win_probability` (0 - 100%). API `/api/forecast/summary` tính toán doanh số dự báo tổng theo công thức: `Forecast Amount = Value * Win Probability / 100`. |
| **3. Điều kiện bắt buộc rời giai đoạn (Exit Conditions)** | Cấu hình `required_conditions` (dạng JSON, VD: `{"min_meetings": 1}`). Khi chuyển sang giai đoạn tiếp theo, backend tự động kiểm tra số lượng cuộc gặp (`meetings_count`). Nếu chưa đạt điều kiện -> Chặn chuyển giai đoạn và trả về lỗi rõ ràng. |
| **4. Thay đổi cấu hình không làm hỏng cơ hội đang chạy** | Cấu hình giai đoạn lưu `stage_key` độc lập và sử dụng `is_active` (soft delete/disable). Cơ hội đang chạy giữ nguyên snapshot xác suất và dữ liệu lịch sử an toàn. |

---

## 📂 Cấu trúc thư mục Feature

```
S2-09-pipeline-stage-config-backend/
├── README.md                           ← Tài liệu hướng dẫn & API Spec
├── database/
│   └── s2_09_pipeline_stages.sql       ← SQL Schema cho SQL Server 2019+
└── backend/
    ├── app/
    │   ├── pipeline_stages.py          ← Module quản lý giai đoạn pipeline & dự báo doanh số
    │   ├── opportunities.py            ← Tích hợp stage key & kiểm tra điều kiện chuyển giai đoạn
    │   ├── routes.py                   ← API Endpoints
    │   └── ...
    └── tests/
        └── test_pipeline_stages.py     ← Automated integration tests
```

---

## 📡 Chi tiết API Endpoints

- `GET /api/pipeline-stages` — Danh sách các giai đoạn Pipeline & xác suất thắng
- `POST /api/pipeline-stages` — Cấu hình tạo giai đoạn mới (Sales Manager / Admin)
- `GET /api/pipeline-stages/<id>` — Xem chi tiết 1 giai đoạn
- `PUT /api/pipeline-stages/<id>` — Cập nhật giai đoạn, xác suất thắng & điều kiện (Sales Manager / Admin)
- `DELETE /api/pipeline-stages/<id>` — Vô hiệu hóa / Xóa giai đoạn (Sales Manager / Admin)
- `GET /api/forecast/summary` — Báo cáo tổng hợp Dự báo doanh số (Weighted Sales Forecast Report)
