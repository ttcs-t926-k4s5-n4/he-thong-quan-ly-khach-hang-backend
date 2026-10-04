from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.auth import current_user
from app.db import fetch_one, get_connection
from app.security import now

router = APIRouter(
    prefix="/api/admin",
    tags=["Bàn giao và khóa tài khoản"],
)


class HandoverAndLockRequest(BaseModel):
    from_user_id: int = Field(gt=0)
    to_user_id: int = Field(gt=0)


@router.post("/handover-and-lock")
def handover_and_lock(
    payload: HandoverAndLockRequest,
    request: Request,
):
    admin = current_user(request)

    if admin["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Chỉ Quản trị hệ thống được bàn giao và khóa tài khoản.",
        )

    if payload.from_user_id == payload.to_user_id:
        raise HTTPException(
            status_code=400,
            detail="Người tiếp nhận phải khác người bị khóa.",
        )

    if payload.from_user_id == admin["user_id"]:
        raise HTTPException(
            status_code=400,
            detail="Không thể tự khóa tài khoản đang sử dụng.",
        )

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Khóa hai bản ghi người dùng trong transaction để tránh xung đột.
        cursor.execute(
            '''
            SELECT id, is_active
            FROM dbo.users WITH (UPDLOCK, ROWLOCK)
            WHERE id IN (?, ?)
            ORDER BY id
            ''',
            (payload.from_user_id, payload.to_user_id),
        )

        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        users = {
            dict(zip(columns, row, strict=True))["id"]:
            dict(zip(columns, row, strict=True))
            for row in rows
        }

        source_user = users.get(payload.from_user_id)
        receiver_user = users.get(payload.to_user_id)

        if source_user is None or not bool(source_user["is_active"]):
            raise HTTPException(
                status_code=400,
                detail="Tài khoản cần khóa không tồn tại hoặc đã bị khóa.",
            )

        if receiver_user is None or not bool(receiver_user["is_active"]):
            raise HTTPException(
                status_code=400,
                detail="Người tiếp nhận không tồn tại hoặc đã bị khóa.",
            )

        # 1. Chuyển toàn bộ khách hàng.
        cursor.execute(
            '''
            UPDATE dbo.customers
            SET owner_id = ?
            WHERE owner_id = ?
            ''',
            (payload.to_user_id, payload.from_user_id),
        )
        customer_count = cursor.rowcount

        # 2. Chuyển toàn bộ cơ hội.
        cursor.execute(
            '''
            UPDATE dbo.opportunities
            SET owner_id = ?
            WHERE owner_id = ?
            ''',
            (payload.to_user_id, payload.from_user_id),
        )
        opportunity_count = cursor.rowcount

        # 3. Ghi nhật ký bàn giao để giữ lịch sử chủ sở hữu.
        cursor.execute(
            '''
            INSERT INTO dbo.handover_logs(
                from_user_id,
                to_user_id,
                admin_id,
                customer_count,
                opportunity_count,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, SYSUTCDATETIME())
            ''',
            (
                payload.from_user_id,
                payload.to_user_id,
                admin["user_id"],
                customer_count,
                opportunity_count,
            ),
        )

        # 4. Khóa tài khoản cũ.
        cursor.execute(
            '''
            UPDATE dbo.users
            SET is_active = 0
            WHERE id = ?
            ''',
            (payload.from_user_id,),
        )

        # 5. Thu hồi ngay tất cả phiên còn mở của tài khoản cũ.
        cursor.execute(
            '''
            UPDATE dbo.sessions
            SET revoked_at = ?
            WHERE user_id = ?
              AND revoked_at IS NULL
            ''',
            (now(), payload.from_user_id),
        )

        connection.commit()

        return {
            "message": "Đã bàn giao dữ liệu và khóa tài khoản.",
            "customers_transferred": customer_count,
            "opportunities_transferred": opportunity_count,
        }

    except HTTPException:
        connection.rollback()
        raise
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
