"""Cấu hình ứng dụng. Có thể ghi đè bằng biến môi trường."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    # Khoá ký token đăng nhập – BẮT BUỘC đổi khi triển khai thật (biến môi trường CRM_SECRET_KEY)
    SECRET_KEY = os.environ.get("CRM_SECRET_KEY", "hay-doi-khoa-bi-mat-nay-truoc-khi-trien-khai")
    # Đường dẫn file CSDL SQLite
    DATABASE = os.environ.get("CRM_DATABASE", str(BASE_DIR / "instance" / "crm.sqlite3"))
    # Thời hạn token đăng nhập (giây), mặc định 8 giờ
    TOKEN_MAX_AGE_SECONDS = int(os.environ.get("CRM_TOKEN_MAX_AGE", 8 * 60 * 60))
    # Tự tạo bảng và dữ liệu mẫu khi khởi động nếu CSDL còn trống
    AUTO_INIT_DB = os.environ.get("CRM_AUTO_INIT_DB", "1") == "1"
