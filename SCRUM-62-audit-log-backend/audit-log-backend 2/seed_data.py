"""
Seed Script - Tạo dữ liệu mẫu để test hệ thống Audit Log.
Chạy: python seed_data.py
"""

import sys
import os

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.database import SessionLocal, engine, Base
from app.models import User, AuditLog, UserRole, ObjectType, ActionType

# Tạo bảng
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # ==================== TẠO USERS MẪU ====================
    print("Đang tạo users mẫu...")

    users_data = [
        {"username": "admin_hoa", "full_name": "Nguyễn Thị Hoa", "email": "hoa@company.com", "role": UserRole.ADMIN},
        {"username": "mgr_minh", "full_name": "Trần Văn Minh", "email": "minh@company.com", "role": UserRole.MANAGER},
        {"username": "sales_nam", "full_name": "Lê Hải Nam", "email": "nam@company.com", "role": UserRole.SALES},
        {"username": "acc_linh", "full_name": "Phạm Thuỳ Linh", "email": "linh@company.com", "role": UserRole.ACCOUNTANT},
    ]

    users = []
    for data in users_data:
        existing = db.query(User).filter(User.username == data["username"]).first()
        if not existing:
            user = User(**data)
            db.add(user)
            db.flush()
            users.append(user)
            print(f"  + Tạo user: {data['full_name']} ({data['role'].value})")
        else:
            users.append(existing)
            print(f"  * User đã tồn tại: {data['full_name']}")

    db.commit()

    # ==================== TẠO AUDIT LOGS MẪU ====================
    print("\nĐang tạo audit logs mẫu...")

    now = datetime.utcnow()
    logs_data = [
        # Thay đổi chiết khấu
        {
            "user_id": users[1].id,  # Manager Minh
            "action": ActionType.UPDATE,
            "object_type": ObjectType.DISCOUNT,
            "object_id": 101,
            "field_name": "discount_percentage",
            "old_value": "10%",
            "new_value": "25%",
            "description": "Tăng chiết khấu cho khách hàng VIP ABC Corp",
            "ip_address": "192.168.1.50",
            "created_at": now - timedelta(days=5),
        },
        {
            "user_id": users[2].id,  # Sales Nam
            "action": ActionType.UPDATE,
            "object_type": ObjectType.DISCOUNT,
            "object_id": 102,
            "field_name": "discount_percentage",
            "old_value": "5%",
            "new_value": "30%",
            "description": "Điều chỉnh chiết khấu đơn hàng lớn - Công ty XYZ",
            "ip_address": "192.168.1.100",
            "created_at": now - timedelta(days=3),
        },
        # Thay đổi chỉ tiêu
        {
            "user_id": users[0].id,  # Admin Hoa
            "action": ActionType.UPDATE,
            "object_type": ObjectType.QUOTA,
            "object_id": 201,
            "field_name": "quota_amount",
            "old_value": "500000000",
            "new_value": "300000000",
            "description": "Giảm chỉ tiêu Q4 cho team Sales miền Nam",
            "ip_address": "192.168.1.10",
            "created_at": now - timedelta(days=2),
        },
        {
            "user_id": users[1].id,  # Manager Minh
            "action": ActionType.CREATE,
            "object_type": ObjectType.QUOTA,
            "object_id": 205,
            "field_name": None,
            "old_value": None,
            "new_value": "1000000000",
            "description": "Tạo chỉ tiêu mới cho team Sales miền Bắc Q1/2027",
            "ip_address": "192.168.1.50",
            "created_at": now - timedelta(days=1),
        },
        # Thay đổi quyền sở hữu dữ liệu
        {
            "user_id": users[0].id,  # Admin Hoa
            "action": ActionType.UPDATE,
            "object_type": ObjectType.DATA_OWNERSHIP,
            "object_id": 301,
            "field_name": "owner_id",
            "old_value": "user_3 (Lê Hải Nam)",
            "new_value": "user_2 (Trần Văn Minh)",
            "description": "Chuyển quyền sở hữu dữ liệu khách hàng khu vực HCM",
            "ip_address": "192.168.1.10",
            "created_at": now - timedelta(hours=12),
        },
        # Thay đổi vai trò người dùng
        {
            "user_id": users[0].id,  # Admin Hoa
            "action": ActionType.UPDATE,
            "object_type": ObjectType.USER_ROLE,
            "object_id": users[2].id,
            "field_name": "role",
            "old_value": "sales",
            "new_value": "manager",
            "description": "Nâng quyền Lê Hải Nam lên Manager",
            "ip_address": "192.168.1.10",
            "created_at": now - timedelta(hours=6),
        },
        # Xóa chiết khấu
        {
            "user_id": users[1].id,  # Manager Minh
            "action": ActionType.DELETE,
            "object_type": ObjectType.DISCOUNT,
            "object_id": 103,
            "field_name": None,
            "old_value": "15%",
            "new_value": None,
            "description": "Xóa chiết khấu hết hạn của đối tác DEF",
            "ip_address": "192.168.1.50",
            "created_at": now - timedelta(hours=2),
        },
    ]

    for data in logs_data:
        log = AuditLog(**data)
        db.add(log)
        print(f"  + [{data['action'].value.upper()}] {data['object_type'].value}: {data['description']}")

    db.commit()
    print(f"\n✅ Hoàn tất! Đã tạo {len(users)} users và {len(logs_data)} audit logs.")
    print("Chạy server: uvicorn app.main:app --reload")
    print("Xem API docs: http://localhost:8000/docs")

except Exception as e:
    db.rollback()
    print(f"❌ Lỗi: {e}")
    raise
finally:
    db.close()
