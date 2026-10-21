# SCRUM-83: Lead assignment backend

Backend độc lập cho phân lead tự động theo rule có thứ tự ưu tiên, có worker xử lý hàng đợi bằng Python, FastAPI, SQLAlchemy và SQLite.

## Chạy

```bash
cd /Users/hainam1919/scrum_83_lead_assignment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Mở Swagger UI tại http://127.0.0.1:8000/docs. Worker được khởi chạy cùng API. Giữ tiến trình API chạy để worker xử lý job; job đang chờ được lưu trong database và tiếp tục sau khi khởi động lại.

## Cấu hình rule

`PUT /assignment/rules` thay toàn bộ danh sách rule. Rule được xét theo `priority` tăng dần và rule đầu tiên khớp sẽ được dùng. Nếu khai báo cả `region` và `industry`, cả hai phải khớp. Bỏ trống điều kiện tạo rule mặc định khớp mọi lead.

```json
{
  "rules": [
    {
      "name": "Miền Nam - SaaS",
      "priority": 1,
      "region": "South",
      "industry": "SaaS",
      "mode": "round_robin",
      "assignees": ["sales-01", "sales-02"]
    },
    {
      "name": "Lead miền Bắc",
      "priority": 2,
      "region": "North",
      "mode": "fixed",
      "assignees": ["sales-03"]
    }
  ]
}
```

## Luồng xử lý

- `POST /leads` nhận lead và đưa job vào hàng đợi; API không phải chờ phân công xong.
- Worker nền xét lần lượt các rule. `fixed` giao cho một người; `round_robin` xoay vòng giữa các thành viên được cấu hình.
- Job được xem tại `GET /assignment/jobs/{job_id}`.
- Có thể tra job mới nhất theo lead bằng `GET /assignment/jobs/lead/{lead_id}`.
- Nếu không rule nào khớp, lead chuyển vào `manual_queue`; trưởng nhóm xem `GET /assignment/queue` và giao người phụ trách bằng `POST /leads/{lead_id}/assign`.

Worker xử lý các job đang chờ liên tục, thường trong vài giây khi API đang chạy. Mốc 5 phút phụ thuộc vào việc service và worker được vận hành liên tục; đây là worker trong cùng tiến trình FastAPI, chưa phải hệ thống hàng đợi phân tán cho triển khai nhiều instance.
