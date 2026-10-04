from flask import Blueprint, Flask, jsonify, request
from app.auth import GENERIC_LOGIN_MESSAGE, login

api=Blueprint("api",__name__,url_prefix="/api")

@api.get("/health")
def health(): return jsonify({"status":"ok","service":"s1-01-login-backend"})

@api.post("/auth/login")
def login_route():
    body=request.get_json(silent=True) or {}
    email=str(body.get("email","")).strip()
    password=str(body.get("password",""))
    if not email or not password:
        return jsonify({"message":GENERIC_LOGIN_MESSAGE}),401
    status,payload=login(email,password)
    return jsonify(payload),status

def register_routes(app:Flask): app.register_blueprint(api)
