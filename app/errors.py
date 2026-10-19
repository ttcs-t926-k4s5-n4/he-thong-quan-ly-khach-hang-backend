"""Lỗi nghiệp vụ và bộ xử lý lỗi trả về JSON tiếng Việt.

Mọi lỗi trả về dạng: {"detail": "<thông báo tiếng Việt>", "error_code": "<MÃ_LỖI>", ...}
"""
from __future__ import annotations

from flask import jsonify, request
from werkzeug.exceptions import HTTPException


class AppError(Exception):
    status_code = 400
    default_code = "BAD_REQUEST"

    def __init__(self, message: str, *, code: str | None = None, extra: dict | None = None,
                 status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.extra = extra or {}
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self) -> dict:
        body = {"detail": self.message, "error_code": self.code}
        body.update(self.extra)
        return body


class ValidationFailed(AppError):
    """Dữ liệu gửi lên không hợp lệ (HTTP 422). errors: danh sách lỗi theo từng trường."""
    status_code = 422
    default_code = "VALIDATION_ERROR"

    def __init__(self, errors: list[dict], message: str | None = None):
        self.errors = errors
        if message is None:
            if len(errors) == 1:
                message = errors[0]["message"]
            else:
                message = "Dữ liệu gửi lên chưa hợp lệ: " + " ".join(e["message"] for e in errors)
        super().__init__(message, extra={"errors": errors})


class Unauthorized(AppError):
    status_code = 401
    default_code = "UNAUTHORIZED"


class Forbidden(AppError):
    status_code = 403
    default_code = "FORBIDDEN"


class NotFound(AppError):
    status_code = 404
    default_code = "NOT_FOUND"


class Conflict(AppError):
    status_code = 409
    default_code = "CONFLICT"


HTTP_MESSAGES = {
    400: "Yêu cầu không hợp lệ.",
    401: "Bạn chưa đăng nhập.",
    403: "Bạn không có quyền thực hiện thao tác này.",
    413: "Dữ liệu gửi lên quá lớn.",
    415: "Định dạng dữ liệu không được hỗ trợ.",
    429: "Bạn gửi quá nhiều yêu cầu, vui lòng thử lại sau.",
}


def register_error_handlers(app) -> None:
    from app.db import rollback_quietly

    @app.errorhandler(AppError)
    def _app_error(err: AppError):
        rollback_quietly()
        return jsonify(err.to_dict()), err.status_code

    @app.errorhandler(HTTPException)
    def _http_error(err: HTTPException):
        rollback_quietly()
        if err.code == 404:
            message = f"Không tìm thấy đường dẫn API: {request.path}"
        elif err.code == 405:
            message = f"Phương thức {request.method} không được hỗ trợ cho đường dẫn {request.path}."
        else:
            message = HTTP_MESSAGES.get(err.code, "Yêu cầu không thể xử lý.")
        return jsonify({"detail": message, "error_code": f"HTTP_{err.code}"}), err.code

    @app.errorhandler(Exception)
    def _unexpected(err: Exception):
        rollback_quietly()
        if app.testing:
            raise err
        app.logger.exception("Lỗi không mong muốn: %s", err)
        return jsonify({"detail": "Đã xảy ra lỗi hệ thống, vui lòng thử lại sau.",
                        "error_code": "INTERNAL_ERROR"}), 500
