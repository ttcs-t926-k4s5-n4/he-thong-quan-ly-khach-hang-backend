import os

from dotenv import load_dotenv
from fastapi import APIRouter, Request, Response

from app.db import fetch_one, get_connection
from app.security import (
    SESSION_TTL,
    clear_session_cookie,
    hash_token,
    new_session_token,
    now,
    set_session_cookie,
    unauthorized,
    verify_password,
)

load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["Xác thực"])
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


def current_user(request: Request):
    token = request.cookies.get("session")

    if not token:
        unauthorized(
            "Phiên đăng nhập đã hết hạn hoặc không hợp lệ, vui lòng đăng nhập lại."
        )

    connection = get_connection()
    try:
        cursor = connection.cursor()
        user = fetch_one(
            cursor,
            '''
            SELECT
                s.id AS session_id,
                s.user_id,
                s.expires_at,
                s.revoked_at,
                u.email,
                u.role,
                u.is_active
            FROM dbo.sessions AS s
            INNER JOIN dbo.users AS u ON u.id = s.user_id
            WHERE s.token_hash = ?
            ''',
            (hash_token(token),),
        )

        if (
            user is None
            or user["revoked_at"] is not None
            or int(user["expires_at"]) <= now()
            or not bool(user["is_active"])
        ):
            unauthorized(
                "Phiên đăng nhập đã hết hạn hoặc không hợp lệ, vui lòng đăng nhập lại."
            )

        cursor.execute(
            "UPDATE dbo.sessions SET expires_at = ? WHERE id = ?",
            (now() + SESSION_TTL, user["session_id"]),
        )
        connection.commit()
        return user
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@router.post("/login")
def login(payload: dict, response: Response):
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))

    if not email or not password:
        response.status_code = 401
        return {"message": "Email hoặc mật khẩu không đúng."}

    connection = get_connection()
    try:
        cursor = connection.cursor()

        user = fetch_one(
            cursor,
            '''
            SELECT id, email, password_hash, role, is_active
            FROM dbo.users
            WHERE LOWER(email) = LOWER(?)
            ''',
            (email,),
        )

        if user is None or not verify_password(
            password,
            str(user["password_hash"]),
        ):
            response.status_code = 401
            return {"message": "Email hoặc mật khẩu không đúng."}

        if not bool(user["is_active"]):
            response.status_code = 403
            return {"message": "Tài khoản đã bị khóa."}

        # Khóa hàng người dùng khi tạo phiên để không tạo phiên đồng thời
        # với thao tác khóa tài khoản.
        locked_user = fetch_one(
            cursor,
            '''
            SELECT id, is_active
            FROM dbo.users WITH (UPDLOCK, ROWLOCK)
            WHERE id = ?
            ''',
            (user["id"],),
        )

        if locked_user is None or not bool(locked_user["is_active"]):
            response.status_code = 403
            return {"message": "Tài khoản đã bị khóa."}

        token = new_session_token()
        timestamp = now()

        cursor.execute(
            '''
            INSERT INTO dbo.sessions(
                user_id,
                token_hash,
                created_at,
                expires_at,
                revoked_at
            )
            VALUES (?, ?, ?, ?, NULL)
            ''',
            (
                user["id"],
                hash_token(token),
                timestamp,
                timestamp + SESSION_TTL,
            ),
        )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    set_session_cookie(response, token, COOKIE_SECURE)

    return {
        "message": "Đăng nhập thành công và khởi tạo phiên.",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
        },
    }


@router.get("/me")
def me(request: Request):
    user = current_user(request)
    return {
        "authenticated": True,
        "user": {
            "id": user["user_id"],
            "email": user["email"],
            "role": user["role"],
        },
    }


@router.post("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get("session")

    if token:
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                '''
                UPDATE dbo.sessions
                SET revoked_at = ?
                WHERE token_hash = ?
                  AND revoked_at IS NULL
                ''',
                (now(), hash_token(token)),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    clear_session_cookie(response)

    return {
        "message": "Đăng xuất thành công. Phiên đã bị hủy phía server."
    }
