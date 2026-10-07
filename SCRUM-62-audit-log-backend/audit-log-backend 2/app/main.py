"""
Audit Log Backend - Main Application
SCRUM-62: Là Quản trị hệ thống, tôi muốn xem nhật ký thay đổi trên dữ liệu nhạy cảm,
          để truy được ai đã sửa chiết khấu hoặc chỉ tiêu khi cuối quý số liệu không khớp.

Chức năng:
  - Ghi lại mọi thay đổi trên chiết khấu, chỉ tiêu, quyền sở hữu dữ liệu và vai trò người dùng
  - Mỗi bản ghi có người thực hiện, thời điểm, giá trị trước và sau
  - Lọc theo người dùng, loại đối tượng, khoảng thời gian

Chạy server:
  uvicorn app.main:app --reload

Swagger UI:
  http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import audit_logs, users

# Tạo tất cả bảng trong database (nếu chưa tồn tại)
Base.metadata.create_all(bind=engine)

# Khởi tạo FastAPI app
app = FastAPI(
    title="Audit Log System",
    description=(
        "Hệ thống nhật ký thay đổi dữ liệu nhạy cảm (SCRUM-62).\n\n"
        "Theo dõi các thay đổi trên: chiết khấu, chỉ tiêu, quyền sở hữu dữ liệu, vai trò người dùng.\n\n"
        "Mỗi bản ghi gồm: người thực hiện, thời điểm, giá trị trước/sau, mô tả."
    ),
    version="1.0.0",
)

# Cấu hình CORS - cho phép frontend kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production: thay bằng domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các router
app.include_router(users.router)
app.include_router(audit_logs.router)


@app.get("/", tags=["Health Check"])
def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Audit Log System",
        "version": "1.0.0",
        "docs": "/docs",
    }
