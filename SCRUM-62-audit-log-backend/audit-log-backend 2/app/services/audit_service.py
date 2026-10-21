"""
Audit Service - Logic xử lý nghiệp vụ cho Audit Log
SCRUM-62: Nhật ký thay đổi trên dữ liệu nhạy cảm
"""

from datetime import datetime
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.models import AuditLog, User, ObjectType, ActionType
from app.schemas import AuditLogCreate, AuditLogFilter


def create_audit_log(db: Session, audit_data: AuditLogCreate) -> AuditLog:
    """
    Tạo một bản ghi audit log mới.
    Được gọi mỗi khi có thay đổi trên dữ liệu nhạy cảm.
    """
    # Kiểm tra user có tồn tại không
    user = db.query(User).filter(User.id == audit_data.user_id).first()
    if not user:
        raise ValueError(f"Không tìm thấy người dùng với ID: {audit_data.user_id}")

    db_audit_log = AuditLog(
        user_id=audit_data.user_id,
        action=audit_data.action,
        object_type=audit_data.object_type,
        object_id=audit_data.object_id,
        field_name=audit_data.field_name,
        old_value=audit_data.old_value,
        new_value=audit_data.new_value,
        description=audit_data.description,
        ip_address=audit_data.ip_address,
    )

    db.add(db_audit_log)
    db.commit()
    db.refresh(db_audit_log)
    return db_audit_log


def get_audit_logs(
    db: Session,
    filters: AuditLogFilter,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[AuditLog], int]:
    """
    Lấy danh sách audit log có phân trang và bộ lọc.

    Bộ lọc hỗ trợ:
    - user_id: Lọc theo người thực hiện
    - object_type: Lọc theo loại đối tượng (discount, quota, ...)
    - action: Lọc theo loại hành động (create, update, delete)
    - start_date / end_date: Lọc theo khoảng thời gian
    - object_id: Lọc theo ID đối tượng cụ thể
    """
    query = db.query(AuditLog).options(joinedload(AuditLog.user))

    # Xây dựng danh sách điều kiện lọc
    conditions = []

    if filters.user_id is not None:
        conditions.append(AuditLog.user_id == filters.user_id)

    if filters.object_type is not None:
        conditions.append(AuditLog.object_type == filters.object_type)

    if filters.action is not None:
        conditions.append(AuditLog.action == filters.action)

    if filters.start_date is not None:
        conditions.append(AuditLog.created_at >= filters.start_date)

    if filters.end_date is not None:
        conditions.append(AuditLog.created_at <= filters.end_date)

    if filters.object_id is not None:
        conditions.append(AuditLog.object_id == filters.object_id)

    # Áp dụng tất cả điều kiện
    if conditions:
        query = query.filter(and_(*conditions))

    # Đếm tổng số bản ghi (trước phân trang)
    total = query.count()

    # Sắp xếp theo thời gian mới nhất và phân trang
    items = (
        query
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return items, total


def get_audit_log_by_id(db: Session, log_id: int) -> Optional[AuditLog]:
    """Lấy chi tiết một bản ghi audit log theo ID."""
    return (
        db.query(AuditLog)
        .options(joinedload(AuditLog.user))
        .filter(AuditLog.id == log_id)
        .first()
    )
