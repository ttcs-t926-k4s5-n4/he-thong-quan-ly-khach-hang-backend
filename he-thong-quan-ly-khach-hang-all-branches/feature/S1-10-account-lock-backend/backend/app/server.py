from fastapi import FastAPI, Request

from app.account_lock import router as account_lock_router
from app.auth import current_user, router as auth_router

app = FastAPI(
    title="S1-10 - Bàn giao dữ liệu và khóa tài khoản",
    version="1.0.0",
    description=(
        "Backend cho User Story S1-10 của Hệ thống quản lý khách hàng. "
        "Hệ thống bắt buộc bàn giao khách hàng và cơ hội trước khi khóa tài khoản, "
        "ghi nhật ký bàn giao và thu hồi các phiên đang mở."
    ),
)

app.include_router(auth_router)
app.include_router(account_lock_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "s1-10-account-lock-backend",
    }


@app.get("/api/home")
def home(request: Request):
    user = current_user(request)
    return {
        "message": "Phiên đăng nhập hợp lệ.",
        "user": {
            "email": user["email"],
            "role": user["role"],
        },
    }
