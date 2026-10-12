"""Phân quyền theo vai trò và phạm vi dữ liệu (thống nhất với SCRUM-29).

- Nhân viên kinh doanh: chỉ thấy dữ liệu do mình sở hữu.
- Trưởng nhóm: thấy dữ liệu của mọi thành viên trong nhóm.
- Giám đốc kinh doanh, Quản trị hệ thống: thấy toàn bộ.
"""
from __future__ import annotations

from app.errors import Forbidden

ROLE_RANK = {"staff": 1, "team_lead": 2, "director": 3, "admin": 4}


def rank(user: dict) -> int:
    return ROLE_RANK.get(user["role"], 0)


def at_least(user: dict, role: str) -> bool:
    """Người dùng có vai trò từ `role` trở lên hay không."""
    return rank(user) >= ROLE_RANK[role]


def require_role(user: dict, role: str, message: str) -> None:
    if not at_least(user, role):
        raise Forbidden(message)


def sees_everything(user: dict) -> bool:
    return user["role"] in ("director", "admin")


def owner_scope(user: dict, column: str) -> tuple[str, list]:
    """Điều kiện SQL giới hạn dữ liệu theo người sở hữu (`column` là cột id người sở hữu)."""
    if sees_everything(user):
        return "1=1", []
    if user["role"] == "team_lead" and user.get("team_id"):
        return f"{column} IN (SELECT id FROM users WHERE team_id = ?)", [user["team_id"]]
    return f"{column} = ?", [user["id"]]


def can_access_owner(user: dict, owner: dict) -> bool:
    """Người dùng có được thấy/thao tác dữ liệu do `owner` sở hữu không."""
    if sees_everything(user) or owner["id"] == user["id"]:
        return True
    return (user["role"] == "team_lead" and user.get("team_id") is not None
            and owner.get("team_id") == user["team_id"])


def scope_label(user: dict) -> str:
    if sees_everything(user):
        return "Toàn công ty"
    if user["role"] == "team_lead" and user.get("team_id"):
        return f"Nhóm {user.get('team_name') or ''}".strip()
    return "Của tôi"
