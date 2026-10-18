r"""
tests/test_opportunity_history.py ΓÇö Test suite cho SCRUM-95: Opportunity Change History

Kiß╗âm thß╗¡:
1. Lß║Ñy lß╗ïch sß╗¡ cß╗ºa mß╗Öt c╞í hß╗Öi (GET /api/opportunities/<id>/history)
2. Cß║¡p nhß║¡t Stage, Value, Expected Close Date v├á Owner
3. Cß║¡p nhß║¡t nhiß╗üu tr╞░ß╗¥ng trong c├╣ng mß╗Öt request
4. Kh├┤ng tß║ío lß╗ïch sß╗¡ khi dß╗» liß╗çu kh├┤ng thay ─æß╗òi
5. Rollback cß║ú cß║¡p nhß║¡t v├á lß╗ïch sß╗¡ khi transaction thß║Ñt bß║íi
6. C╞í hß╗Öi kh├┤ng tß╗ôn tß║íi (404)
7. Ng╞░ß╗¥i d├╣ng ch╞░a ─æ─âng nhß║¡p (401)
8. Ng╞░ß╗¥i d├╣ng kh├┤ng c├│ quyß╗ün truy cß║¡p (403)
9. Ph├ón trang v├á dß╗» liß╗çu lß╗ïch sß╗¡ rß╗ùng
10. Lß╗ìc lß╗ïch sß╗¡ theo tr╞░ß╗¥ng `field`
"""
import unittest
from unittest.mock import MagicMock, patch

from app import create_app
from app.auth import CurrentUser
from app.opportunity_history import (
    can_access_opportunity,
    compute_opportunity_diff,
    get_opportunity_history,
    record_history_in_transaction,
)


class TestComputeOpportunityDiff(unittest.TestCase):
    """Kiß╗âm thß╗¡ logic so s├ính gi├í trß╗ï c┼⌐ v├á mß╗¢i (diff engine)."""

    def setUp(self):
        self.old_opp = {
            "id": 1,
            "title": "C╞í hß╗Öi ERP",
            "stage": "Mß╗¢i tß║ío",
            "value": 100000000.0,
            "expected_close_date": "2026-12-31",
            "owner_id": 2,
            "created_by": 2,
        }

    def test_diff_stage_changed(self):
        """Thay ─æß╗òi stage ΓåÆ tß║ío bß║ún ghi diff stage"""
        diffs = compute_opportunity_diff(
            old_opp=self.old_opp,
            new_stage="─É├ám ph├ín",
            new_value=100000000.0,
            new_expected_close_date="2026-12-31",
            new_owner_id=2,
        )
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0]["field_name"], "stage")
        self.assertEqual(diffs[0]["old_value"], "Mß╗¢i tß║ío")
        self.assertEqual(diffs[0]["new_value"], "─É├ám ph├ín")

    def test_diff_value_changed(self):
        """Thay ─æß╗òi value ΓåÆ tß║ío bß║ún ghi diff value"""
        diffs = compute_opportunity_diff(
            old_opp=self.old_opp,
            new_stage="Mß╗¢i tß║ío",
            new_value=150000000.0,
            new_expected_close_date="2026-12-31",
            new_owner_id=2,
        )
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0]["field_name"], "value")
        self.assertEqual(diffs[0]["old_value"], "100000000")
        self.assertEqual(diffs[0]["new_value"], "150000000")

    def test_diff_expected_close_date_changed(self):
        """Thay ─æß╗òi ng├áy chß╗æt dß╗▒ kiß║┐n ΓåÆ tß║ío diff expected_close_date"""
        diffs = compute_opportunity_diff(
            old_opp=self.old_opp,
            new_stage="Mß╗¢i tß║ío",
            new_value=100000000.0,
            new_expected_close_date="2027-01-15",
            new_owner_id=2,
        )
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0]["field_name"], "expected_close_date")
        self.assertEqual(diffs[0]["old_value"], "2026-12-31")
        self.assertEqual(diffs[0]["new_value"], "2027-01-15")

    def test_diff_owner_changed(self):
        """Thay ─æß╗òi ng╞░ß╗¥i sß╗ƒ hß╗»u ΓåÆ tß║ío diff owner"""
        diffs = compute_opportunity_diff(
            old_opp=self.old_opp,
            new_stage="Mß╗¢i tß║ío",
            new_value=100000000.0,
            new_expected_close_date="2026-12-31",
            new_owner_id=5,
        )
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0]["field_name"], "owner")
        self.assertEqual(diffs[0]["old_value"], "2")
        self.assertEqual(diffs[0]["new_value"], "5")

    def test_diff_multiple_fields_changed(self):
        """Thay ─æß╗òi nhiß╗üu tr╞░ß╗¥ng c├╣ng l├║c ΓåÆ ghi nhß║¡n ─æß║ºy ─æß╗º tß║Ñt cß║ú c├íc tr╞░ß╗¥ng"""
        diffs = compute_opportunity_diff(
            old_opp=self.old_opp,
            new_stage="Chß╗æt hß╗úp ─æß╗ông",
            new_value=250000000.0,
            new_expected_close_date="2026-11-20",
            new_owner_id=9,
        )
        self.assertEqual(len(diffs), 4)
        field_names = [d["field_name"] for d in diffs]
        self.assertIn("stage", field_names)
        self.assertIn("value", field_names)
        self.assertIn("expected_close_date", field_names)
        self.assertIn("owner", field_names)

    def test_no_diff_when_data_unchanged(self):
        """Kh├┤ng thay ─æß╗òi dß╗» liß╗çu ΓåÆ kh├┤ng tß║ío bß║ún ghi lß╗ïch sß╗¡ n├áo"""
        diffs = compute_opportunity_diff(
            old_opp=self.old_opp,
            new_stage="Mß╗¢i tß║ío",
            new_value=100000000.0,
            new_expected_close_date="2026-12-31",
            new_owner_id=2,
        )
        self.assertEqual(len(diffs), 0)


