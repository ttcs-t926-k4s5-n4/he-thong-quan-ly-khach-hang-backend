import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from app.db import close_db
from app.mailer import create_mailer
from app.routes import register_routes

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _cors_origins() -> list[str]:
    raw = os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    )
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "s1-03-local-secret-key"),
        FRONTEND_BASE_URL=os.environ.get(
            "FRONTEND_BASE_URL", "http://127.0.0.1:5173"
        ).rstrip("/"),
        CORS_ALLOWED_ORIGINS=_cors_origins(),
        RESET_TOKEN_TTL_SECONDS=int(
            os.environ.get("RESET_TOKEN_TTL_SECONDS", "1800")
        ),
        MAIL_BACKEND=os.environ.get("MAIL_BACKEND", "console"),
        MAIL_FROM=os.environ.get(
            "MAIL_FROM", "CRM System <no-reply@example.com>"
        ),
        SMTP_HOST=os.environ.get("SMTP_HOST", ""),
        SMTP_PORT=int(os.environ.get("SMTP_PORT", "587")),
        SMTP_USERNAME=os.environ.get("SMTP_USERNAME", ""),
        SMTP_PASSWORD=os.environ.get("SMTP_PASSWORD", ""),
        SMTP_USE_SSL=_env_bool("SMTP_USE_SSL"),
        SMTP_STARTTLS=_env_bool("SMTP_STARTTLS", True),
        DEMO_USER_ENABLED=_env_bool("DEMO_USER_ENABLED", True),
        DEMO_USER_EMAIL=os.environ.get(
            "DEMO_USER_EMAIL", "demo@company.local"
        ),
        DEMO_USER_PASSWORD=os.environ.get(
            "DEMO_USER_PASSWORD", "Demo@123456"
        ),
        MAX_CONTENT_LENGTH=16 * 1024,
        DEBUG=_env_bool("FLASK_DEBUG"),
    )

    if test_config:
        app.config.update(test_config)

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ALLOWED_ORIGINS"]}},
    )

    app.teardown_appcontext(close_db)

    if "MAILER" not in app.config:
        app.config["MAILER"] = create_mailer(app.config)

    register_routes(app)

    @app.after_request
    def apply_security_headers(response: Any) -> Any:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    return app
