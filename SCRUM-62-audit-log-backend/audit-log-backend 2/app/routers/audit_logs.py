"""
Audit Log Router - API endpoints cho nhật ký thay đổi
SCRUM-62: Nhật ký thay đổi trên dữ liệu nhạy cảm

Endpoints:
  POST   /api/audit-logs          - Tạo bản ghi audit log
  GET    /api/audit-logs          - Lấy danh sách (có lọc + phân trang)
  GET    /api/audit-logs/{id}     - Lấy chi tiết một bản ghi
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ObjectType, ActionType
from app.schemas import (
    AuditLogCreate,
    AuditLogResponse,
    AuditLogFilter,
    AuditLogListResponse,
)
from app.services.audit_service import (
    create_audit_log,
    get_audit_logs,
    get_audit_log_by_id,
)

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


@router.post("/", response_model=AuditLogResponse, status_code=201)
def create_log(audit_data: AuditLogCreate, db: Session = Depends(get_db)):
    """
    Tạo một bản ghi nhật ký thay đổi mới.

    Sử dụng khi có bất kỳ thay đổi nào trên:
    - Chiết khấu (discount)
    - Chỉ tiêu (quota)
    - Quyền sở hữu dữ liệu (data_ownership)
    - Vai trò người dùng (user_role)
    """
    try:
        log = create_audit_log(db, audit_data)
        return log
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=AuditLogListResponse)
def list_logs(
    user_id: Optional[int] = Query(None, description="Lọc theo ID người dùng"),
    object_type: Optional[ObjectType] = Query(None, description="Lọc theo loại đối tượng"),
    action: Optional[ActionType] = Query(None, description="Lọc theo loại hành động"),
    start_date: Optional[datetime] = Query(None, description="Lọc từ ngày (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Lọc đến ngày (ISO 8601)"),
    object_id: Optional[int] = Query(None, description="Lọc theo ID đối tượng"),
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100, description="Số bản ghi mỗi trang"),
    db: Session = Depends(get_db),
):
    """
    Lấy danh sách nhật ký thay đổi có phân trang.

    Hỗ trợ lọc theo:
    - **user_id**: Người thực hiện thay đổi
    - **object_type**: Loại đối tượng (discount, quota, data_ownership, user_role)
    - **action**: Loại hành động (create, update, delete)
    - **start_date / end_date**: Khoảng thời gian
    - **object_id**: ID đối tượng cụ thể
    """
    filters = AuditLogFilter(
        user_id=user_id,
        object_type=object_type,
        action=action,
        start_date=start_date,
        end_date=end_date,
        object_id=object_id,
    )

    items, total = get_audit_logs(db, filters, page, page_size)

    return AuditLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.get("/{log_id}", response_model=AuditLogResponse)
def get_log_detail(log_id: int, db: Session = Depends(get_db)):
    """Lấy chi tiết một bản ghi nhật ký thay đổi theo ID."""
    log = get_audit_log_by_id(db, log_id)
    if not log:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy audit log với ID: {log_id}"
        )
    return log
