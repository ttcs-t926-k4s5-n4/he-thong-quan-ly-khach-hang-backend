"""Chạy nhanh: python run.py  (tự tạo CSDL mẫu nếu chưa có)."""
import os

from app import create_app
from app.db import init_db

app = create_app()

if __name__ == "__main__":
    if not os.path.exists(app.config["DATABASE"]):
        with app.app_context():
            init_db()
            print("Đã tạo CSDL mẫu tại", app.config["DATABASE"])
    app.run(debug=True)
