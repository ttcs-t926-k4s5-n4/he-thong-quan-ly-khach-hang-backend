import time
from flask import current_app
from werkzeug.security import check_password_hash
from app.db import get_db

GENERIC_LOGIN_MESSAGE="Email hoặc mật khẩu không đúng."
LOCKED_MESSAGE="Đăng nhập không thành công. Vui lòng thử lại sau 15 phút."

ROLE_LABEL={"admin":"Quản trị hệ thống","manager":"Giám đốc kinh doanh","employee":"Nhân viên kinh doanh"}
ROLE_HOME={"admin":"/app/admin","manager":"/app/manager","employee":"/app/employee"}

def login(email, password):
    db=get_db()
    cur=db.cursor()
    cur.execute("""
        SELECT id,full_name,email,password_hash,role,failed_login_attempts,locked_until
        FROM dbo.users WHERE LOWER(email)=LOWER(?)
    """,(email.strip().lower(),))
    row=cur.fetchone()
    if row is None:
        return 401, {"message":GENERIC_LOGIN_MESSAGE}

    user={
        "id":int(row[0]),"full_name":str(row[1]),"email":str(row[2]),
        "password_hash":str(row[3]),"role":str(row[4]),
        "failures":int(row[5] or 0),"locked_until":row[6],
    }
    now=int(time.time())

    if user["locked_until"] is not None and int(user["locked_until"])>now:
        return 429, {"message":LOCKED_MESSAGE}

    if user["locked_until"] is not None and int(user["locked_until"])<=now:
        cur.execute("UPDATE dbo.users SET failed_login_attempts=0,locked_until=NULL WHERE id=?",(user["id"],))
        db.commit()
        user["failures"]=0

    if not check_password_hash(user["password_hash"],password):
        failures=user["failures"]+1
        lock_until=now+int(current_app.config["LOGIN_LOCK_SECONDS"]) if failures>=int(current_app.config["LOGIN_MAX_FAILURES"]) else None
        cur.execute("UPDATE dbo.users SET failed_login_attempts=?,locked_until=? WHERE id=?",(failures,lock_until,user["id"]))
        db.commit()
        return (429,{"message":LOCKED_MESSAGE}) if lock_until else (401,{"message":GENERIC_LOGIN_MESSAGE})

    cur.execute("UPDATE dbo.users SET failed_login_attempts=0,locked_until=NULL WHERE id=?",(user["id"],))
    db.commit()
    role=user["role"]
    return 200,{
        "message":"Đăng nhập thành công.",
        "user":{"id":user["id"],"full_name":user["full_name"],"email":user["email"],"role":role,"role_label":ROLE_LABEL.get(role,role)},
        "redirect_url":ROLE_HOME.get(role,"/app/employee"),
    }
