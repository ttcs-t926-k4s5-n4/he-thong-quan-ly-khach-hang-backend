"""
Hệ Thống Menu Điều Hướng Theo Phân Quyền (RBAC Navigation System)
Đáp ứng yêu cầu User Story SCRUM-16 / SCRUM-30:
1. Mục menu không thuộc quyền thì không hiển thị
2. Hiển thị tên, vai trò và nhóm kinh doanh đang thuộc về
3. Dùng được thuận tiện trên màn hình 360px
"""

import os
from functools import wraps
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    abort,
    jsonify
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "rbac-demo-secret-key-2026")

# ==========================================
# 1. CẤU TRÚC DANH MỤC MENU TOÀN HỆ THỐNG
# ==========================================
ALL_MENU_ITEMS = [
    {
        "id": "dashboard",
        "label": "Bảng điều khiển",
        "icon": "dashboard",
        "url": "/dashboard",
        "required_permission": "view_dashboard",
        "description": "Tổng quan chỉ số hiệu suất & thông báo mới nhất",
        "badge": "Chính"
    },
    {
        "id": "customers",
        "label": "Khách hàng của tôi",
        "icon": "users",
        "url": "/customers",
        "required_permission": "manage_customers",
        "description": "Danh sách khách hàng tiềm năng, liên hệ & chăm sóc",
        "badge": "24"
    },
    {
        "id": "deals",
        "label": "Đơn hàng & Hợp đồng",
        "icon": "shopping-bag",
        "url": "/deals",
        "required_permission": "manage_deals",
        "description": "Theo dõi tiến độ đơn hàng và hợp đồng đang xử lý",
        "badge": "8"
    },
    {
        "id": "team_reports",
        "label": "Báo cáo doanh số nhóm",
        "icon": "bar-chart",
        "url": "/team-reports",
        "required_permission": "view_team_reports",
        "description": "Báo cáo doanh thu, tiến độ và năng suất toàn nhóm",
        "badge": "Team"
    },
    {
        "id": "team_targets",
        "label": "Chỉ tiêu & KPI nhóm",
        "icon": "target",
        "url": "/team-targets",
        "required_permission": "manage_team_targets",
        "description": "Thiết lập chỉ tiêu doanh số và đánh giá KPI thành viên",
        "badge": "KPI"
    },
    {
        "id": "user_management",
        "label": "Quản lý nhân viên",
        "icon": "user-check",
        "url": "/users",
        "required_permission": "manage_users",
        "description": "Danh sách tài khoản, phân quyền chức vụ & đội ngũ",
        "badge": "Admin"
    },
    {
        "id": "system_settings",
        "label": "Cấu hình hệ thống",
        "icon": "settings",
        "url": "/settings",
        "required_permission": "system_settings",
        "description": "Cấu hình thông số kỹ thuật, bảo mật & sao lưu",
        "badge": "Hệ thống"
    }
]

