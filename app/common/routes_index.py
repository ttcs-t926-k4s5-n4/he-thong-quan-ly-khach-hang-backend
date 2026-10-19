"""Trang giới thiệu và danh mục API tự sinh từ các route đã đăng ký."""
from flask import Blueprint, current_app, jsonify

bp = Blueprint("index", __name__)


@bp.get("/")
@bp.get("/api")
def api_index():
    """Danh mục toàn bộ API của hệ thống."""
    endpoints = []
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        view = current_app.view_functions[rule.endpoint]
        doc = (view.__doc__ or "").strip().splitlines()
        methods = sorted(m for m in rule.methods if m not in ("HEAD", "OPTIONS"))
        endpoints.append({"methods": methods, "path": str(rule), "description": doc[0] if doc else ""})
    endpoints.sort(key=lambda e: (e["path"], e["methods"]))
    return jsonify({
        "name": "API CRM – Cơ hội bán hàng, Pipeline, Hoạt động & Công việc",
        "version": "1.0.0",
        "stories": ["SCRUM-87", "SCRUM-88", "SCRUM-89", "SCRUM-90", "SCRUM-99", "SCRUM-100"],
        "authentication": "Gọi POST /api/auth/login để lấy token, sau đó gửi header "
                          "Authorization: Bearer <token> cho các API còn lại.",
        "endpoints": endpoints,
    })
