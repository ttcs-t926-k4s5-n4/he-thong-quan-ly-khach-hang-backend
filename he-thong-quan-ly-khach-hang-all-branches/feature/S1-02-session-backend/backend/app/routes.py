from flask import Blueprint,Flask,current_app,jsonify,make_response,request
from app.session_service import authenticate,create_session,revoke_session,validate_and_extend
api=Blueprint("api",__name__,url_prefix="/api")
def cname():return str(current_app.config["SESSION_COOKIE_NAME"])
def set_cookie(resp,token):
    resp.set_cookie(cname(),token,max_age=int(current_app.config["SESSION_TTL_SECONDS"]),
                    httponly=True,secure=bool(current_app.config["SESSION_COOKIE_SECURE"]),samesite="Lax",path="/")
    return resp
def del_cookie(resp):resp.delete_cookie(cname(),path="/");return resp
@api.get("/health")
def health():return jsonify({"status":"ok","service":"s1-02-session-backend"})
@api.post("/session/login")
def login():
    body=request.get_json(silent=True) or {};user=authenticate(str(body.get("email","")),str(body.get("password","")))
    if user is None:return jsonify({"message":"Email hoặc mật khẩu không đúng."}),401
    token=create_session(user["id"])
    return set_cookie(make_response(jsonify({"message":"Đăng nhập thành công.","user":user})),token)
@api.get("/session/me")
def me():
    token=request.cookies.get(cname(),"")
    if not token:return jsonify({"code":"session_expired","message":"Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."}),401
    user=validate_and_extend(token)
    if user is None:
        return del_cookie(make_response(jsonify({"code":"session_expired","message":"Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."}),401))
    return set_cookie(make_response(jsonify({"user":user,"message":"Phiên đăng nhập đã được gia hạn."})),token)
@api.post("/session/logout")
def logout():
    token=request.cookies.get(cname(),"")
    if token:revoke_session(token)
    return del_cookie(make_response(jsonify({"message":"Đã đăng xuất an toàn."})))
def register_routes(app:Flask):app.register_blueprint(api)
