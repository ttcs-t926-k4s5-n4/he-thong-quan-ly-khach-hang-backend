import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from app.db import close_db
from app.routes import register_routes
load_dotenv(Path(__file__).resolve().parent.parent/".env")
def _bool(name,default=False):
    value=os.getenv(name); return default if value is None else value.lower() in {"1","true","yes","on"}
def create_app(test_config=None):
    app=Flask(__name__)
    origins=[x.strip() for x in os.getenv("FRONTEND_ORIGINS","http://127.0.0.1:5174").split(",") if x.strip()]
    app.config.update(
      SESSION_TTL_SECONDS=int(os.getenv("SESSION_TTL_SECONDS","900")),
      SESSION_COOKIE_NAME=os.getenv("SESSION_COOKIE_NAME","crm_session"),
      SESSION_COOKIE_SECURE=_bool("SESSION_COOKIE_SECURE"),
    )
    if test_config: app.config.update(test_config)
    CORS(app,resources={r"/api/*":{"origins":origins}},supports_credentials=True)
    app.teardown_appcontext(close_db);register_routes(app);return app
