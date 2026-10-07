# Audit Log System - Backend

## SCRUM-62: Nhật ký thay đổi trên dữ liệu nhạy cảm

> Là Quản trị hệ thống, tôi muốn xem nhật ký thay đổi trên dữ liệu nhạy cảm,
> để truy được ai đã sửa chiết khấu hoặc chỉ tiêu khi cuối quý số liệu không khớp.

## Chức năng

- ✅ Ghi lại mọi thay đổi trên chiết khấu, chỉ tiêu, quyền sở hữu dữ liệu và vai trò người dùng
- ✅ Mỗi bản ghi có người thực hiện, thời điểm, giá trị trước và sau
- ✅ Lọc theo người dùng, loại đối tượng, khoảng thời gian

## Cài đặt & Chạy

### 1. Tạo virtual environment

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
```

### 2. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 3. Tạo dữ liệu mẫu (tùy chọn)

```bash
python seed_data.py
```

### 4. Chạy server

```bash
uvicorn app.main:app --reload
```

### 5. Truy cập API docs

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## API Endpoints

### Users

| Method | Endpoint           | Mô tả                  |
|--------|-------------------|-------------------------|
| POST   | `/api/users/`     | Tạo người dùng mới     |
| GET    | `/api/users/`     | Danh sách người dùng    |
| GET    | `/api/users/{id}` | Chi tiết người dùng     |

### Audit Logs

| Method | Endpoint                | Mô tả                          |
|--------|------------------------|---------------------------------|
| POST   | `/api/audit-logs/`     | Tạo bản ghi audit log          |
| GET    | `/api/audit-logs/`     | Danh sách (có lọc + phân trang)|
| GET    | `/api/audit-logs/{id}` | Chi tiết bản ghi                |

### Bộ lọc Audit Log (Query Parameters)

| Parameter     | Kiểu      | Mô tả                                                  |
|--------------|-----------|----------------------------------------------------------|
| `user_id`    | int       | Lọc theo ID người thực hiện                              |
| `object_type`| string    | `discount`, `quota`, `data_ownership`, `user_role`       |
| `action`     | string    | `create`, `update`, `delete`                             |
| `start_date` | datetime  | Lọc từ ngày (ISO 8601)                                   |
| `end_date`   | datetime  | Lọc đến ngày (ISO 8601)                                  |
| `object_id`  | int       | Lọc theo ID đối tượng cụ thể                             |
| `page`       | int       | Số trang (mặc định: 1)                                   |
| `page_size`  | int       | Số bản ghi mỗi trang (mặc định: 20, tối đa: 100)        |

## Ví dụ sử dụng

### Tạo audit log khi cập nhật chiết khấu

```bash
curl -X POST http://localhost:8000/api/audit-logs/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "action": "update",
    "object_type": "discount",
    "object_id": 101,
    "field_name": "discount_percentage",
    "old_value": "10%",
    "new_value": "25%",
    "description": "Tăng chiết khấu cho khách hàng VIP",
    "ip_address": "192.168.1.50"
  }'
```

### Lọc audit log theo người dùng và khoảng thời gian

```bash
curl "http://localhost:8000/api/audit-logs/?user_id=1&start_date=2026-10-01T00:00:00&end_date=2026-10-31T23:59:59"
```

### Lọc theo loại đối tượng (chỉ xem chiết khấu)

```bash
curl "http://localhost:8000/api/audit-logs/?object_type=discount"
```

## Cấu trúc project

```
audit-log-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point - FastAPI app
│   ├── database.py           # Cấu hình database (SQLite)
│   ├── models.py             # SQLAlchemy models (User, AuditLog)
│   ├── schemas.py            # Pydantic schemas (request/response)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── audit_logs.py     # API endpoints cho audit log
│   │   └── users.py          # API endpoints cho users
│   └── services/
│       ├── __init__.py
│       └── audit_service.py  # Logic xử lý nghiệp vụ
├── seed_data.py              # Script tạo dữ liệu mẫu
├── requirements.txt          # Dependencies
└── README.md                 # Tài liệu
```

## Tech Stack

- **Python 3.10+**
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **SQLite** - Database (dễ chuyển sang PostgreSQL)
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server
