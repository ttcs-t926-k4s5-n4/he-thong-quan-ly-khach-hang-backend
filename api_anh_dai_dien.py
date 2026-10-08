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
        anh = anh.convert("RGB")
    except Exception:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Tệp không phải là ảnh JPG/PNG hợp lệ hoặc ảnh đã bị hỏng.",
        }), 400

    # --- [Tiêu chí 2] Cắt ảnh thành hình VUÔNG ở chính giữa ---
    rong, cao = anh.size
    canh = min(rong, cao)
    trai = (rong - canh) // 2
    tren = (cao - canh) // 2
    anh_vuong = anh.crop((trai, tren, trai + canh, tren + canh))

    # Ảnh đại diện chuẩn 512x512 và bản thu nhỏ 128x128
    anh_dai_dien = anh_vuong.resize(
        (KICH_THUOC_ANH_DAI_DIEN, KICH_THUOC_ANH_DAI_DIEN), Image.LANCZOS
    )
    anh_thu_nho = anh_vuong.resize(
        (KICH_THUOC_ANH_THU_NHO, KICH_THUOC_ANH_THU_NHO), Image.LANCZOS
    )

    duong_dan_anh = os.path.join(THU_MUC_ANH, f"nguoi_dung_{nguoi_dung['id']}_anh_dai_dien.jpg")
    duong_dan_thu_nho = os.path.join(THU_MUC_ANH, f"nguoi_dung_{nguoi_dung['id']}_anh_thu_nho.jpg")
    anh_dai_dien.save(duong_dan_anh, "JPEG", quality=90)
    anh_thu_nho.save(duong_dan_thu_nho, "JPEG", quality=90)

    db = ket_noi_csdl()
    db.execute(
        "UPDATE nguoi_dung SET anh_dai_dien = ?, anh_thu_nho = ? WHERE id = ?",
        (duong_dan_anh, duong_dan_thu_nho, nguoi_dung["id"]),
    )
    db.commit()

    return jsonify({
        "thanh_cong": True,
        "thong_bao": (
            f"Tải ảnh đại diện thành công. Ảnh gốc {rong}x{cao} đã được cắt vuông {canh}x{canh}, "
            f"lưu thành ảnh đại diện {KICH_THUOC_ANH_DAI_DIEN}x{KICH_THUOC_ANH_DAI_DIEN} "
            f"và bản thu nhỏ {KICH_THUOC_ANH_THU_NHO}x{KICH_THUOC_ANH_THU_NHO}."
        ),
        "xem_anh_dai_dien": "GET /api/ho-so/anh-dai-dien",
        "xem_anh_thu_nho": "GET /api/ho-so/anh-thu-nho",
    })


@api_anh_dai_dien.get("/api/ho-so/anh-dai-dien")
def xem_anh_dai_dien():
    """Trả về ảnh đại diện (đã cắt vuông) của người dùng hiện tại."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi
    if not nguoi_dung["anh_dai_dien"] or not os.path.exists(nguoi_dung["anh_dai_dien"]):
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Bạn chưa có ảnh đại diện. Hãy tải lên bằng POST /api/ho-so/anh-dai-dien.",
        }), 404
    return send_file(nguoi_dung["anh_dai_dien"], mimetype="image/jpeg")


@api_anh_dai_dien.get("/api/ho-so/anh-thu-nho")
def xem_anh_thu_nho():
    """Trả về bản thu nhỏ của ảnh đại diện."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi
    if not nguoi_dung["anh_thu_nho"] or not os.path.exists(nguoi_dung["anh_thu_nho"]):
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Bạn chưa có bản thu nhỏ. Hãy tải ảnh đại diện lên trước.",
        }), 404
    return send_file(nguoi_dung["anh_thu_nho"], mimetype="image/jpeg")
