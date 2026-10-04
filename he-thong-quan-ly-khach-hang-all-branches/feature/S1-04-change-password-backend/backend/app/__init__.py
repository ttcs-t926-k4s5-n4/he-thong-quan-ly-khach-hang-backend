import os
from datetime import timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from app.db import close_db
from app.routes import register_routes
from app.security import validate_api_origin

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _session_ttl_seconds() -> int:
    return int(os.environ.get("LOGIN_SESSION_TTL_SECONDS", str(8 * 60 * 60)))


def _frontend_origins() -> list[str]:
    raw = os.environ.get("FRONTEND_ORIGINS", "http://localhost:5173")
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    ttl = _session_ttl_seconds()

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "s1-04-local-secret-key"),
        FRONTEND_ORIGINS=_frontend_origins(),
        LOGIN_SESSION_TTL_SECONDS=ttl,
        PERMANENT_SESSION_LIFETIME=timedelta(seconds=ttl),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=_env_bool("SESSION_COOKIE_SECURE"),
        MAX_CONTENT_LENGTH=16 * 1024,
        DEBUG=_env_bool("FLASK_DEBUG"),
    )

    if test_config:
        app.config.update(test_config)

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["FRONTEND_ORIGINS"]}},
        supports_credentials=True,
    )

    app.teardown_appcontext(close_db)
    app.before_request(validate_api_origin)
    register_routes(app)

    @app.after_request
    def apply_security_headers(response: Any) -> Any:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    return app
