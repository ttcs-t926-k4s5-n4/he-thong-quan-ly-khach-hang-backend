"""Truy vấn dữ liệu — MỌI hàm đều bắt buộc nhận user và lọc qua
build_scope_filter(). Không có hàm nào đọc bản ghi mà bỏ qua phân quyền."""
import sqlite3
from typing import Optional

from . import messages
from .resources import Resource
from .scope import Scope, User, build_scope_filter, max_scope


def _select_clause(resource: Resource) -> str:
    cols = [f"t.{c} AS {c}" for c, _ in resource.columns]
    cols += ["t.owner_id AS owner_id", "u.full_name AS owner_name"]
    return ", ".join(cols)


def _where(resource: Resource, user: User, scope: Scope, q: Optional[str]):
    where, params = build_scope_filter(user, scope, owner_column="t.owner_id")
    clauses = [where]
    params = list(params)
    if q and q.strip():
        like = f"%{q.strip()}%"
        clauses.append("(" + " OR ".join(f"t.{f} LIKE ?" for f in resource.search_fields) + ")")
        params += [like] * len(resource.search_fields)
    return " AND ".join(clauses), params


def list_records(db: sqlite3.Connection, resource: Resource, user: User, scope: Scope,
                 q: Optional[str] = None, page: int = 1, page_size: int = 20,
                 paginate: bool = True):
    """Danh sách + tìm kiếm, đã lọc theo phạm vi. paginate=False dùng cho xuất Excel."""
    where, params = _where(resource, user, scope, q)
    base = f"FROM {resource.table} t JOIN users u ON u.id = t.owner_id WHERE {where}"

    total = db.execute(f"SELECT COUNT(*) {base}", params).fetchone()[0]
    sql = f"SELECT {_select_clause(resource)} {base} ORDER BY t.id"
    run_params = list(params)
    if paginate:
        sql += " LIMIT ? OFFSET ?"
        run_params += [page_size, (page - 1) * page_size]
    rows = [dict(r) for r in db.execute(sql, run_params).fetchall()]
    return rows, total


def get_record(db: sqlite3.Connection, resource: Resource, user: User, record_id: int):
    """Xem chi tiết. Luôn dùng phạm vi rộng nhất của vai trò.

    - Không tồn tại               -> 404
    - Tồn tại nhưng ngoài phạm vi -> 403 kèm thông báo tiếng Việt
    """
    exists = db.execute(f"SELECT 1 FROM {resource.table} WHERE id = ?",
                        (record_id,)).fetchone()
    if exists is None:
        raise messages.not_found(resource.label, record_id)

    scope = max_scope(user)
    where, params = build_scope_filter(user, scope, owner_column="t.owner_id")
    row = db.execute(
        f"SELECT {_select_clause(resource)} FROM {resource.table} t "
        f"JOIN users u ON u.id = t.owner_id WHERE t.id = ? AND {where}",
        [record_id, *params],
    ).fetchone()
    if row is None:
        raise messages.out_of_scope(resource.label, record_id, scope.value)
    return dict(row)
