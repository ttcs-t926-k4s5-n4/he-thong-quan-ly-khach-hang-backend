"""Chạy server: python run.py  (mặc định http://127.0.0.1:5000)."""
import os
import sys

from app import create_app

app = create_app()

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    host = os.environ.get("CRM_HOST", "127.0.0.1")
    port = int(os.environ.get("CRM_PORT", "5000"))
    print("=" * 70)
    print(" Backend CRM – SCRUM-87, 88, 89, 90, 99, 100")
    print(f" Danh mục API : http://{host}:{port}/api")
    print(" Đăng nhập    : POST /api/auth/login  (mật khẩu mẫu: 123456)")
    print(" Tài khoản    : giamdoc, truongnhom1, nhanvien1, nhanvien2, truongnhom2, nhanvien3, quantri")
    print(" Dừng server  : Ctrl + C")
    print("=" * 70)
    app.run(host=host, port=port, debug=os.environ.get("CRM_DEBUG") == "1")
