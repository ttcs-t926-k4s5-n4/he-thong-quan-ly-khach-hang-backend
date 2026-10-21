"""
Database Models - Các bảng trong cơ sở dữ liệu
SCRUM-62: Nhật ký thay đổi trên dữ liệu nhạy cảm
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.database import Base


# ==================== ENUM DEFINITIONS ====================

class UserRole(str, enum.Enum):
    """Vai trò người dùng trong hệ thống"""
    ADMIN = "admin"              # Quản trị hệ thống
    MANAGER = "manager"          # Quản lý
    SALES = "sales"              # Nhân viên kinh doanh
    ACCOUNTANT = "accountant"    # Kế toán


class ObjectType(str, enum.Enum):
    """Loại đối tượng được theo dõi thay đổi"""
    DISCOUNT = "discount"            # Chiết khấu
    QUOTA = "quota"                  # Chỉ tiêu
    DATA_OWNERSHIP = "data_ownership"  # Quyền sở hữu dữ liệu
    USER_ROLE = "user_role"          # Vai trò người dùng


class ActionType(str, enum.Enum):
    """Loại hành động"""
    CREATE = "create"    # Tạo mới
    UPDATE = "update"    # Cập nhật
    DELETE = "delete"    # Xóa


# ==================== DATABASE MODELS ====================

class User(Base):
    """Bảng người dùng"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.SALES)
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship: Một user có nhiều audit log
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class AuditLog(Base):
    """
    Bảng nhật ký thay đổi (Audit Log)
    Ghi lại mọi thay đổi trên dữ liệu nhạy cảm:
    - Chiết khấu (discount)
    - Chỉ tiêu (quota)
    - Quyền sở hữu dữ liệu (data_ownership)
    - Vai trò người dùng (user_role)
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Người thực hiện thay đổi
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Loại hành động: create, update, delete
    action = Column(SAEnum(ActionType), nullable=False)

    # Loại đối tượng bị thay đổi: discount, quota, data_ownership, user_role
    object_type = Column(SAEnum(ObjectType), nullable=False, index=True)

    # ID của đối tượng bị thay đổi (ví dụ: discount_id, user_id bị đổi role...)
    object_id = Column(Integer, nullable=False)

    # Tên trường bị thay đổi (ví dụ: "discount_percentage", "quota_amount")
    field_name = Column(String(255), nullable=True)

    # Giá trị trước khi thay đổi (lưu dạng text để linh hoạt)
    old_value = Column(Text, nullable=True)

    # Giá trị sau khi thay đổi
    new_value = Column(Text, nullable=True)

    # Mô tả ngắn về thay đổi
    description = Column(Text, nullable=True)

    # Địa chỉ IP của người thực hiện
    ip_address = Column(String(45), nullable=True)

    # Thời điểm thay đổi
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return (
            f"<AuditLog(id={self.id}, user_id={self.user_id}, "
            f"action='{self.action}', object_type='{self.object_type}')>"
        )
