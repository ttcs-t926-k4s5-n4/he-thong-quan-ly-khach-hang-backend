import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from app.db import close_db
from app.routes import register_routes

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

def create_app(test_config=None):
    app=Flask(__name__)
    origins=[x.strip() for x in os.getenv("FRONTEND_ORIGINS","http://127.0.0.1:5173").split(",") if x.strip()]
    app.config.update(
        LOGIN_MAX_FAILURES=int(os.getenv("LOGIN_MAX_FAILURES","5")),
        LOGIN_LOCK_SECONDS=int(os.getenv("LOGIN_LOCK_SECONDS","900")),
    )
    if test_config: app.config.update(test_config)
    CORS(app,resources={r"/api/*":{"origins":origins}})
    app.teardown_appcontext(close_db)
    register_routes(app)
    return app
