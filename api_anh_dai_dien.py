# -*- coding: utf-8 -*-
"""
[SCRUM-61] TẢI LÊN ẢNH ĐẠI DIỆN
User story: "Là người dùng của hệ thống, tôi muốn tải lên ảnh đại diện, để đồng
nghiệp nhận ra ai đang phụ trách khách hàng khi xem hồ sơ."

Tiêu chí hoàn thành:
  1. Chấp nhận JPG/PNG tối đa 2MB          -> POST /api/ho-so/anh-dai-dien
  2. Ảnh được cắt vuông và tạo bản thu nhỏ -> GET  /api/ho-so/anh-dai-dien
                                           -> GET  /api/ho-so/anh-thu-nho
"""
import io
import os

from PIL import Image
from flask import Blueprint, request, jsonify, send_file

from cau_hinh import (
    THU_MUC_ANH,
    KICH_THUOC_ANH_TOI_DA,
    DINH_DANG_ANH_CHO_PHEP,
    KICH_THUOC_ANH_DAI_DIEN,
    KICH_THUOC_ANH_THU_NHO,
)
from co_so_du_lieu import ket_noi_csdl
from xac_thuc import lay_nguoi_dung_hien_tai

api_anh_dai_dien = Blueprint("api_anh_dai_dien", __name__)


@api_anh_dai_dien.post("/api/ho-so/anh-dai-dien")
def tai_len_anh_dai_dien():
    """Tải lên ảnh đại diện theo đúng 2 tiêu chí của SCRUM-61."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi

    if "anh" not in request.files:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Chưa chọn ảnh. Hãy gửi form-data với khóa 'anh' chứa tệp JPG hoặc PNG.",
        }), 400

    tep_anh = request.files["anh"]
    ten_tep = (tep_anh.filename or "").lower()
    duoi_tep = os.path.splitext(ten_tep)[1]

    # --- [Tiêu chí 1] Kiểm tra định dạng ---
    if duoi_tep not in DINH_DANG_ANH_CHO_PHEP:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": f"Định dạng '{duoi_tep or 'không rõ'}' không được chấp nhận. Chỉ chấp nhận ảnh JPG hoặc PNG.",
        }), 400

    # --- [Tiêu chí 1] Kiểm tra dung lượng tối đa 2MB ---
    du_lieu_anh = tep_anh.read()
    if len(du_lieu_anh) > KICH_THUOC_ANH_TOI_DA:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": (
                f"Ảnh có dung lượng {len(du_lieu_anh) / (1024 * 1024):.2f}MB, "
                "vượt quá giới hạn tối đa 2MB. Vui lòng chọn ảnh nhỏ hơn."
            ),
        }), 400
    if len(du_lieu_anh) == 0:
        return jsonify({"thanh_cong": False, "thong_bao": "Tệp ảnh rỗng."}), 400

    # Mở ảnh và xác minh đúng là JPG/PNG thật (không chỉ dựa vào đuôi tệp)
    try:
        anh = Image.open(io.BytesIO(du_lieu_anh))
        if anh.format not in ("JPEG", "PNG"):
            raise ValueError