class TestAuthorization(unittest.TestCase):
    """Kiß╗âm thß╗¡ ph├ón quyß╗ün truy cß║¡p c╞í hß╗Öi v├á lß╗ïch sß╗¡."""

    def test_admin_can_access_any_opportunity(self):
        admin = CurrentUser(id=1, email="admin@test.com", full_name="Admin", role="admin", credentials_version=1)
        opp = {"id": 10, "owner_id": 99, "created_by": 99}
        self.assertTrue(can_access_opportunity(admin, opp))

    def test_manager_can_access_any_opportunity(self):
        manager = CurrentUser(id=2, email="manager@test.com", full_name="Manager", role="manager", credentials_version=1)
        opp = {"id": 10, "owner_id": 99, "created_by": 99}
        self.assertTrue(can_access_opportunity(manager, opp))

    def test_employee_can_access_own_opportunity(self):
        employee = CurrentUser(id=5, email="emp@test.com", full_name="Employee", role="employee", credentials_version=1)
        opp = {"id": 10, "owner_id": 5, "created_by": 1}
        self.assertTrue(can_access_opportunity(employee, opp))

    def test_employee_cannot_access_other_opportunity(self):
        employee = CurrentUser(id=5, email="emp@test.com", full_name="Employee", role="employee", credentials_version=1)
        opp = {"id": 10, "owner_id": 8, "created_by": 8}
        self.assertFalse(can_access_opportunity(employee, opp))


class TestTransactionRollback(unittest.TestCase):
    """Kiß╗âm thß╗¡ rollback cß║ú cß║¡p nhß║¡t v├á lß╗ïch sß╗¡ khi transaction thß║Ñt bß║íi."""

    def setUp(self):
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret"})

    @patch("app.opportunities.ensure_opportunity_history_table")
    @patch("app.opportunities.get_pipeline_stage_by_key")
    @patch("app.opportunities.validate_stage_transition")
    @patch("app.opportunities.validate_opportunity_closure")
    @patch("app.opportunities.fetch_one")
    @patch("app.opportunities.get_opportunity")
    @patch("app.opportunities.get_db")
    def test_rollback_on_update_failure(
        self,
        mock_get_db,
        mock_get_opp,
        mock_fetch_one,
        mock_closure,
        mock_trans,
        mock_stage_key,
        mock_ensure,
    ):
        from app.opportunities import update_opportunity

        mock_stage_key.return_value = {
            "stage_key": "negotiation",
            "stage_name": "─É├ám ph├ín",
            "win_probability": 50,
            "is_won_stage": 0,
            "is_lost_stage": 0,
        }
        mock_trans.return_value = (True, "")
        mock_closure.return_value = (True, "")

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_get_db.return_value = mock_conn

        mock_get_opp.return_value = {
            "id": 1,
            "title": "C╞í hß╗Öi test",
            "customer_id": 10,
            "value": 50000000.0,
            "stage": "Mß╗¢i tß║ío",
            "stage_key": "initial",
            "expected_close_date": "2026-12-31",
            "owner_id": 1,
            "created_by": 1,
            "win_probability": 10,
            "meetings_count": 0,
        }
        mock_fetch_one.side_effect = [
            {"id": 10},  # customer found
            {"id": 2},   # owner user found
        ]

        # Giß║ú lß║¡p lß╗ùi khi thß╗▒c thi SQL UPDATE trong transaction
        mock_cur.execute.side_effect = Exception("Database deadlock error")

        with self.app.app_context():
            with self.assertRaises(Exception):
                update_opportunity(
                    opportunity_id=1,
                    title="C╞í hß╗Öi cß║¡p nhß║¡t",
                    customer_id=10,
                    value=80000000.0,
                    stage="─É├ám ph├ín",
                    owner_id=2,
                    changed_by=1,
                )

        # Kiß╗âm tra conn.rollback() ─æ├ú ─æ╞░ß╗úc gß╗ìi ─æß╗â huß╗╖ to├án bß╗Ö thao t├íc
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()


