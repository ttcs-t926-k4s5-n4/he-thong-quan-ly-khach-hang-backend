"""Thông báo lỗi tiếng Việt và lớp lỗi dùng chung cho toàn ứng dụng."""

ROLE_LABELS = {
    "NHAN_VIEN": "Nhân viên kinh doanh",
    "TRUONG_NHOM": "Trưởng nhóm",
    "GIAM_DOC": "Giám đốc kinh doanh",
}

SCOPE_LABELS = {
    "mine": "Của tôi",
    "team": "Của nhóm tôi",
    "all": "Tất cả",
}


class AppError(Exception):
    """Lỗi nghiệp vụ, được chuyển thành JSON {error, message} kèm mã HTTP."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def unauthenticated() -> AppError:
    return AppError(401, "CHUA_DANG_NHAP",
                    "Bạn chưa đăng nhập hoặc phiên đăng nhập không hợp lệ. "
                    "Vui lòng đăng nhập để tiếp tục.")


def invalid_scope(value: str) -> AppError:
    return AppError(400, "PHAM_VI_KHONG_HOP_LE",
                    f"Phạm vi dữ liệu '{value}' không hợp lệ. Chỉ chấp nhận: "
                    "mine (Của tôi), team (Của nhóm tôi), all (Tất cả).")


def scope_not_allowed(role: str, max_scope: str, requested: str) -> AppError:
    return AppError(403, "VUOT_PHAM_VI_VAI_TRO",
                    f"Vai trò {ROLE_LABELS[role]} chỉ được xem dữ liệu trong phạm vi "
                    f"'{SCOPE_LABELS[max_scope]}'. Bạn không thể chọn phạm vi "
                    f"'{SCOPE_LABELS[requested]}'.")


def out_of_scope(entity_label: str, record_id: int, max_scope: str) -> AppError:
    return AppError(403, "NGOAI_PHAM_VI_DU_LIEU",
                    f"Bạn không có quyền xem {entity_label} #{record_id}. "
                    f"Bản ghi này nằm ngoài phạm vi dữ liệu của bạn "
                    f"({SCOPE_LABELS[max_scope]}). Nếu cần truy cập, vui lòng liên hệ "
                    "trưởng nhóm hoặc Giám đốc kinh doanh.")


def not_found(entity_label: str, record_id: int) -> AppError:
    return AppError(404, "KHONG_TIM_THAY",
                    f"Không tìm thấy {entity_label} #{record_id}.")


def unknown_resource(name: str) -> AppError:
    return AppError(404, "DANH_MUC_KHONG_TON_TAI",
                    f"Danh mục '{name}' không tồn tại. Các danh mục hợp lệ: "
                    "customers, opportunities, activities, quotes.")
