"""
Pydantic Schemas - Định nghĩa cấu trúc dữ liệu request/response
SCRUM-62: Nhật ký thay đổi trên dữ liệu nhạy cảm
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models import UserRole, ObjectType, ActionType


# ==================== USER SCHEMAS ====================

class UserCreate(BaseModel):
    """Schema tạo user mới"""
    username: str = Field(..., min_length=3, max_length=100, description="Tên đăng nhập")
    full_name: str = Field(..., min_length=1, max_length=255, description="Họ và tên")
    email: str = Field(..., description="Email")
    role: UserRole = Field(default=UserRole.SALES, description="Vai trò")


class UserResponse(BaseModel):
    """Schema trả về thông tin user"""
    id: int
    username: str
    full_name: str
    email: str
    role: UserRole
    is_active: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== AUDIT LOG SCHEMAS ====================

class AuditLogCreate(BaseModel):
    """
    Schema tạo bản ghi audit log mới.
    Dùng khi ghi lại một thay đổi trên dữ liệu nhạy cảm.
    """
    user_id: int = Field(..., description="ID người thực hiện thay đổi")
    action: ActionType = Field(..., description="Loại hành động: create, update, delete")
    object_type: ObjectType = Field(..., description="Loại đối tượng: discount, quota, data_ownership, user_role")
    object_id: int = Field(..., description="ID đối tượng bị thay đổi")
    field_name: Optional[str] = Field(None, max_length=255, description="Tên trường bị thay đổi")
    old_value: Optional[str] = Field(None, description="Giá trị trước khi thay đổi")
    new_value: Optional[str] = Field(None, description="Giá trị sau khi thay đổi")
    description: Optional[str] = Field(None, description="Mô tả ngắn")
    ip_address: Optional[str] = Field(None, max_length=45, description="Địa chỉ IP")


class AuditLogResponse(BaseModel):
    """Schema trả về thông tin audit log"""
    id: int
    user_id: int
    action: ActionType
    object_type: ObjectType
    object_id: int
    field_name: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    description: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    # Thông tin người thực hiện (join từ bảng users)
    user: Optional[UserResponse] = None

    model_config = {"from_attributes": True}


class AuditLogFilter(BaseModel):
    """
    Schema bộ lọc audit log.
    Lọc theo: người dùng, loại đối tượng, khoảng thời gian.
    """
    user_id: Optional[int] = Field(None, description="Lọc theo ID người dùng")
    object_type: Optional[ObjectType] = Field(None, description="Lọc theo loại đối tượng")
    action: Optional[ActionType] = Field(None, description="Lọc theo loại hành động")
    start_date: Optional[datetime] = Field(None, description="Lọc từ ngày (bao gồm)")
    end_date: Optional[datetime] = Field(None, description="Lọc đến ngày (bao gồm)")
    object_id: Optional[int] = Field(None, description="Lọc theo ID đối tượng cụ thể")


class AuditLogListResponse(BaseModel):
    """Schema trả về danh sách audit log có phân trang"""
    total: int = Field(..., description="Tổng số bản ghi")
    page: int = Field(..., description="Trang hiện tại")
    page_size: int = Field(..., description="Số bản ghi mỗi trang")
    items: List[AuditLogResponse] = Field(..., description="Danh sách audit log")
