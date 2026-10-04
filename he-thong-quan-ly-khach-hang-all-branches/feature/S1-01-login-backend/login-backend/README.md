# 🔐 S1-01 Login Backend

Backend Python FastAPI phục vụ riêng cho User Story **S1-01 (Đăng nhập & Bảo mật)**.

## 📋 Tiêu chí chấp nhận (Acceptance Criteria):
1. **Đăng nhập đúng:** Vào được trang chủ tương ứng với vai trò (`role`).
2. **Sai thông tin:** Hiển thị thông báo chung ("Email hoặc mật khẩu không đúng."), không tiết lộ email có tồn tại hay không.
3. **Khóa tài khoản:** Tự động khóa 15 phút sau 5 lần nhập sai liên tiếp (Trả về HTTP 429).

## 🚀 Hướng dẫn chạy:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.seed
uvicorn main:app --reload
```

- Swagger UI: `http://127.0.0.1:8000/docs`

## 🧪 Chạy Test:

```powershell
python -m pytest tests/ -v
```
