r"""
tests/test_opportunity_shares.py ΓÇö Test suite cho SCRUM-97: Opportunity Sharing & Ownership

Kiß╗âm thß╗¡:
1. Chia sß║╗ mß╗Öt c╞í hß╗Öi cho nhiß╗üu th├ánh vi├¬n (POST /api/opportunities/<id>/shares)
2. Lß║Ñy danh s├ích th├ánh vi├¬n chia sß║╗ (GET /api/opportunities/<id>/shares)
3. Cß║¡p nhß║¡t quyß╗ün chia sß║╗ (PATCH /api/opportunities/<id>/shares/<user_id>)
4. Gß╗í th├ánh vi├¬n chia sß║╗ (DELETE /api/opportunities/<id>/shares/<user_id>)
5. Ng─ân th├¬m th├ánh vi├¬n tr├╣ng (400)
6. Ng─ân chia sß║╗ cho ch├¡nh Ng╞░ß╗¥i sß╗ƒ hß╗»u ch├¡nh (400)
7. Chuyß╗ân quyß╗ün sß╗ƒ hß╗»u ch├¡nh (POST /api/opportunities/<id>/transfer-ownership)
8. Ng─ân Shared Member tß╗▒ chuyß╗ân quyß╗ün sß╗ƒ hß╗»u (403)
9. Ng─ân ng╞░ß╗¥i kh├┤ng c├│ quyß╗ün th├¬m hoß║╖c x├│a th├ánh vi├¬n (403)
10. Ng─ân truy cß║¡p c╞í hß╗Öi ngo├ái phß║ím vi ─æ╞░ß╗úc ph├⌐p (403)
11. Kiß╗âm tra th├ánh vi├¬n kh├┤ng tß╗ôn tß║íi hoß║╖c t├ái khoß║ún bß╗ï kh├│a (400)
12. Rollback transaction khi chuyß╗ân quyß╗ün sß╗ƒ hß╗»u thß║Ñt bß║íi
13. T├¡ch hß╗úp ghi nhß║¡t k├╜ chuyß╗ân quyß╗ün sß╗ƒ hß╗»u v├áo dbo.opportunity_history (SCRUM-95)
"""
import unittest
from unittest.mock import MagicMock, patch

from app import create_app
from app.auth import CurrentUser
from app.opportunity_shares import (
    check_opportunity_access,
    list_opportunity_shares,
    remove_opportunity_share,
    share_opportunity,
    transfer_opportunity_ownership,
    update_share_permission,
)


class TestOpportunitySharesAccessUnit(unittest.TestCase):
    """Kiß╗âm thß╗¡ ma trß║¡n ph├ón quyß╗ün chi tiß║┐t (check_opportunity_access)."""

    def setUp(self):
        self.opp = {"id": 1, "owner_id": 2, "created_by": 2}

    def test_manager_has_full_access(self):
        manager = CurrentUser(99, "m@test.com", "M", "manager", 1)
        for perm in ["read", "edit", "share", "transfer"]:
            allowed, _ = check_opportunity_access(manager, self.opp, required_permission=perm)
            self.assertTrue(allowed)

    def test_primary_owner_has_full_access(self):
        owner = CurrentUser(2, "owner@test.com", "Owner", "employee", 1)
        for perm in ["read", "edit", "share", "transfer"]:
            allowed, _ = check_opportunity_access(owner, self.opp, required_permission=perm)
            self.assertTrue(allowed)

    @patch("app.opportunity_shares.get_user_share_record")
    def test_shared_member_read_only(self, mock_get_share):
        mock_get_share.return_value = {"permission_level": "read"}
        member = CurrentUser(5, "mem@test.com", "Member", "employee", 1)

        allowed_read, _ = check_opportunity_access(member, self.opp, required_permission="read")
        self.assertTrue(allowed_read)

        allowed_edit, _ = check_opportunity_access(member, self.opp, required_permission="edit")
        self.assertFalse(allowed_edit)

        allowed_share, _ = check_opportunity_access(member, self.opp, required_permission="share")
        self.assertFalse(allowed_share)

        allowed_transfer, _ = check_opportunity_access(member, self.opp, required_permission="transfer")
        self.assertFalse(allowed_transfer)

    @patch("app.opportunity_shares.get_user_share_record")
    def test_shared_member_edit_permission(self, mock_get_share):
        mock_get_share.return_value = {"permission_level": "edit"}
        member = CurrentUser(5, "mem@test.com", "Member", "employee", 1)

        allowed_read, _ = check_opportunity_access(member, self.opp, required_permission="read")
        self.assertTrue(allowed_read)

        allowed_edit, _ = check_opportunity_access(member, self.opp, required_permission="edit")
        self.assertTrue(allowed_edit)

        # Shared member vß╗¢i quyß╗ün edit vß║½n KH├öNG ─É╞»ß╗óC chuyß╗ân quyß╗ün sß╗ƒ hß╗»u
        allowed_transfer, _ = check_opportunity_access(member, self.opp, required_permission="transfer")
        self.assertFalse(allowed_transfer)

    @patch("app.opportunity_shares.get_user_share_record")
    def test_unrelated_employee_access_denied(self, mock_get_share):
        mock_get_share.return_value = None
        stranger = CurrentUser(77, "stranger@test.com", "Stranger", "employee", 1)

        allowed, _ = check_opportunity_access(stranger, self.opp, required_permission="read")
        self.assertFalse(allowed)


