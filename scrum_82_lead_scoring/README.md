# SCRUM-82: Lead scoring backend

Backend độc lập cho cấu hình điểm và sắp xếp ưu tiên lead. Project dùng Python, FastAPI, SQLAlchemy và SQLite; dữ liệu nằm trong `scoring.db`.

## Chạy ứng dụng

```bash
cd /Users/hainam1919/scrum_82_lead_scoring
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs

## Cấu hình điểm

`PUT /scoring/config` thay cấu hình tiêu chí và ngưỡng. Điểm các giá trị khớp được cộng lại; việc so khớp không phân biệt chữ hoa/thường. Khi cấu hình thay đổi, toàn bộ lead được tính lại.

```json
{
  "rules": {
    "industry": {"SaaS": 30, "Technology": 20},
    "company_size": {"Enterprise": 25, "SMB": 10},
    "source": {"Referral": 20},
    "interest_level": {"High": 30, "Medium": 15}
  },
  "hot_min": 70,
  "warm_min": 40
}
```

Tiêu chí hỗ trợ: `industry` (ngành nghề), `company_size` (quy mô), `source` (nguồn), `interest_level` (mức độ quan tâm). Lead được phân loại `hot`, `warm` hoặc `cold` theo ngưỡng.

## API chính

- `GET /scoring/config`, `PUT /scoring/config`: xem và cập nhật tiêu chí, điểm, ngưỡng.
- `POST /leads`: tạo lead; phản hồi có điểm và phân loại.
- `PATCH /leads/{lead_id}`: cập nhật thông tin, tự tính lại điểm.
- `GET /leads/priority`: liệt kê lead đang hoạt động theo điểm giảm dần. Điểm chỉ sắp xếp ưu tiên; không tự loại lead.
- `GET /leads/{lead_id}`: xem lead.
