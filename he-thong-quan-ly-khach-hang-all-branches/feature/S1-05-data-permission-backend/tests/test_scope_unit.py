"""Kiểm thử đơn vị cho lõi phân quyền (không cần HTTP)."""
import unittest

from app.messages import AppError
from app.scope import (Role, Scope, User, available_scopes, build_scope_filter,
                       resolve_scope)

NV = User(3, "nhanvien_a", "Nguyễn Văn An", Role.NHAN_VIEN, 1)
TN = User(2, "truongnhom_bac", "Lê Thị Hoa", Role.TRUONG_NHOM, 1)
TN_KHONG_NHOM = User(9, "tn_moi", "Trưởng nhóm mới", Role.TRUONG_NHOM, None)
GD = User(1, "giamdoc", "Trần Văn Giám", Role.GIAM_DOC, None)


class ResolveScopeTests(unittest.TestCase):
    def test_mac_dinh_la_pham_vi_rong_nhat_cua_vai_tro(self):
        self.assertEqual(resolve_scope(NV, None), Scope.MINE)
        self.assertEqual(resolve_scope(TN, None), Scope.TEAM)
        self.assertEqual(resolve_scope(GD, ""), Scope.ALL)

    def test_duoc_chon_pham_vi_hep_hon(self):
        self.assertEqual(resolve_scope(GD, "mine"), Scope.MINE)
        self.assertEqual(resolve_scope(GD, "TEAM"), Scope.TEAM)
        self.assertEqual(resolve_scope(TN, "mine"), Scope.MINE)

    def test_khong_duoc_chon_pham_vi_rong_hon(self):
        for user, requested in [(NV, "team"), (NV, "all"), (TN, "all")]:
            with self.assertRaises(AppError) as ctx:
                resolve_scope(user, requested)
            self.assertEqual(ctx.exception.status, 403)

    def test_pham_vi_khong_hop_le(self):
        with self.assertRaises(AppError) as ctx:
            resolve_scope(GD, "everything")
        self.assertEqual(ctx.exception.status, 400)
        self.assertIn("không hợp lệ", ctx.exception.message)

    def test_danh_sach_pham_vi_duoc_chon(self):
        self.assertEqual(available_scopes(NV), [Scope.MINE])
        self.assertEqual(available_scopes(TN), [Scope.MINE, Scope.TEAM])
        self.assertEqual(available_scopes(GD), [Scope.MINE, Scope.TEAM, Scope.ALL])


class BuildScopeFilterTests(unittest.TestCase):
    def test_mine_loc_theo_chu_so_huu(self):
        sql, params = build_scope_filter(NV, Scope.MINE, "t.owner_id")
        self.assertEqual(sql, "t.owner_id = ?")
        self.assertEqual(params, [3])

    def test_team_loc_theo_nhom(self):
        sql, params = build_scope_filter(TN, Scope.TEAM, "t.owner_id")
        self.assertIn("team_id = ?", sql)
        self.assertEqual(params, [1])

    def test_team_nhung_chua_co_nhom_thi_chi_thay_cua_minh(self):
        sql, params = build_scope_filter(TN_KHONG_NHOM, Scope.TEAM)
        self.assertEqual(sql, "owner_id = ?")
        self.assertEqual(params, [9])

    def test_all_khong_loc(self):
        sql, params = build_scope_filter(GD, Scope.ALL)
        self.assertEqual((sql, params), ("1 = 1", []))


if __name__ == "__main__":
    unittest.main()