class TestHistoryQuery(unittest.TestCase):
    """Kiß╗âm thß╗¡ truy vß║Ñn lß╗ïch sß╗¡, lß╗ìc theo field v├á ph├ón trang."""

    @patch("app.opportunity_history.fetch_all")
    @patch("app.opportunity_history.fetch_one")
    @patch("app.opportunity_history.ensure_opportunity_history_table")
    def test_get_history_empty(self, mock_ensure, mock_fetch_one, mock_fetch_all):
        mock_fetch_one.return_value = {"total": 0}
        mock_fetch_all.return_value = []

        res = get_opportunity_history(opportunity_id=999, page=1, page_size=20, conn=MagicMock())
        self.assertEqual(res["total"], 0)
        self.assertEqual(len(res["items"]), 0)
        self.assertEqual(res["page"], 1)
        self.assertEqual(res["page_size"], 20)
        self.assertEqual(res["total_pages"], 1)

    @patch("app.opportunity_history.fetch_all")
    @patch("app.opportunity_history.fetch_one")
    @patch("app.opportunity_history.ensure_opportunity_history_table")
    def test_get_history_with_field_filter(self, mock_ensure, mock_fetch_one, mock_fetch_all):
        mock_fetch_one.return_value = {"total": 1}
        mock_fetch_all.return_value = [
            {
                "id": 1,
                "opportunity_id": 10,
                "field_name": "stage",
                "old_value": "Mß╗¢i tß║ío",
                "new_value": "─É├ám ph├ín",
                "changed_by": 2,
                "changed_by_name": "Tr╞░ß╗ƒng nh├│m",
                "changed_by_email": "manager@test.com",
                "changed_at": 1729158000000,
            }
        ]

        res = get_opportunity_history(opportunity_id=10, field="stage", page=1, page_size=10, conn=MagicMock())
        self.assertEqual(res["total"], 1)
        self.assertEqual(len(res["items"]), 1)
        self.assertEqual(res["items"][0]["field_name"], "stage")
        self.assertEqual(res["items"][0]["field_label"], "Giai ─æoß║ín")
        self.assertEqual(res["items"][0]["old_value"], "Mß╗¢i tß║ío")
        self.assertEqual(res["items"][0]["new_value"], "─É├ám ph├ín")
        self.assertIn("changed_at_iso", res["items"][0])


