import unittest

from app.rules import RoleAssignmentError, validate_role_assignment


class RoleAssignmentRulesTest(unittest.TestCase):
    def test_user_can_hold_multiple_roles(self):
        validate_role_assignment(
            current_admin_id=1,
            target_user_id=2,
            current_role_codes={"SALES"},
            selected_role_codes={"SALES", "REPORT_VIEWER"},
            business_group_id=None,
        )

    def test_team_leader_requires_business_group(self):
        with self.assertRaises(RoleAssignmentError):
            validate_role_assignment(
                current_admin_id=1,
                target_user_id=2,
                current_role_codes={"SALES"},
                selected_role_codes={"SALES", "TEAM_LEADER"},
                business_group_id=None,
            )

    def test_admin_cannot_revoke_own_admin_role(self):
        with self.assertRaises(RoleAssignmentError):
            validate_role_assignment(
                current_admin_id=1,
                target_user_id=1,
                current_role_codes={"ADMIN", "SALES"},
                selected_role_codes={"SALES"},
                business_group_id=1,
            )


if __name__ == "__main__":
    unittest.main()
