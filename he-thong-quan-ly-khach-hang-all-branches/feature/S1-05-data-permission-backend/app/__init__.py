"""SCRUM-29 — Phân quyền dữ liệu theo vai trò và dữ liệu sở hữu."""
import os

from flask import Flask, jsonify

from . import db
from .messages import AppError


def create_app(test_config=None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(DATABASE=os.path.join(app.instance_path, "crm.db"))
    if test_config:
        app.config.update(test_config)
    app.json.ensure_ascii = False  # JSON tiếng Việt có dấu, không bị \uXXXX
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    from .routes import bp
    app.register_blueprint(bp)

    @app.errorhandler(AppError)
    def handle_app_error(err: AppError):
        return jsonify({"error": err.code, "message": err.message}), err.status

    return app
