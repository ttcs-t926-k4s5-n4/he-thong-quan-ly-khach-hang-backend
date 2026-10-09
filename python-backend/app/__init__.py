"""
Ứng dụng Flask cho epic SCRUM-19 — Lead & Marketing (chỉ backend).

Mỗi story là một module độc lập trong app/features. Module nào có mặt trong
nhánh hiện tại thì được nạp, nên từng nhánh feature/SCRUM-xx vẫn chạy riêng được.
"""
import importlib
import logging
import os

from flask import Flask
from werkzeug.exceptions import HTTPException

from app.core import ApiError, SlidingWindowLimiter, close_db, core_bp, init_db

FEATURE_MODULES = [
    "app.features.scrum78_web_form",
    "app.features.scrum79_lead_import",
    "app.features.scrum80_campaign_tracking",
]

HTTP_MESSAGES = {
    400: "Yêu cầu không hợp lệ",
    404: "Không tìm thấy đường dẫn API",
    405: "Phương thức HTTP không được hỗ trợ cho đường dẫn này",
    413: "Tệp hoặc dữ liệu gửi lên vượt quá dung lượng cho phép (tối đa 5MB)",
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _env_bool(name, default="0"):
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


def create_app(overrides=None):
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.json.sort_keys = False
    app.config.update(
        DB_PATH=os.getenv("DB_PATH", os.path.join(BASE_DIR, "data", "crm_leads.db")),
        TRUST_PROXY=_env_bool("TRUST_PROXY"),
        PUBLIC_BASE_URL=os.getenv("PUBLIC_BASE_URL", "").rstrip("/"),
        RATE_LIMIT_PER_FORM=os.getenv("RATE_LIMIT_PER_FORM", "5/600"),   # 5 lần / 10 phút / IP / biểu mẫu
        RATE_LIMIT_PER_IP=os.getenv("RATE_LIMIT_PER_IP", "20/3600"),     # 20 lần / giờ / IP (mọi biểu mẫu)
        MIN_FILL_SECONDS=float(os.getenv("MIN_FILL_SECONDS", "3")),
        MAX_IMPORT_ROWS=int(os.getenv("MAX_IMPORT_ROWS", "2000")),
        IMPORT_PREVIEW_TTL_MINUTES=int(os.getenv("IMPORT_PREVIEW_TTL_MINUTES", "30")),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    )
    if overrides:
        app.config.update(overrides)

    init_db(app.config["DB_PATH"])
    app.extensions["rate_limiter"] = SlidingWindowLimiter()
    app.teardown_appcontext(close_db)

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-User-Id"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
        return response

    @app.errorhandler(ApiError)
    def handle_api_error(err):
        body = {"error": {"status": err.status, "message": err.message}}
        if err.details:
            body["error"]["details"] = err.details
        return body, err.status, err.headers

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        message = HTTP_MESSAGES.get(err.code, err.description)
        return {"error": {"status": err.code, "message": message}}, err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logging.getLogger(__name__).exception("Lỗi không mong muốn")
        return {"error": {"status": 500, "message": "Lỗi hệ thống, vui lòng thử lại sau"}}, 500

    app.register_blueprint(core_bp)

    features = []
    for module_name in FEATURE_MODULES:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name == module_name:   # feature chưa có trong nhánh này -> bỏ qua
                continue
            raise
        app.register_blueprint(module.bp)
        features.append(module.FEATURE)
    app.config["FEATURES"] = features

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "crm-lead-marketing (python)", "features": features}

    return app