# ==========================================
# 2. DỮ LIỆU TÀI KHOẢN MẪU ĐỂ TEST PHÂN QUYỀN
# ==========================================
# Mỗi tài khoản có: Họ tên, Vai trò, Nhóm kinh doanh, Danh sách quyền
USERS_DATABASE = {
    "admin": {
        "id": "USR-001",
        "username": "admin",
        "full_name": "Nguyễn Tuấn Anh",
        "role_code": "DIRECTOR",
        "role_name": "Giám đốc kinh doanh",
        "role_badge_class": "badge-director",
        "business_team": "Khối Phát Triển Kinh Doanh Toàn Quốc",
        "email": "tuananh.nguyen@enterprise.vn",
        "avatar_initials": "TA",
        "avatar_color": "#4f46e5",
        "permissions": [
            "view_dashboard",
            "manage_customers",
            "manage_deals",
            "view_team_reports",
            "manage_team_targets",
            "manage_users",
            "system_settings"
        ]
    },
    "manager": {
        "id": "USR-002",
        "username": "manager",
        "full_name": "Trần Thị Minh Tâm",
        "role_code": "TEAM_LEAD",
        "role_name": "Trưởng nhóm kinh doanh",
        "role_badge_class": "badge-manager",
        "business_team": "Nhóm Bán Lẻ Khu Vực Miền Bắc",
        "email": "minhtam.tran@enterprise.vn",
        "avatar_initials": "MT",
        "avatar_color": "#0891b2",
        "permissions": [
            "view_dashboard",
            "manage_customers",
            "manage_deals",
            "view_team_reports",
            "manage_team_targets"
        ]
    },
    "sales": {
        "id": "USR-003",
        "username": "sales",
        "full_name": "Lê Hoàng Phúc",
        "role_code": "SALES_EXECUTIVE",
        "role_name": "Chuyên viên kinh doanh",
        "role_badge_class": "badge-sales",
        "business_team": "Nhóm Bán Lẻ Khu Vực Miền Bắc",
        "email": "hoangphuc.le@enterprise.vn",
        "avatar_initials": "HP",
        "avatar_color": "#059669",
        "permissions": [
            "view_dashboard",
            "manage_customers",
            "manage_deals"
        ]
    },
    "intern": {
        "id": "USR-004",
        "username": "intern",
        "full_name": "Đỗ Mai Linh",
        "role_code": "INTERN",
        "role_name": "Thực tập sinh kinh doanh",
        "role_badge_class": "badge-intern",
        "business_team": "Nhóm Khách Hàng Doanh Nghiệp (B2B)",
        "email": "mailinh.do@enterprise.vn",
        "avatar_initials": "ML",
        "avatar_color": "#d97706",
        "permissions": [
            "view_dashboard"
        ]
    }
}


# ==========================================
# 3. HÀM XỬ LÝ LỌC MENU DỰA TRÊN QUYỀN (RBAC)
# ==========================================
def get_user_menu(user):
    """
    Yêu cầu: "Mục menu không thuộc quyền thì không hiển thị"
    Hàm này duyệt qua toàn bộ menu hệ thống và chỉ giữ lại những mục
    mà user hiện tại có permission tương ứng.
    """
    if not user or "permissions" not in user:
        return []
    
    user_permissions = set(user["permissions"])
    filtered_menu = []
    
    for item in ALL_MENU_ITEMS:
        if item["required_permission"] in user_permissions:
            filtered_menu.append(item)
            
    return filtered_menu


def get_current_user():
    """Lấy thông tin người dùng từ session, mặc định là 'sales' nếu chưa chọn."""
    username = session.get("username", "sales")
    return USERS_DATABASE.get(username, USERS_DATABASE["sales"])


# Decorator kiểm tra quyền truy cập route phía backend
def require_permission(perm):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if perm not in user.get("permissions", []):
                flash(
                    f"Truy cập bị từ chối: Tài khoản '{user['full_name']}' không có quyền '{perm}'!",
                    "danger"
                )
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Context Processor để tự động truyền thông tin user và menu đã lọc vào mọi template
@app.context_processor
def inject_user_and_menu():
    user = get_current_user()
    user_menu = get_user_menu(user)
    return {
        "current_user": user,
        "user_menu": user_menu,
        "all_users": USERS_DATABASE,
        "all_menu_items": ALL_MENU_ITEMS
    }


# ==========================================
# 4. CÁC ĐƯỜNG DẪN (ROUTES) CỦA ỨNG DỤNG
# ==========================================

@app.route("/")
def index():
    return redirect(url_for("dashboard"))


@app.route("/switch-user/<username>")
def switch_user(username):
    """Tiện ích chuyển nhanh vai trò/tài khoản để test trực tiếp trên UI."""
    if username in USERS_DATABASE:
        session["username"] = username
        flash(f"Đã chuyển sang tài khoản: {USERS_DATABASE[username]['full_name']} ({USERS_DATABASE[username]['role_name']})", "success")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    user = get_current_user()
    user_menu = get_user_menu(user)
    hidden_count = len(ALL_MENU_ITEMS) - len(user_menu)
    return render_template(
        "pages/dashboard.html",
        active_tab="dashboard",
        title="Bảng Điều Khiển",
        hidden_count=hidden_count
    )


