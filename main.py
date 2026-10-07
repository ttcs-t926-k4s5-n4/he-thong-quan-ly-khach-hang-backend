# -*- coding: utf-8 -*-
"""
================================================================================
BACKEND CRM KHÁCH HÀNG - FILE CHẠY CHÍNH
Gồm 3 chức năng theo Jira: SCRUM-69, SCRUM-70, SCRUM-71
================================================================================
Cấu trúc project (mỗi SCRUM một file -> tương ứng một nhánh feature trên GitHub):
    main.py               <- file chạy chính
    cau_hinh.py           <- hằng số, trạng thái, regex kiểm tra
    co_so_du_lieu.py      <- SQLite: bảng, chỉ mục, dữ liệu mẫu
    xac_thuc.py           <- xác thực + PHÂN QUYỀN xem khách hàng (SCRUM-69)
    api_khach_hang.py     <- [SCRUM-69] hồ sơ khách hàng doanh nghiệp
    api_nguoi_lien_he.py  <- [SCRUM-70] người liên hệ & vai trò quyết định mua
    api_trang_360.py      <- [SCRUM-71] trang 360 + cơ hội/hoạt động/tệp đính kèm
    kiem_thu.py           <- kiểm thử tự động toàn bộ tiêu chí

Cách chạy:
    pip install -r requirements.txt
    python main.py
Server: http://127.0.0.1:5000  (mở GET / để xem danh sách API)
Xác thực demo: header X-User-Id hoặc ?user_id= trên URL
    1 = Nguyễn Quản Trị  (Quản trị hệ thống)
    2 = Lê Trưởng Nhóm   (Trưởng nhóm - Nhóm kinh doanh 1)
    3 = Trần Nhân Viên A (Nhân viên - Nhóm kinh doanh 1)
    4 = Phạm Nhân Viên B (Nhân viên - Nhóm kinh doanh 2)
================================================================================
"""
from flask import Flask, jsonify

from co_so_du_lieu import khoi_tao_csdl, dong_csdl
from api_khach_hang import api_khach_hang
from api_nguoi_lien_he import api_nguoi_lien_he
from api_trang_360 import api_trang_360


def tao_ung_dung() -> Flask:
    """Tạo ứng dụng Flask và đăng ký 3 nhóm chức năng."""
    app = Flask(__name__)
    app.json.ensure_ascii = False  # trả về tiếng Việt có dấu trong JSON

    app.register_blueprint(api_khach_hang)     # SCRUM-69
    app.register_blueprint(api_nguoi_lien_he)  # SCRUM-70
    app.register_blueprint(api_trang_360)      # SCRUM-71

    app.teardown_appcontext(dong_csdl)

    @app.get("/")
    def trang_chu():
        return jsonify({
            "ten_he_thong": "Backend CRM Khách hàng - 3 chức năng (SCRUM-69, SCRUM-70, SCRUM-71)",
            "xac_thuc": (
                "Gửi header X-User-Id hoặc thêm ?user_id= vào URL. "
                "1=Quản trị, 2=Trưởng nhóm (Nhóm KD 1), 3=Nhân viên A (Nhóm KD 1), 4=Nhân viên B (Nhóm KD 2)."
            ),
            "danh_sach_api": {
                "SCRUM-69 - Hồ sơ khách hàng doanh nghiệp": {
                    "Tạo khách hàng (tên công ty, MST, ngành nghề, quy mô, website, địa chỉ, người sở hữu)":
                        "POST /api/khach-hang  (JSON)",
                    "Danh sách khách hàng (lọc theo quyền: nhân viên/trưởng nhóm/quản trị)":
                        "GET  /api/khach-hang",
                    "Xem chi tiết một khách hàng": "GET  /api/khach-hang/<id>",
                    "Cập nhật hồ sơ / trạng thái (Tiềm năng, Đang giao dịch, Khách hàng, Ngừng hợp tác)":
                        "PUT  /api/khach-hang/<id>  (JSON)",
                },
                "SCRUM-70 - Người liên hệ & vai trò quyết định mua": {
                    "Thêm người liên hệ (chức danh, email, SĐT, vai trò mua, đầu mối chính)":
                        "POST /api/khach-hang/<id>/nguoi-lien-he  (JSON)",
                    "Danh sách người liên hệ của khách hàng": "GET  /api/khach-hang/<id>/nguoi-lien-he",
                    "Cập nhật thông tin / vai trò quyết định mua": "PUT  /api/nguoi-lien-he/<id>  (JSON)",
                    "Đặt làm đầu mối chính": "PUT  /api/nguoi-lien-he/<id>/dau-moi-chinh",
                    "Chuyển sang công ty khác (giữ nguyên lịch sử)":
                        "PUT  /api/nguoi-lien-he/<id>/chuyen-cong-ty  (JSON: khach_hang_moi_id)",
                    "Xem lịch sử các công ty đã thuộc về": "GET  /api/nguoi-lien-he/<id>/lich-su",
                },
                "SCRUM-71 - Trang 360 của khách hàng": {
                    "Trang 360 (công ty + người liên hệ + cơ hội + dòng thời gian + tệp; kèm 2 tổng giá trị và thời gian tải)":
                        "GET  /api/khach-hang/<id>/trang-360",
                    "Tạo cơ hội bán hàng": "POST /api/khach-hang/<id>/co-hoi  (JSON)",
                    "Ghi hoạt động vào dòng thời gian": "POST /api/khach-hang/<id>/hoat-dong  (JSON)",
                    "Tải tệp đính kèm (tối đa 10MB)": "POST /api/khach-hang/<id>/tep-dinh-kem  (form-data: tep)",
                    "Tải xuống tệp đính kèm": "GET  /api/tep-dinh-kem/<id>",
                },
            },
        })

    # ----- Xử lý lỗi chung, trả về tiếng Việt -----
    @app.errorhandler(404)
    def khong_tim_thay(_):
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Không tìm thấy đường dẫn API này. Mở GET / để xem danh sách API.",
        }), 404

    @app.errorhandler(405)
    def sai_phuong_thuc(_):
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Phương thức HTTP không đúng cho đường dẫn này (kiểm tra lại GET/POST/PUT).",
        }), 405

    @app.errorhandler(500)
    def loi_he_thong(_):
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Có lỗi xảy ra trong hệ thống. Vui lòng thử lại.",
        }), 500

    return app


app = tao_ung_dung()


if __name__ == "__main__":
    khoi_tao_csdl()
    print("=" * 70)
    print("BACKEND CRM KHÁCH HÀNG - SCRUM-69 / SCRUM-70 / SCRUM-71")
    print("Server đang chạy tại: http://127.0.0.1:5000")
    print("Mở GET / để xem danh sách API. Đăng nhập demo: ?user_id=3 (Nhân viên A).")
    print("=" * 70)
    app.run(host="127.0.0.1", port=5000, debug=True)
