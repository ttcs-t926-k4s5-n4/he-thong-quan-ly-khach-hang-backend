import os
os.environ["DATABASE_PATH"] = "./test_login.db"

from fastapi.testclient import TestClient
from app.db import init_db, get_connection
from app.security import hash_password
from app.server import app

init_db()
conn = get_connection()
conn.execute("DELETE FROM login_attempts")
conn.execute("DELETE FROM users")
conn.execute(
    "INSERT INTO users(email, password_hash, role) VALUES(?,?,?)",
    ("user@company.local", hash_password("Password@123"), "user")
)
conn.commit()
conn.close()

client = TestClient(app)

def test_health():
    assert client.get("/health").json()["status"] == "ok"

def test_s1_01_login_success_and_role():
    """Tiêu chí 1: Đăng nhập đúng thì vào được trang chủ tương ứng với vai trò"""
    res = client.post("/api/auth/login", json={
        "email": "user@company.local",
        "password": "Password@123"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["message"] == "Đăng nhập thành công."
    assert data["user"]["role"] == "user"
    assert "redirect_url" in data

def test_s1_01_generic_error_message():
    """Tiêu chí 2: Sai thông tin hiển thị thông báo chung, không tiết lộ email có tồn tại hay không"""
    # Test với email không tồn tại
    res1 = client.post("/api/auth/login", json={
        "email": "nonexistent@company.local",
        "password": "Password@123"
    })
    assert res1.status_code == 401
    assert res1.json()["message"] == "Email hoặc mật khẩu không đúng."

    # Test với mật khẩu sai của email có thật
    res2 = client.post("/api/auth/login", json={
        "email": "user@company.local",
        "password": "WrongPassword"
    })
    assert res2.status_code == 401
    assert res2.json()["message"] == "Email hoặc mật khẩu không đúng."

def test_s1_01_lockout_after_5_failed_attempts():
    """Tiêu chí 3: Khoá tạm 15 phút sau 5 lần sai liên tiếp"""
    test_email = "lockout@company.local"
    # Nhập sai 5 lần
    for _ in range(5):
        client.post("/api/auth/login", json={"email": test_email, "password": "WrongPassword"})

    # Lần thử 6 bị khóa 429
    res = client.post("/api/auth/login", json={"email": test_email, "password": "WrongPassword"})
    assert res.status_code == 429
    assert "Tài khoản tạm thời bị khóa" in res.json()["message"]
