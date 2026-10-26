"""Kiểm thử phạm vi quyền truy cập dữ liệu (Data Scope) trên nền tảng Flask/SQLite.
Xác thực nguyên tắc:
1. Nhân viên A không thể xem hoặc thao tác trên khách hàng của nhân viên khác.
2. Danh sách tra cứu khách hàng của nhân viên chỉ chứa dữ liệu thuộc quyền sở hữu của mình.
3. Trưởng nhóm thấy dữ liệu của các thành viên trong nhóm phụ trách.
4. Giám đốc có quyền xem toàn bộ dữ liệu trong hệ thống.
"""
import unittest

from tests.base import CRMTestCase


class TestDataScope(CRMTestCase):
    def test_employee_a_cannot_read_employee_b_customer(self):
        """Nhân viên không thể truy cập dữ liệu khách hàng thuộc quyền quản lý của nhân viên khác."""
        # Khách hàng Ánh Dương thuộc sở hữu của nhanvien1
        c_a = self.customer("anh_duong")
        # Khách hàng An Khang thuộc sở hữu của nhanvien2
        c_b = self.customer("an_khang")

        # Nhân viên 1 truy cập được dòng thời gian khách hàng của mình
        status_a, body_a = self.get(f"/api/customers/{c_a}/activities", "nhanvien1")
        self.assertEqual(status_a, 200, f"Nhân viên 1 phải xem được khách hàng của mình: {body_a}")

        # Nhân viên 1 truy cập khách hàng của nhân viên 2: bị từ chối (404 để ẩn tài nguyên ngoài quyền)
        status_b, _ = self.get(f"/api/customers/{c_b}/activities", "nhanvien1")
        self.assertIn(status_b, (403, 404), "Nhân viên 1 không được phép truy cập khách hàng của nhân viên 2")

    def test_employee_list_only_contain_own_data(self):
        """Danh sách tra cứu khách hàng của nhân viên chỉ chứa khách hàng do chính nhân viên đó sở hữu."""
        status, body = self.get("/api/lookups/customers", "nhanvien1")
        self.assertEqual(status, 200)
        items = body.get("items", [])
        self.assertTrue(len(items) > 0, "Nhân viên 1 phải có khách hàng trong danh sách")

        uid_nv1 = self.uid("nhanvien1")
        for item in items:
            self.assertEqual(
                item["owner"]["id"], uid_nv1,
                f"Lỗi Data Scope: Khách hàng '{item['name']}' có owner_id={item['owner']['id']}, không phải của nhanvien1 ({uid_nv1})!"
            )

    def test_team_leader_sees_group_and_director_sees_all(self):
        """Trưởng nhóm thấy toàn bộ khách hàng của nhóm; Giám đốc thấy tất cả khách hàng công ty."""
        # Trưởng nhóm 1 thấy khách hàng của cả nhóm 1 (nhanvien1, nhanvien2, truongnhom1)
        status_lead, body_lead = self.get("/api/lookups/customers", "truongnhom1")
        self.assertEqual(status_lead, 200)
        lead_items = body_lead.get("items", [])
        lead_owners = {item["owner"]["id"] for item in lead_items}
        # Phải thấy ít nhất nhanvien1 và nhanvien2
        self.assertTrue({self.uid("nhanvien1"), self.uid("nhanvien2")}.issubset(lead_owners),
                        f"Trưởng nhóm 1 phải thấy khách hàng của các thành viên trong nhóm: {lead_owners}")

        # Giám đốc thấy toàn bộ khách hàng trong hệ thống (ít nhất 6 khách hàng trong seed data)
        status_dir, body_dir = self.get("/api/lookups/customers", "giamdoc")
        self.assertEqual(status_dir, 200)
        dir_items = body_dir.get("items", [])
        self.assertTrue(len(dir_items) >= 6, f"Giám đốc phải thấy toàn bộ ít nhất 6 khách hàng, thực tế: {len(dir_items)}")
        dir_owners = {item["owner"]["id"] for item in dir_items}
        # Thấy cả nhóm 1 lẫn nhóm 2
        self.assertIn(self.uid("nhanvien1"), dir_owners)
        self.assertIn(self.uid("nhanvien3"), dir_owners)


if __name__ == "__main__":
    unittest.main()
