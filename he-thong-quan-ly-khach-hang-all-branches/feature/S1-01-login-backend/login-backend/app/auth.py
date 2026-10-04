from fastapi import APIRouter, Response
from .db import get_connection
from .security import (
    MAX_ATTEMPTS, LOCKOUT_WINDOW, now,
    verify_password
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

def is_locked(email: str) -> bool:
    cutoff = now() - LOCKOUT_WINDOW
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM login_attempts "
        "WHERE email=? AND success=0 AND attempted_at>=?",
        (email.lower(), cutoff)
    ).fetchone()
    conn.close()
    return row["count"] >= MAX_ATTEMPTS

def record_attempt(email: str, success: bool):
    conn = get_connection()
    conn.execute(
        "INSERT INTO login_attempts(email, attempted_at, success) VALUES(?,?,?)",
        (email.lower(), now(), 1 if success else 0)
    )
    if success:
        conn.execute(
            "DELETE FROM login_attempts WHERE email=? AND success=0",
            (email.lower(),)
        )
    conn.commit()
    conn.close()

@router.post("/login")
def login(payload: dict, response: Response):
    """
    S1-01: Đăng nhập bằng Email & Mật khẩu
    - Đăng nhập đúng: trả về thông tin user kèm vai trò (role).
    - Sai thông tin: hiển thị thông báo chung, không tiết lộ email có tồn tại hay không.
    - Nhập sai 5 lần liên tiếp: khóa tài khoản tạm thời 15 phút (Mã 429).
    """
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    generic_error = {"message": "Email hoặc mật khẩu không đúng."}

    if not email or not password:
        response.status_code = 401
        return generic_error

    if is_locked(email):
        response.status_code = 429
        return {"message": "Tài khoản tạm thời bị khóa. Vui lòng thử lại sau."}

    conn = get_connection()
    user = conn.execute(
        "SELECT id, email, password_hash, role FROM users WHERE email=?",
        (email,)
    ).fetchone()
    conn.close()

    if not user or not verify_password(password, user["password_hash"]):
        record_attempt(email, False)
        response.status_code = 401
        return generic_error

    record_attempt(email, True)

    return {
        "message": "Đăng nhập thành công.",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"]
        },
        "redirect_url": f"/home/{user['role']}"
    }