@app.route("/customers")
@require_permission("manage_customers")
def customers():
    sample_customers = [
        {"id": "KH-1029", "name": "Công ty TNHH Á Châu", "phone": "0912 345 678", "revenue": "180.000.000 đ", "status": "Tiềm năng"},
        {"id": "KH-1030", "name": "Tập đoàn Đầu tư Sao Mai", "phone": "0988 765 432", "revenue": "450.000.000 đ", "status": "Đang đàm phán"},
        {"id": "KH-1031", "name": "Doanh nghiệp Tư nhân Hoàng Long", "phone": "0903 112 233", "revenue": "95.000.000 đ", "status": "Đã chốt hợp đồng"},
    ]
    return render_template(
        "pages/customers.html",
        active_tab="customers",
        title="Quản Lý Khách Hàng",
        customers=sample_customers
    )


@app.route("/deals")
@require_permission("manage_deals")
def deals():
    sample_deals = [
        {"code": "HD-2026-01", "customer": "Công ty TNHH Á Châu", "value": "180.000.000 đ", "stage": "Gửi báo giá", "progress": 65},
        {"code": "HD-2026-02", "customer": "Tập đoàn Đầu tư Sao Mai", "value": "450.000.000 đ", "stage": "Soạn thảo hợp đồng", "progress": 85},
        {"code": "HD-2026-03", "customer": "Doanh nghiệp Tư nhân Hoàng Long", "value": "95.000.000 đ", "stage": "Hoàn tất thanh toán", "progress": 100},
    ]
    return render_template(
        "pages/deals.html",
        active_tab="deals",
        title="Đơn Hàng & Hợp Đồng",
        deals=sample_deals
    )


@app.route("/team-reports")
@require_permission("view_team_reports")
def team_reports():
    team_data = [
        {"name": "Trần Thị Minh Tâm", "role": "Trưởng nhóm", "target": "800 tr", "achieved": "850 tr", "rate": "106%"},
        {"name": "Lê Hoàng Phúc", "role": "Chuyên viên", "target": "400 tr", "achieved": "385 tr", "rate": "96%"},
        {"name": "Nguyễn Văn Đức", "role": "Chuyên viên", "target": "350 tr", "achieved": "370 tr", "rate": "105%"},
    ]
    return render_template(
        "pages/team_reports.html",
        active_tab="team_reports",
        title="Báo Cáo Doanh Số Toàn Nhóm",
        team_data=team_data
    )


@app.route("/team-targets")
@require_permission("manage_team_targets")
def team_targets():
    return render_template(
        "pages/team_targets.html",
        active_tab="team_targets",
        title="Chỉ Tiêu & Phân Bổ KPI Nhóm"
    )


@app.route("/users")
@require_permission("manage_users")
def users():
    return render_template(
        "pages/users.html",
        active_tab="user_management",
        title="Quản Lý Tài Khoản Nhân Viên",
        users_list=USERS_DATABASE.values()
    )


@app.route("/settings")
@require_permission("system_settings")
def settings():
    return render_template(
        "pages/settings.html",
        active_tab="system_settings",
        title="Cấu Hình Hệ Thống"
    )


# API endpoint để kiểm tra hoặc tích hợp front-end
@app.route("/api/user-info")
def api_user_info():
    user = get_current_user()
    user_menu = get_user_menu(user)
    return jsonify({
        "full_name": user["full_name"],
        "role_name": user["role_name"],
        "business_team": user["business_team"],
        "accessible_menu_count": len(user_menu),
        "accessible_menus": [item["label"] for item in user_menu]
    })


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 60)
    print(" HE THONG MENU DIEU HUONG PHAN QUYEN (RBAC NAVIGATION SYSTEM)")
    print(" User Story: SCRUM-16 / SCRUM-30")
    print(" Dang chay tai: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host="127.0.0.1", port=5000)

