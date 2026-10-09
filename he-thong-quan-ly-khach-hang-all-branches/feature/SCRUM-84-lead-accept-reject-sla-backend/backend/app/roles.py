"""
roles.py — Phân quyền dữ liệu (S1-05) & Quản lý vai trò (S1-09)
"""
from typing import Any

from app.auth import CurrentUser, ROLE_LABEL, ROLE_HOME


# ── Data scopes per role (S1-05) ─────────────────────────────────────────────

ROLE_SCOPES = {
    "admin": {
        "label": "Quản trị hệ thống",
        "can_view_all_data": True,
        "can_manage_users": True,
        "can_manage_roles": True,
        "can_export": True,
        "can_handover": True,
        "description": "Truy cập toàn bộ dữ liệu: tất cả, cơ hội, hoạt động, báo giá.",
    },
    "manager": {
        "label": "Giám đốc kinh doanh",
        "can_view_all_data": True,
        "can_view_team": True,
        "can_manage_users": False,
        "can_manage_roles": False,
        "can_export": True,
        "can_handover": False,
        "description": "Xem dữ liệu của mình, nhóm và toàn công ty. Có thể xuất Excel.",
    },
    "employee": {
        "label": "Nhân viên kinh doanh",
        "can_view_own_data": True,
        "can_manage_users": False,
        "can_manage_roles": False,
        "can_export": False,
        "can_handover": False,
        "description": "Chỉ xem dữ liệu của chính mình.",
    },
}

# Menu items theo vai trò (S1-06)
ROLE_MENUS = {
    "admin": [
        {"key": "dashboard", "label": "Tổng quan", "icon": "📊", "path": "/dashboard/admin"},
        {"key": "users", "label": "Quản lý tài khoản", "icon": "👥", "path": "/users"},
        {"key": "roles", "label": "Quản lý vai trò", "icon": "🔑", "path": "/roles"},
        {"key": "change-password", "label": "Đổi mật khẩu", "icon": "🔒", "path": "/change-password"},
    ],
    "manager": [
        {"key": "dashboard", "label": "Tổng quan", "icon": "📊", "path": "/dashboard/manager"},
        {"key": "change-password", "label": "Đổi mật khẩu", "icon": "🔒", "path": "/change-password"},
    ],
    "employee": [
        {"key": "dashboard", "label": "Tổng quan", "icon": "📊", "path": "/dashboard/employee"},
        {"key": "change-password", "label": "Đổi mật khẩu", "icon": "🔒", "path": "/change-password"},
    ],
}


def get_user_profile(user: CurrentUser) -> dict[str, Any]:
    """Trả về profile + scope + menu cho user đang đăng nhập (S1-05, S1-06)."""
    scope = ROLE_SCOPES.get(user.role, {})
    menu = ROLE_MENUS.get(user.role, [])
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "role_label": ROLE_LABEL.get(user.role, user.role),
        },
        "scope": scope,
        "menu": menu,
        "home_url": ROLE_HOME.get(user.role, "/dashboard/employee"),
    }
