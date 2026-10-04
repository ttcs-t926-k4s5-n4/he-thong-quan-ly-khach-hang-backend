from app.auth import GENERIC_LOGIN_MESSAGE, ROLE_HOME
def test_generic_message():
    assert GENERIC_LOGIN_MESSAGE=="Email hoặc mật khẩu không đúng."
def test_redirects():
    assert ROLE_HOME["admin"]=="/app/admin"
    assert ROLE_HOME["manager"]=="/app/manager"
    assert ROLE_HOME["employee"]=="/app/employee"