class TestOpportunityHistoryEndpoints(unittest.TestCase):
    """Kiß╗âm thß╗¡ t├¡ch hß╗úp c├íc endpoint HTTP cß╗ºa SCRUM-95."""

    def setUp(self):
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret-scrum95"})
        self.client = self.app.test_client()

    def test_history_endpoint_unauthenticated_returns_401(self):
        """Ch╞░a ─æ─âng nhß║¡p gß╗ìi GET /api/opportunities/<id>/history ΓåÆ 401"""
        resp = self.client.get("/api/opportunities/1/history")
        self.assertEqual(resp.status_code, 401)

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_opportunity")
    def test_history_endpoint_opportunity_not_found_returns_404(self, mock_get_opp, mock_auth):
        """C╞í hß╗Öi kh├┤ng tß╗ôn tß║íi ΓåÆ 404"""
        mock_auth.return_value = CurrentUser(id=2, email="manager@test.com", full_name="Manager", role="manager", credentials_version=1)
        mock_get_opp.return_value = None

        resp = self.client.get("/api/opportunities/99999/history")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Kh├┤ng t├¼m thß║Ñy", resp.get_json()["message"])

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_opportunity")
    def test_history_endpoint_forbidden_for_other_employee_returns_403(self, mock_get_opp, mock_auth):
        """Nh├ón vi├¬n kh├┤ng sß╗ƒ hß╗»u c╞í hß╗Öi xem lß╗ïch sß╗¡ ΓåÆ 403 Forbidden"""
        mock_auth.return_value = CurrentUser(id=5, email="emp1@test.com", full_name="Employee 1", role="employee", credentials_version=1)
        mock_get_opp.return_value = {
            "id": 1,
            "title": "C╞í hß╗Öi VIP",
            "owner_id": 8,
            "created_by": 8,
        }

        resp = self.client.get("/api/opportunities/1/history")
        self.assertEqual(resp.status_code, 403)
        self.assertIn("kh├┤ng c├│ quyß╗ün", resp.get_json()["message"])

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_opportunity")
    @patch("app.routes.get_opportunity_history")
    def test_history_endpoint_success_for_manager(self, mock_get_hist, mock_get_opp, mock_auth):
        """Tr╞░ß╗ƒng nh├│m xem lß╗ïch sß╗¡ c╞í hß╗Öi th├ánh c├┤ng ΓåÆ 200"""
        mock_auth.return_value = CurrentUser(id=2, email="manager@test.com", full_name="Manager", role="manager", credentials_version=1)
        mock_get_opp.return_value = {
            "id": 1,
            "title": "C╞í hß╗Öi ABC",
            "owner_id": 5,
            "created_by": 5,
        }
        mock_get_hist.return_value = {
            "items": [
                {
                    "id": 1,
                    "opportunity_id": 1,
                    "field_name": "stage",
                    "old_value": "Mß╗¢i tß║ío",
                    "new_value": "─É├ám ph├ín",
                    "changed_by": 2,
                    "changed_by_name": "Manager",
                    "changed_at": 1729158000000,
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20,
            "total_pages": 1,
        }

        resp = self.client.get("/api/opportunities/1/history?page=1&page_size=20&field=stage")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["field_name"], "stage")

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_opportunity")
    @patch("app.routes.update_opportunity")
    def test_update_opportunity_tracks_changed_by_from_session(self, mock_update, mock_get_opp, mock_auth):
        """Cß║¡p nhß║¡t c╞í hß╗Öi sß╗¡ dß╗Ñng user.id tß╗½ session thay v├¼ client payload"""
        user_in_session = CurrentUser(id=77, email="user77@test.com", full_name="User 77", role="manager", credentials_version=1)
        mock_auth.return_value = user_in_session
        mock_get_opp.return_value = {
            "id": 1,
            "title": "C┼⌐",
            "owner_id": 77,
            "created_by": 77,
        }
        mock_update.return_value = {"id": 1, "title": "Mß╗¢i"}

        resp = self.client.put(
            "/api/opportunities/1",
            json={
                "title": "T├¬n mß╗¢i",
                "customer_id": 10,
                "value": 200000000,
                "stage": "─É├ám ph├ín",
                "owner_id": 88,
                "user_id": 9999,  # Cß╗æ t├¼nh giß║ú mß║ío user_id tß╗½ client
            },
        )
        self.assertEqual(resp.status_code, 200)
        # X├íc nhß║¡n changed_by ─æ╞░ß╗úc truyß╗ün v├áo update_opportunity l├á user.id=77, kh├┤ng phß║úi 9999
        _, kwargs = mock_update.call_args
        self.assertEqual(kwargs.get("changed_by"), 77)

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_opportunity")
    @patch("app.routes.get_opportunity_history")
    def test_employee_can_access_own_opportunity_history(self, mock_get_hist, mock_get_opp, mock_auth):
        """Nh├ón vi├¬n c├│ quyß╗ün xem lß╗ïch sß╗¡ c╞í hß╗Öi do ch├¡nh m├¼nh sß╗ƒ hß╗»u ΓåÆ 200"""
        mock_auth.return_value = CurrentUser(id=5, email="emp5@test.com", full_name="Employee 5", role="employee", credentials_version=1)
        mock_get_opp.return_value = {
            "id": 10,
            "title": "C╞í hß╗Öi cß╗ºa t├┤i",
            "owner_id": 5,
            "created_by": 5,
        }
        mock_get_hist.return_value = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20,
            "total_pages": 1,
        }

        resp = self.client.get("/api/opportunities/10/history")
        self.assertEqual(resp.status_code, 200)

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_opportunity")
    @patch("app.routes.update_opportunity")
    def test_update_opportunity_owner_not_found_returns_404(self, mock_update, mock_get_opp, mock_auth):
        """Cß║¡p nhß║¡t c╞í hß╗Öi vß╗¢i owner_id kh├┤ng tß╗ôn tß║íi trong hß╗ç thß╗æng ΓåÆ 404"""
        mock_auth.return_value = CurrentUser(id=2, email="manager@test.com", full_name="Manager", role="manager", credentials_version=1)
        mock_get_opp.return_value = {
            "id": 1,
            "title": "C┼⌐",
            "owner_id": 2,
            "created_by": 2,
        }
        mock_update.side_effect = ValueError("owner_not_found")

        resp = self.client.put(
            "/api/opportunities/1",
            json={
                "title": "T├¬n mß╗¢i",
                "customer_id": 10,
                "owner_id": 999999,
            },
        )
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Ng╞░ß╗¥i sß╗ƒ hß╗»u kh├┤ng tß╗ôn tß║íi", resp.get_json()["message"])