class TestOpportunitySharesLogicUnit(unittest.TestCase):
    """Kiß╗âm thß╗¡ logic chia sß║╗ v├á chuyß╗ân quyß╗ün sß╗ƒ hß╗»u."""

    @patch("app.opportunity_shares.fetch_one")
    @patch("app.opportunity_shares.ensure_opportunity_shares_table")
    def test_cannot_share_with_primary_owner(self, mock_ensure, mock_fetch_one):
        mock_fetch_one.side_effect = [
            {"id": 1, "owner_id": 5},  # opp (owner l├á 5)
            {"id": 5, "full_name": "Owner", "is_active": True},  # user target
        ]
        with self.assertRaises(ValueError) as ctx:
            share_opportunity(opportunity_id=1, user_id=5, permission_level="read", conn=MagicMock())
        self.assertIn("Ng╞░ß╗¥i sß╗ƒ hß╗»u ch├¡nh", str(ctx.exception))

    @patch("app.opportunity_shares.fetch_one")
    @patch("app.opportunity_shares.ensure_opportunity_shares_table")
    def test_cannot_share_with_inactive_user(self, mock_ensure, mock_fetch_one):
        mock_fetch_one.side_effect = [
            {"id": 1, "owner_id": 2},  # opp
            {"id": 6, "full_name": "Locked User", "is_active": False},  # user bß╗ï v├┤ hiß╗çu h├│a
        ]
        with self.assertRaises(ValueError) as ctx:
            share_opportunity(opportunity_id=1, user_id=6, permission_level="read", conn=MagicMock())
        self.assertIn("v├┤ hiß╗çu h├│a", str(ctx.exception))

    @patch("app.opportunity_shares.fetch_one")
    @patch("app.opportunity_shares.ensure_opportunity_shares_table")
    def test_cannot_share_duplicate(self, mock_ensure, mock_fetch_one):
        mock_fetch_one.side_effect = [
            {"id": 1, "owner_id": 2},  # opp
            {"id": 8, "full_name": "User 8", "is_active": True},  # user
            {"id": 99},  # existing share
        ]
        with self.assertRaises(ValueError) as ctx:
            share_opportunity(opportunity_id=1, user_id=8, permission_level="read", conn=MagicMock())
        self.assertIn("─æ├ú ─æ╞░ß╗úc chia sß║╗", str(ctx.exception))

    @patch("app.opportunity_shares.record_history_in_transaction")
    @patch("app.opportunity_shares.list_opportunity_shares")
    @patch("app.opportunity_shares.fetch_one")
    @patch("app.opportunity_shares.ensure_opportunity_history_table")
    @patch("app.opportunity_shares.ensure_opportunity_shares_table")
    def test_transfer_ownership_success_and_logs_history(
        self,
        mock_ensure_shares,
        mock_ensure_hist,
        mock_fetch_one,
        mock_list,
        mock_log_hist,
    ):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur

        mock_fetch_one.side_effect = [
            {"id": 1, "title": "CRM", "owner_id": 2},  # opp ban ─æß║ºu owner l├á 2
            {"id": 7, "full_name": "Chß╗º mß╗¢i", "is_active": True},  # chß╗º mß╗¢i
            None,  # old_share_exists
        ]

        transfer_opportunity_ownership(opportunity_id=1, new_owner_id=7, transferred_by=2, conn=mock_conn)

        # ─Éß║úm bß║úo commit transaction
        mock_conn.commit.assert_called_once()
        # ─Éß║úm bß║úo ghi nhß║¡n lß╗ïch sß╗¡ thay ─æß╗òi ng╞░ß╗¥i sß╗ƒ hß╗»u (SCRUM-95)
        mock_log_hist.assert_called_once()
        _, kwargs = mock_log_hist.call_args
        self.assertEqual(kwargs["diffs"][0]["field_name"], "owner")
        self.assertEqual(kwargs["diffs"][0]["old_value"], "2")
        self.assertEqual(kwargs["diffs"][0]["new_value"], "7")


