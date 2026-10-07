"""
app/__init__.py — Flask application factory
"""
import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from app.db import close_db
from app.mailer import create_mailer
from app.routes import register_routes

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    return default if v is None else v.strip().lower() in {"1", "true", "yes", "on"}


def _origins() -> list[str]:
    raw = os.environ.get("FRONTEND_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173")
    return [x.strip().rstrip("/") for x in raw.split(",") if x.strip()]


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "sprint1-dev-secret-change-me"),
        PERMANENT_SESSION_LIFETIME=timedelta(
            seconds=int(os.environ.get("SESSION_TTL_SECONDS", "900"))
        ),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=_bool("SESSION_COOKIE_SECURE"),
        SESSION_TTL_SECONDS=int(os.environ.get("SESSION_TTL_SECONDS", "900")),
        LOGIN_MAX_FAILURES=int(os.environ.get("LOGIN_MAX_FAILURES", "5")),
        LOGIN_LOCK_SECONDS=int(os.environ.get("LOGIN_LOCK_SECONDS", "900")),
        RESET_TOKEN_TTL_SECONDS=int(os.environ.get("RESET_TOKEN_TTL_SECONDS", "1800")),
        ACTIVATION_TOKEN_TTL_SECONDS=int(os.environ.get("ACTIVATION_TOKEN_TTL_SECONDS", "86400")),
        FRONTEND_BASE_URL=os.environ.get("FRONTEND_BASE_URL", "http://127.0.0.1:5173").rstrip("/"),
        MAIL_BACKEND=os.environ.get("MAIL_BACKEND", "console"),
        MAIL_FROM=os.environ.get("MAIL_FROM", "CRM System <no-reply@example.com>"),
        SMTP_HOST=os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        SMTP_PORT=int(os.environ.get("SMTP_PORT", "587")),
        SMTP_USERNAME=os.environ.get("SMTP_USERNAME", ""),
        SMTP_PASSWORD=os.environ.get("SMTP_PASSWORD", ""),
        SMTP_USE_SSL=_bool("SMTP_USE_SSL"),
        SMTP_STARTTLS=_bool("SMTP_STARTTLS", True),
        MAX_CONTENT_LENGTH=64 * 1024,
        DEBUG=_bool("FLASK_DEBUG"),
    )

    if test_config:
        app.config.update(test_config)

    origins = _origins()
    CORS(
        app,
        resources={r"/api/*": {"origins": origins}},
        supports_credentials=True,
    )

    app.teardown_appcontext(close_db)
    app.config["MAILER"] = create_mailer(app.config)
    register_routes(app)

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response

    return app
