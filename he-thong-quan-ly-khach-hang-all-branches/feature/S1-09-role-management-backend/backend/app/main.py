import os

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import BusinessGroup, Role, User
from app.rules import RoleAssignmentError, validate_role_assignment
from app.schemas import (
    BusinessGroupOut,
    RoleAssignmentIn,
    RoleOut,
    UserOut,
)

app = FastAPI(
    title="S1-09 - Quản lý vai trò và nhóm kinh doanh",
    version="1.0.0",
    description=(
        "API cho phép một người dùng giữ nhiều vai trò, bắt buộc Trưởng nhóm "
        "phải thuộc một nhóm kinh doanh, và chặn quản trị viên tự thu hồi "
        "vai trò Quản trị của chính mình."
    ),
)

origins = [
    item.strip()
    for item in os.getenv(
        "FRONTEND_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    ).split(",")
    if item.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "s1-09-role-management-backend"}


@app.get("/api/roles", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db)):
    return db.scalars(select(Role).order_by(Role.id)).all()


@app.get("/api/business-groups", response_model=list[BusinessGroupOut])
def list_business_groups(db: Session = Depends(get_db)):
    return db.scalars(select(BusinessGroup).order_by(BusinessGroup.id)).all()


@app.get("/api/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    statement = (
        select(User)
        .options(
            selectinload(User.roles),
            selectinload(User.business_group),
        )
        .order_by(User.id)
    )
    return db.scalars(statement).all()


@app.put("/api/users/{user_id}/role-assignment")
def update_role_assignment(
    user_id: int,
    payload: RoleAssignmentIn,
    x_current_user_id: int = Header(..., alias="X-Current-User-Id"),
    db: Session = Depends(get_db),
):
    statement = (
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id)
    )
    target_user = db.scalar(statement)

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng.",
        )

    roles = list(
        db.scalars(
            select(Role).where(Role.id.in_(payload.role_ids))
        ).all()
    )

    if len(roles) != len(set(payload.role_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Danh sách vai trò không hợp lệ.",
        )

    selected_codes = {role.code for role in roles}
    current_codes = {role.code for role in target_user.roles}

    if payload.business_group_id is not None:
        group = db.get(BusinessGroup, payload.business_group_id)
        if group is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nhóm kinh doanh không tồn tại.",
            )

    try:
        validate_role_assignment(
            current_admin_id=x_current_user_id,
            target_user_id=target_user.id,
            current_role_codes=current_codes,
            selected_role_codes=selected_codes,
            business_group_id=payload.business_group_id,
        )
    except RoleAssignmentError as error:
        message = str(error)
        http_status = (
            status.HTTP_403_FORBIDDEN
            if "tự thu hồi" in message
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=http_status,
            detail=message,
        ) from error

    target_user.roles = roles
    target_user.business_group_id = payload.business_group_id

    db.commit()

    return {
        "message": "Đã cập nhật vai trò và nhóm kinh doanh.",
        "user_id": target_user.id,
        "role_ids": payload.role_ids,
        "business_group_id": payload.business_group_id,
    }
