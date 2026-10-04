class RoleAssignmentError(ValueError):
    pass


def validate_role_assignment(
    *,
    current_admin_id: int,
    target_user_id: int,
    current_role_codes: set[str],
    selected_role_codes: set[str],
    business_group_id: int | None,
) -> None:
    # AC1: Cho phép nhiều vai trò cùng lúc.
    # Không giới hạn selected_role_codes chỉ còn một vai trò.

    # AC2: Trưởng nhóm bắt buộc phải thuộc một nhóm kinh doanh cụ thể.
    if "TEAM_LEADER" in selected_role_codes and business_group_id is None:
        raise RoleAssignmentError(
            "Người giữ vai trò Trưởng nhóm phải được gán vào một nhóm kinh doanh cụ thể."
        )

    # AC3: Quản trị viên không được tự thu hồi vai trò Quản trị của chính mình.
    is_self = current_admin_id == target_user_id
    removing_own_admin = (
        is_self
        and "ADMIN" in current_role_codes
        and "ADMIN" not in selected_role_codes
    )

    if removing_own_admin:
        raise RoleAssignmentError(
            "Bạn không thể tự thu hồi vai trò Quản trị của chính mình."
        )
