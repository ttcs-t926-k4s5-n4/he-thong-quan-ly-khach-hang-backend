"""Backend CRM – Cơ hội bán hàng, Pipeline kanban, Dòng sản phẩm, Điều kiện chuyển giai đoạn,
Hoạt động với khách hàng và Công việc (SCRUM-87, 88, 89, 90, 99, 100).

Khởi tạo ứng dụng Flask theo mẫu application factory. Blueprint của từng story nằm trong
app/features/<tên>/routes.py và được đăng ký tự động.
"""
from __future__ import annotations

import importlib
import os
import pkgutil

from flask import Flask

from app import db
from app.config import Config
from app.errors import register_error_handlers


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    # JSON trả về giữ nguyên tiếng Việt có dấu, giữ thứ tự khoá, khai báo rõ UTF-8
    app.json.ensure_ascii = False
    app.json.sort_keys = False
    app.json.mimetype = "application/json; charset=utf-8"

    os.makedirs(os.path.dirname(os.path.abspath(app.config["DATABASE"])), exist_ok=True)
    db.init_app(app)
    register_error_handlers(app)

    from app.common.routes_auth import bp as auth_bp
    from app.common.routes_index import bp as index_bp
    from app.common.routes_lookups import bp as lookups_bp

    app.register_blueprint(index_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(lookups_bp)
    _register_feature_blueprints(app)

    if app.config.get("AUTO_INIT_DB"):
        with app.app_context():
            db.init_db()
            from app import seed

            if seed.is_empty():
                seed.seed_all()
    return app


def _register_feature_blueprints(app: Flask) -> None:
    """Tự đăng ký blueprint của mọi story trong app/features (mỗi story một thư mục)."""
    from app import features

    for module in sorted(pkgutil.iter_modules(features.__path__), key=lambda m: m.name):
        if not module.ispkg:
            continue
        name = f"{features.__name__}.{module.name}.routes"
        try:
            routes = importlib.import_module(name)
        except ModuleNotFoundError as exc:
            if exc.name == name:
                continue
            raise
        app.register_blueprint(routes.bp)
