"""Lõi phân quyền dữ liệu: vai trò (role) + dữ liệu sở hữu (owner).

Quy tắc:
  - Nhân viên     -> tối đa phạm vi MINE : chỉ bản ghi có owner_id = chính mình
  - Trưởng nhóm   -> tối đa phạm vi TEAM : bản ghi của mọi thành viên cùng team
  - Giám đốc KD   -> tối đa phạm vi ALL  : toàn bộ bản ghi

Người dùng có thể chủ động chọn phạm vi HẸP hơn (ví dụ Giám đốc xem "Của tôi"),
nhưng không bao giờ được chọn phạm vi RỘNG hơn vai trò cho phép.

Mọi truy vấn danh sách / tìm kiếm / xuất Excel / xem chi tiết đều phải đi qua
build_scope_filter() — đây là điểm kiểm soát duy nhất.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from . import messages


class Role(str, Enum):
    NHAN_VIEN = "NHAN_VIEN"
    TRUONG_NHOM = "TRUONG_NHOM"
    GIAM_DOC = "GIAM_DOC"


class Scope(str, Enum):
    MINE = "mine"
    TEAM = "team"
    ALL = "all"


SCOPE_RANK = {Scope.MINE: 1, Scope.TEAM: 2, Scope.ALL: 3}

ROLE_MAX_SCOPE = {
    Role.NHAN_VIEN: Scope.MINE,
    Role.TRUONG_NHOM: Scope.TEAM,
    Role.GIAM_DOC: Scope.ALL,
}


@dataclass(frozen=True)
class User:
    id: int
    username: str
    full_name: str
    role: Role
    team_id: Optional[int]


def max_scope(user: User) -> Scope:
    """Phạm vi rộng nhất mà vai trò của người dùng được phép."""
    return ROLE_MAX_SCOPE[user.role]


def available_scopes(user: User) -> List[Scope]:
    """Các phạm vi người dùng được chọn (để frontend hiển thị bộ lọc)."""
    limit = SCOPE_RANK[max_scope(user)]
    return [s for s in Scope if SCOPE_RANK[s] <= limit]


def resolve_scope(user: User, requested: Optional[str]) -> Scope:
    """Xác định phạm vi thực tế cho một truy vấn.

    - Không truyền -> dùng phạm vi rộng nhất của vai trò.
    - Truyền giá trị lạ -> lỗi 400.
    - Truyền phạm vi rộng hơn vai trò -> lỗi 403.
    """
    allowed = max_scope(user)
    if requested is None or requested.strip() == "":
        return allowed
    try:
        scope = Scope(requested.strip().lower())
    except ValueError:
        raise messages.invalid_scope(requested)
    if SCOPE_RANK[scope] > SCOPE_RANK[allowed]:
        raise messages.scope_not_allowed(user.role.value, allowed.value, scope.value)
    return scope


def build_scope_filter(user: User, scope: Scope, owner_column: str = "owner_id"):
    """Trả về (mệnh đề WHERE, tham số) để lọc bản ghi theo phạm vi.

    owner_column chỉ nhận tên cột do code định nghĩa (không lấy từ người dùng),
    nên an toàn khi ghép chuỗi SQL. Giá trị luôn đi qua tham số '?'.
    """
    if scope == Scope.ALL:
        return "1 = 1", []
    if scope == Scope.TEAM and user.team_id is not None:
        return (f"{owner_column} IN (SELECT id FROM users WHERE team_id = ?)",
                [user.team_id])
    # MINE, hoặc TEAM nhưng người dùng chưa thuộc nhóm nào -> chỉ dữ liệu của mình
    return f"{owner_column} = ?", [user.id]
