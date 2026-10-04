import os

from dotenv import load_dotenv

from app.db import fetch_one, get_connection
from app.security import hash_password

load_dotenv()


def create_user_if_missing(
    cursor,
    email: str,
    password: str,
    role: str,
):
    existing = fetch_one(
        cursor,
        "SELECT id FROM dbo.users WHERE LOWER(email) = LOWER(?)",
        (email,),
    )

    if existing is not None:
        return existing["id"]

    cursor.execute(
        '''
        INSERT INTO dbo.users(
            email,
            password_hash,
            role,
            is_active
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, 1)
        ''',
        (email, hash_password(password), role),
    )

    return int(cursor.fetchone()[0])


def seed():
    admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@company.vn")
    admin_password = os.getenv("SEED_ADMIN_PASSWORD")
    source_email = os.getenv(
        "SEED_SOURCE_EMAIL",
        "employee.old@company.vn",
    )
    source_password = os.getenv("SEED_SOURCE_PASSWORD")
    receiver_email = os.getenv(
        "SEED_RECEIVER_EMAIL",
        "employee.new@company.vn",
    )
    receiver_password = os.getenv("SEED_RECEIVER_PASSWORD")

    if not admin_password:
        raise RuntimeError("Cần đặt SEED_ADMIN_PASSWORD trong .env.")
    if not source_password:
        raise RuntimeError("Cần đặt SEED_SOURCE_PASSWORD trong .env.")
    if not receiver_password:
        raise RuntimeError("Cần đặt SEED_RECEIVER_PASSWORD trong .env.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        admin_id = create_user_if_missing(
            cursor,
            admin_email,
            admin_password,
            "admin",
        )
        source_id = create_user_if_missing(
            cursor,
            source_email,
            source_password,
            "user",
        )
        receiver_id = create_user_if_missing(
            cursor,
            receiver_email,
            receiver_password,
            "user",
        )

        # Dữ liệu mẫu chỉ tạo khi chưa có để dễ kiểm thử việc bàn giao.
        customer = fetch_one(
            cursor,
            '''
            SELECT TOP 1 id
            FROM dbo.customers
            WHERE owner_id = ?
            ''',
            (source_id,),
        )
        if customer is None:
            cursor.execute(
                '''
                INSERT INTO dbo.customers(name, owner_id)
                VALUES (?, ?)
                ''',
                ("Khách hàng mẫu", source_id),
            )

        opportunity = fetch_one(
            cursor,
            '''
            SELECT TOP 1 id
            FROM dbo.opportunities
            WHERE owner_id = ?
            ''',
            (source_id,),
        )
        if opportunity is None:
            cursor.execute(
                '''
                INSERT INTO dbo.opportunities(title, owner_id)
                VALUES (?, ?)
                ''',
                ("Cơ hội mẫu", source_id),
            )

        connection.commit()

        print("Đã tạo dữ liệu kiểm thử S1-10.")
        print(f"Admin ID: {admin_id}")
        print(f"Nhân viên nghỉ ID: {source_id}")
        print(f"Người tiếp nhận ID: {receiver_id}")

    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    seed()
