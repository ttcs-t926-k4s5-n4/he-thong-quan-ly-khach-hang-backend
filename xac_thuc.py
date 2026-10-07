# -*- coding: utf-8 -*-
"""
XÁC THỰC ĐƠN GIẢN CHO DEMO
Đọc header X-User-Id để xác định người dùng hiện tại.
"""
from flask import request, jsonify

from co_so_du_lieu import ket_noi_csdl


def lay_nguoi_dung_hien_tai():
    """
    Trả về (nguoi_dung, loi). Nếu có lỗi thì nguoi_dung = None
    và loi là cặp (response, mã_http) để trả thẳng cho client.
    """
    ma_nguoi_dung = request.headers.get("X-User-Id") or request.args.get("user_id")
    if not ma_nguoi_dung:
        return None, (
            jsonify({
                "thanh_cong": False,
                "thong_bao": "Thiếu header X-User-Id. Hãy gửi kèm header X-User-Id với id người dùng (ví dụ: 1).",
            }),
            401,
        )
    db = ket_noi_csdl()
    nguoi_dung = db.execute(
        "SELECT * FROM nguoi_dung WHERE id = ?", (ma_nguoi_dung,)
    ).fetchone()
    if nguoi_dung is None:
        return None, (
            jsonify({
                "thanh_cong": False,
                "thong_bao": f"Không tìm thấy người dùng có id = {ma_nguoi_dung}.",
            }),
            404,
        )
    return nguoi_dung, None
