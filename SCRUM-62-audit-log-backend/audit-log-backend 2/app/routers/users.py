"""
Users Router - API endpoints quản lý người dùng
Hỗ trợ tạo user mẫu để test audit log.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Tạo người dùng mới."""
    # Kiểm tra username đã tồn tại chưa
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Username '{user_data.username}' đã tồn tại")

    # Kiểm tra email đã tồn tại chưa
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail=f"Email '{user_data.email}' đã tồn tại")

    db_user = User(
        username=user_data.username,
        full_name=user_data.full_name,
        email=user_data.email,
        role=user_data.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    """Lấy danh sách tất cả người dùng."""
    return db.query(User).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Lấy thông tin một người dùng theo ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy user với ID: {user_id}")
    return user