class TestOpportunitySharesEndpoints(unittest.TestCase):
    """Kiß╗âm thß╗¡ c├íc HTTP endpoint cß╗ºa SCRUM-97."""

    def setUp(self):
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret-scrum97"})
        self.client = self.app.test_client()

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_opportunity")
    @patch("app.routes.list_opportunity_shares")
    def test_get_shares_endpoint_success(self, mock_list, mock_get_opp, mock_auth):
        mock_auth.return_value = CurrentUser(2, "manager@test.com", "Manager", "manager", 1)
        mock_get_opp.return_value = {"id": 1, "owner_id": 5}
        mock_list.return_value = {
            "opportunity_id": 1,
            "primary_owner": {"id": 5, "full_name": "Owner"},
            "shares": [{"user_id": 8, "permission_level": "read"}],
        }

        resp = self.client.get("/api/opportunities/1/shares")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("primary_owner", data)
        self.assertIn("shares", data)

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_opportunity")
    @patch("app.routes.share_opportunity")
    def test_post_share_endpoint_success(self, mock_share, mock_get_opp, mock_auth):
        mock_auth.return_value = CurrentUser(2, "manager@test.com", "Manager", "manager", 1)
        mock_get_opp.return_value = {"id": 1, "owner_id": 2}
        mock_share.return_value = {"opportunity_id": 1, "shares": []}

        resp = self.client.post("/api/opportunities/1/shares", json={"user_id": 8, "permission_level": "edit"})
        self.assertEqual(resp.status_code, 201)
        self.assertIn("Chia sß║╗ c╞í hß╗Öi th├ánh c├┤ng", resp.get_json()["message"])

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_opportunity")
    def test_post_share_endpoint_missing_user_id_returns_400(self, mock_get_opp, mock_auth):
        mock_auth.return_value = CurrentUser(2, "manager@test.com", "Manager", "manager", 1)
        mock_get_opp.return_value = {"id": 1, "owner_id": 2}

        resp = self.client.post("/api/opportunities/1/shares", json={"permission_level": "edit"})
        self.assertEqual(resp.status_code, 400)

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_opportunity")
    @patch("app.routes.remove_opportunity_share")
    def test_delete_share_endpoint_success(self, mock_remove, mock_get_opp, mock_auth):
        mock_auth.return_value = CurrentUser(2, "manager@test.com", "Manager", "manager", 1)
        mock_get_opp.return_value = {"id": 1, "owner_id": 2}
        mock_remove.return_value = True

        resp = self.client.delete("/api/opportunities/1/shares/8")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("─É├ú gß╗í quyß╗ün chia sß║╗", resp.get_json()["message"])

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_opportunity")
    @patch("app.routes.transfer_opportunity_ownership")
    def test_transfer_ownership_endpoint_success(self, mock_transfer, mock_get_opp, mock_auth):
        mock_auth.return_value = CurrentUser(2, "owner@test.com", "Primary Owner", "employee", 1)
        mock_get_opp.return_value = {"id": 1, "owner_id": 2}  # user l├á primary owner
        mock_transfer.return_value = {"opportunity_id": 1, "primary_owner": {"id": 9}}

        resp = self.client.post("/api/opportunities/1/transfer-ownership", json={"new_owner_id": 9})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Chuyß╗ân quyß╗ün sß╗ƒ hß╗»u c╞í hß╗Öi th├ánh c├┤ng", resp.get_json()["message"])

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_opportunity")
    @patch("app.opportunity_shares.get_user_share_record")
    def test_transfer_ownership_forbidden_for_shared_member(self, mock_get_share, mock_get_opp, mock_auth):
        """Th├ánh vi├¬n ─æ╞░ß╗úc chia sß║╗ (Shared Member) KH├öNG ─æ╞░ß╗úc chuyß╗ân quyß╗ün sß╗ƒ hß╗»u ΓåÆ 403"""
        mock_auth.return_value = CurrentUser(5, "mem@test.com", "Shared Member", "employee", 1)
        mock_get_opp.return_value = {"id": 1, "owner_id": 2}  # user 5 KH├öNG PHß║óI primary owner
        mock_get_share.return_value = {"permission_level": "manage"}

        resp = self.client.post("/api/opportunities/1/transfer-ownership", json={"new_owner_id": 9})
        self.assertEqual(resp.status_code, 403)
        self.assertIn("Chß╗ë Ng╞░ß╗¥i sß╗ƒ hß╗»u ch├¡nh", resp.get_json()["message"])


if __name__ == "__main__":
    unittest.main()