class TestAtomicHistoryRecording(unittest.TestCase):
    """Kiß╗âm thß╗¡ t├¡nh nguy├¬n tß╗¡ khi ghi nhß║¡n lß╗ïch sß╗¡ c├╣ng transaction cß║¡p nhß║¡t."""

    def setUp(self):
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret"})

    @patch("app.opportunities.ensure_opportunity_history_table")
    @patch("app.opportunities.get_pipeline_stage_by_key")
    @patch("app.opportunities.validate_stage_transition")
    @patch("app.opportunities.validate_opportunity_closure")
    @patch("app.opportunities.fetch_one")
    @patch("app.opportunities.get_opportunity")
    @patch("app.opportunities.get_db")
    def test_update_opportunity_commits_both_opp_and_history(
        self,
        mock_get_db,
        mock_get_opp,
        mock_fetch_one,
        mock_closure,
        mock_trans,
        mock_stage_key,
        mock_ensure,
    ):
        from app.opportunities import update_opportunity

        mock_stage_key.return_value = {
            "stage_key": "negotiation",
            "stage_name": "─É├ám ph├ín",
            "win_probability": 50,
            "is_won_stage": 0,
            "is_lost_stage": 0,
        }
        mock_trans.return_value = (True, "")
        mock_closure.return_value = (True, "")

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_get_db.return_value = mock_conn

        # Opportunity ban ─æß║ºu
        mock_get_opp.side_effect = [
            {
                "id": 1,
                "title": "Dß╗▒ ├ín CRM",
                "customer_id": 10,
                "value": 50000000.0,
                "stage": "Mß╗¢i tß║ío",
                "stage_key": "initial",
                "expected_close_date": "2026-10-30",
                "owner_id": 1,
                "created_by": 1,
                "win_probability": 10,
                "meetings_count": 0,
            },
            {
                "id": 1,
                "title": "Dß╗▒ ├ín CRM",
                "customer_id": 10,
                "value": 90000000.0,
                "stage": "─É├ám ph├ín",
                "stage_key": "negotiation",
                "expected_close_date": "2026-11-15",
                "owner_id": 3,
                "created_by": 1,
                "win_probability": 50,
                "meetings_count": 0,
            },
        ]
        mock_fetch_one.side_effect = [
            {"id": 10},  # customer found
            {"id": 3},   # owner user found
        ]

        with self.app.app_context():
            updated = update_opportunity(
                opportunity_id=1,
                title="Dß╗▒ ├ín CRM",
                customer_id=10,
                value=90000000.0,
                stage="─É├ám ph├ín",
                expected_close_date="2026-11-15",
                owner_id=3,
                changed_by=7,
            )

        # ─Éß║úm bß║úo transaction ─æ╞░ß╗úc commit
        mock_conn.commit.assert_called_once()
        mock_conn.rollback.assert_not_called()

        # Kiß╗âm tra cur.execute ─æ├ú chß║íy c├óu lß╗çnh INSERT v├áo opportunity_history
        executed_sqls = [call[0][0] for call in mock_cur.execute.call_args_list]
        has_history_insert = any("opportunity_history" in s for s in executed_sqls)
        self.assertTrue(has_history_insert)


if __name__ == "__main__":
    unittest.main()
