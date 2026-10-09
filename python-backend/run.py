"""Chạy server: python run.py  (mặc định http://127.0.0.1:8000)"""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"CRM Lead & Marketing (Python) chạy tại http://{host}:{port}")
    print("Các feature đã nạp:", ", ".join(f["key"] for f in app.config["FEATURES"]) or "(không có)")
    app.run(host=host, port=port, debug=os.getenv("FLASK_DEBUG", "0") == "1")
