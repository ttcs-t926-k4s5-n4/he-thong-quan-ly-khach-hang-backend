from fastapi import FastAPI, Request
from .db import init_db
from .auth import router as auth_router

app = FastAPI(
    title="S1-01 Login Backend",
    version="1.0.0",
    description="Backend API phục vụ Yêu cầu S1-01: Đăng nhập & Bảo mật khóa tài khoản."
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(auth_router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "login-backend"}

@app.get("/api/home")
def home(role: str = "user"):
    return {
        "message": f"Chào mừng bạn đến với Trang chủ ({role}).",
        "role": role
    }
