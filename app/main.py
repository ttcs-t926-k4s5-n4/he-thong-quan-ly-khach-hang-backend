import io
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Cookie, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from pydantic import BaseModel, EmailStr

from .db import connect, db_cursor, init_database, row_to_dict, rows_to_dicts
from .security import hash_password, hash_token, new_token, password_error, verify_password
from .seed import seed_demo_data

SESSION_MINUTES = int(os.getenv("SESSION_IDLE_MINUTES", "15"))
RESET_MINUTES = int(os.getenv("RESET_TOKEN_MINUTES", "30"))
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
COOKIE_NAME = "crm_session"

app = FastAPI(title="Hệ thống quản lý khách hàng - Sprint 1", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_database()
    seed_demo_data()


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_roles(cur, user_id: int) -> list[str]:
    cur.execute("SELECT r.code FROM user_roles ur JOIN roles r ON r.id=ur.role_id WHERE ur.user_id=? ORDER BY r.id", user_id)
    return [r[0] for r in cur.fetchall()]


def public_user(cur, user_id: int):
    cur.execute("""SELECT u.id,u.full_name,u.email,u.status,u.data_scope,u.business_group_id,u.is_active,g.name group_name
                   FROM users u LEFT JOIN business_groups g ON g.id=u.business_group_id WHERE u.id=?""", user_id)
    u = row_to_dict(cur, cur.fetchone())
    if not u: return None
    u["roles"] = get_roles(cur, user_id)
    return u


def create_session(cur, user_id: int, version: int):
    token = new_token()
    cur.execute("INSERT INTO login_sessions(token_hash,user_id,credentials_version,expires_at) VALUES(?,?,?,?)", hash_token(token), user_id, version, utcnow()+timedelta(minutes=SESSION_MINUTES))
    return token


def current_user(request: Request, required: bool = True):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        if required: raise HTTPException(401, "Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại.")
        return None
    with db_cursor(commit=True) as cur:
        cur.execute("""SELECT s.token_hash,s.user_id,s.credentials_version,s.expires_at,s.revoked_at,u.credentials_version AS user_version,u.is_active
                       FROM login_sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=?""", hash_token(token))
        row = row_to_dict(cur, cur.fetchone())
        if not row or row["revoked_at"] is not None or row["expires_at"] < utcnow() or not row["is_active"] or row["credentials_version"] != row["user_version"]:
            if required: raise HTTPException(401, "Phiên đăng nhập không còn hợp lệ. Hãy đăng nhập lại.")
            return None
        cur.execute("UPDATE login_sessions SET last_seen_at=?, expires_at=? WHERE token_hash=?", utcnow(), utcnow()+timedelta(minutes=SESSION_MINUTES), hash_token(token))
        return public_user(cur, row["user_id"])


def require_role(user, *roles):
    if not set(user["roles"]).intersection(roles):
        raise HTTPException(403, "Bạn không có quyền thực hiện chức năng này. Hãy liên hệ quản trị viên nếu cần được cấp quyền.")


def menu_for(user):
    roles = set(user["roles"])
    items = [
        {"key":"home","label":"Tổng quan","path":"/"},
        {"key":"customers","label":"Khách hàng & cơ hội","path":"/customers"},
        {"key":"change-password","label":"Đổi mật khẩu","path":"/change-password"},
    ]
    if roles & {"ADMIN","DIRECTOR"}:
        items.append({"key":"users","label":"Quản lý người dùng","path":"/users"})
    if "ADMIN" in roles:
        items.extend([
            {"key":"roles","label":"Vai trò & nhóm","path":"/roles"},
            {"key":"lock","label":"Khóa & bàn giao","path":"/account-lock"},
            {"key":"outbox","label":"Email demo","path":"/outbox"},
        ])
    return items


class LoginIn(BaseModel):
    # Dùng str để chấp nhận các email demo nội bộ dạng @crm.local.
    email: str
    password: str

@app.get("/api/health")
def health(): return {"status":"ok","service":"crm-sprint1"}

@app.post("/api/auth/login")
def login(body: LoginIn, response: Response):
    email = body.email.lower()
    generic = "Email hoặc mật khẩu không đúng. Vui lòng kiểm tra lại thông tin đăng nhập."
    locked_message = "Tài khoản đã bị khóa tạm thời. Vui lòng đăng nhập lại sau 15 phút."
    login_failed = False
    account_locked = False
    token = None
    user = None

    # Không raise HTTPException bên trong db_cursor(commit=True), vì context manager
    # sẽ rollback transaction và làm mất failed_login_attempts/locked_until.
    # Thay vào đó ghi DB trước, để context manager commit, rồi mới trả lỗi.
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT id,password_hash,is_active,failed_login_attempts,locked_until,credentials_version FROM users WHERE email=?", email)
        row = row_to_dict(cur, cur.fetchone())
        now = utcnow()

        # Tài khoản đang bị khóa: không cho đăng nhập kể cả mật khẩu đúng.
        if row and row["locked_until"] and row["locked_until"] > now:
            login_failed = True
            account_locked = True

        else:
            # Hết thời gian khóa thì reset bộ đếm rồi cho phép thử lại.
            if row and row["locked_until"] and row["locked_until"] <= now:
                row["failed_login_attempts"] = 0
                row["locked_until"] = None
                cur.execute("UPDATE users SET failed_login_attempts=0, locked_until=NULL WHERE id=?", row["id"])

            if not row or not row["is_active"] or not verify_password(body.password, row["password_hash"]):
                login_failed = True
                # Chỉ lưu bộ đếm cho tài khoản tồn tại. Các lần 1-4 vẫn dùng thông báo chung.
                if row:
                    attempts = int(row["failed_login_attempts"] or 0) + 1
                    locked_until = now + timedelta(minutes=15) if attempts >= 5 else None
                    cur.execute(
                        "UPDATE users SET failed_login_attempts=?, locked_until=? WHERE id=?",
                        attempts, locked_until, row["id"]
                    )
                    # Ngay lần sai thứ 5, báo rõ tài khoản đã bị khóa 15 phút.
                    if locked_until is not None:
                        account_locked = True
            else:
                # Đăng nhập thành công thì xóa bộ đếm sai.
                cur.execute("UPDATE users SET failed_login_attempts=0, locked_until=NULL WHERE id=?", row["id"])
                token = create_session(cur, row["id"], row["credentials_version"])
                user = public_user(cur, row["id"])

    if login_failed:
        if account_locked:
            raise HTTPException(423, locked_message)
        raise HTTPException(401, generic)

    # Session cookie: không Max-Age -> đóng trình duyệt sẽ mất cookie.
    response.set_cookie(COOKIE_NAME, token, httponly=True, samesite="lax", secure=False, path="/")
    return {"message":"Đăng nhập thành công.","user":user,"menu":menu_for(user)}

@app.get("/api/auth/me")
def me(request: Request):
    user=current_user(request)
    return {"user":user,"menu":menu_for(user),"message":"Phiên hợp lệ và đã được gia hạn."}

@app.post("/api/auth/logout")
def logout(request: Request,response: Response):
    token=request.cookies.get(COOKIE_NAME)
    if token:
        with db_cursor(commit=True) as cur:
            cur.execute("UPDATE login_sessions SET revoked_at=? WHERE token_hash=?", utcnow(), hash_token(token))
    response.delete_cookie(COOKIE_NAME,path="/")
    return {"message":"Đã đăng xuất an toàn và thu hồi phiên trên máy chủ."}

class ForgotIn(BaseModel): email: str
@app.post("/api/auth/forgot-password")
def forgot_password(body: ForgotIn):
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT id FROM users WHERE email=?", body.email.lower())
        row=cur.fetchone()
        if row:
            token=new_token()
            cur.execute("UPDATE password_reset_tokens SET used_at=? WHERE user_id=? AND used_at IS NULL", utcnow(), row[0])
            cur.execute("INSERT INTO password_reset_tokens(user_id,token_hash,expires_at) VALUES(?,?,?)", row[0],hash_token(token),utcnow()+timedelta(minutes=RESET_MINUTES))
            link=f"{FRONTEND_ORIGIN}/reset-password?token={token}"
            cur.execute("INSERT INTO outbox_emails(recipient,subject,body) VALUES(?,?,?)", body.email,"Đặt lại mật khẩu CRM",f"Liên kết có hiệu lực 30 phút và chỉ dùng một lần: {link}")
    return {"message":"Nếu email tồn tại trong hệ thống, chúng tôi đã gửi liên kết đặt lại mật khẩu."}

class ResetIn(BaseModel): password: str; password_confirmation: str
@app.post("/api/auth/reset-password/{token}")
def reset_password(token: str, body: ResetIn):
    err=password_error(body.password)
    if err: raise HTTPException(400,err)
    if body.password!=body.password_confirmation: raise HTTPException(400,"Mật khẩu xác nhận không khớp. Hãy nhập lại hai ô giống nhau.")
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT id,user_id,expires_at,used_at FROM password_reset_tokens WHERE token_hash=?",hash_token(token))
        row=row_to_dict(cur,cur.fetchone())
        if not row or row["used_at"] is not None or row["expires_at"]<utcnow():
            raise HTTPException(400,"Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn. Hãy yêu cầu một liên kết mới.")
        cur.execute("UPDATE users SET password_hash=?,credentials_version=credentials_version+1,updated_at=? WHERE id=?",hash_password(body.password),utcnow(),row["user_id"])
        cur.execute("UPDATE password_reset_tokens SET used_at=? WHERE id=?",utcnow(),row["id"])
        cur.execute("UPDATE login_sessions SET revoked_at=? WHERE user_id=? AND revoked_at IS NULL",utcnow(),row["user_id"])
    return {"message":"Đặt lại mật khẩu thành công. Bạn có thể đăng nhập bằng mật khẩu mới."}

class ChangePasswordIn(BaseModel): current_password:str; new_password:str; new_password_confirmation:str
@app.post("/api/auth/change-password")
def change_password(body:ChangePasswordIn,request:Request):
    user=current_user(request)
    err=password_error(body.new_password)
    if err: raise HTTPException(400,err)
    if body.new_password!=body.new_password_confirmation: raise HTTPException(400,"Xác nhận mật khẩu mới không khớp. Hãy nhập lại.")
    token=request.cookies.get(COOKIE_NAME)
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT password_hash,credentials_version FROM users WHERE id=?",user["id"])
        row=row_to_dict(cur,cur.fetchone())
        if not verify_password(body.current_password,row["password_hash"]): raise HTTPException(400,"Mật khẩu hiện tại không đúng. Hãy kiểm tra lại.")
        if verify_password(body.new_password,row["password_hash"]): raise HTTPException(400,"Mật khẩu mới phải khác mật khẩu hiện tại. Hãy chọn mật khẩu khác.")
        new_ver=row["credentials_version"]+1
        cur.execute("UPDATE users SET password_hash=?,credentials_version=?,updated_at=? WHERE id=?",hash_password(body.new_password),new_ver,utcnow(),user["id"])
        cur.execute("UPDATE login_sessions SET revoked_at=? WHERE user_id=? AND token_hash<>? AND revoked_at IS NULL",utcnow(),user["id"],hash_token(token))
        cur.execute("UPDATE login_sessions SET credentials_version=? WHERE token_hash=?",new_ver,hash_token(token))
    return {"message":"Đổi mật khẩu thành công. Các phiên đăng nhập khác đã được thu hồi."}


def data_scope_clause(user, alias="x"):
    if user["data_scope"]=="all" or "ADMIN" in user["roles"]:
        return "1=1", []
    if user["data_scope"]=="group":
        return f"{alias}.business_group_id=?", [user["business_group_id"]]
    return f"{alias}.owner_id=?", [user["id"]]

@app.get("/api/customers")
def customers(request:Request,q:str=""):
    user=current_user(request); clause,args=data_scope_clause(user,"c")
    sql=f"""SELECT c.id,c.name,c.phone,c.email,c.owner_id,c.business_group_id,u.full_name owner_name,g.name group_name
             FROM customers c JOIN users u ON u.id=c.owner_id LEFT JOIN business_groups g ON g.id=c.business_group_id
             WHERE {clause} AND (c.name LIKE ? OR c.email LIKE ? OR c.phone LIKE ?) ORDER BY c.id DESC"""
    search=f"%{q}%"; args += [search,search,search]
    with db_cursor() as cur:
        cur.execute(sql,*args); return {"items":rows_to_dicts(cur,cur.fetchall()),"scope":user["data_scope"]}

@app.get("/api/opportunities")
def opportunities(request:Request,q:str=""):
    user=current_user(request); clause,args=data_scope_clause(user,"o")
    sql=f"""SELECT o.id,o.title,o.value,o.stage,o.owner_id,o.business_group_id,u.full_name owner_name,g.name group_name
             FROM opportunities o JOIN users u ON u.id=o.owner_id LEFT JOIN business_groups g ON g.id=o.business_group_id
             WHERE {clause} AND (o.title LIKE ? OR o.stage LIKE ?) ORDER BY o.id DESC"""
    search=f"%{q}%"; args += [search,search]
    with db_cursor() as cur:
        cur.execute(sql,*args); return {"items":rows_to_dicts(cur,cur.fetchall()),"scope":user["data_scope"]}

@app.get("/api/activities")
def activities(request:Request,q:str=""):
    user=current_user(request); clause,args=data_scope_clause(user,"a")
    search=f"%{q}%"; args += [search,search]
    with db_cursor() as cur:
        cur.execute(f"""SELECT a.id,a.subject,a.activity_type,a.owner_id,u.full_name owner_name,g.name group_name
                        FROM activities a JOIN users u ON u.id=a.owner_id LEFT JOIN business_groups g ON g.id=a.business_group_id
                        WHERE {clause} AND (a.subject LIKE ? OR a.activity_type LIKE ?) ORDER BY a.id DESC""",*args)
        return {"items":rows_to_dicts(cur,cur.fetchall()),"scope":user["data_scope"]}

@app.get("/api/quotations")
def quotations(request:Request,q:str=""):
    user=current_user(request); clause,args=data_scope_clause(user,"q")
    search=f"%{q}%"; args += [search,search]
    with db_cursor() as cur:
        cur.execute(f"""SELECT q.id,q.quote_no,q.total_amount,q.status,q.owner_id,u.full_name owner_name,g.name group_name
                        FROM quotations q JOIN users u ON u.id=q.owner_id LEFT JOIN business_groups g ON g.id=q.business_group_id
                        WHERE {clause} AND (q.quote_no LIKE ? OR q.status LIKE ?) ORDER BY q.id DESC""",*args)
        return {"items":rows_to_dicts(cur,cur.fetchall()),"scope":user["data_scope"]}



def ensure_record_in_scope(cur, user, table: str, record_id: int):
    allowed = {
        "customers": "c",
        "opportunities": "o",
        "activities": "a",
        "quotations": "q",
    }
    alias = allowed[table]
    cur.execute(f"SELECT {alias}.id FROM {table} {alias} WHERE {alias}.id=?", record_id)
    if not cur.fetchone():
        raise HTTPException(404, "Không tìm thấy bản ghi được yêu cầu.")
    clause, args = data_scope_clause(user, alias)
    cur.execute(f"SELECT {alias}.id FROM {table} {alias} WHERE {alias}.id=? AND {clause}", record_id, *args)
    if not cur.fetchone():
        raise HTTPException(403, "Bạn không có quyền truy cập bản ghi này vì nằm ngoài phạm vi dữ liệu được cấp.")

@app.get("/api/customers/{record_id}")
def customer_detail(record_id:int, request:Request):
    user=current_user(request)
    with db_cursor() as cur:
        ensure_record_in_scope(cur,user,"customers",record_id)
        cur.execute("""SELECT c.id,c.name,c.phone,c.email,c.owner_id,c.business_group_id,u.full_name owner_name,g.name group_name
                       FROM customers c JOIN users u ON u.id=c.owner_id LEFT JOIN business_groups g ON g.id=c.business_group_id WHERE c.id=?""",record_id)
        return {"item":row_to_dict(cur,cur.fetchone()),"scope":user["data_scope"]}

@app.get("/api/opportunities/{record_id}")
def opportunity_detail(record_id:int, request:Request):
    user=current_user(request)
    with db_cursor() as cur:
        ensure_record_in_scope(cur,user,"opportunities",record_id)
        cur.execute("""SELECT o.id,o.title,o.value,o.stage,o.owner_id,o.business_group_id,u.full_name owner_name,g.name group_name
                       FROM opportunities o JOIN users u ON u.id=o.owner_id LEFT JOIN business_groups g ON g.id=o.business_group_id WHERE o.id=?""",record_id)
        return {"item":row_to_dict(cur,cur.fetchone()),"scope":user["data_scope"]}

@app.get("/api/activities/{record_id}")
def activity_detail(record_id:int, request:Request):
    user=current_user(request)
    with db_cursor() as cur:
        ensure_record_in_scope(cur,user,"activities",record_id)
        cur.execute("""SELECT a.id,a.subject,a.activity_type,a.owner_id,a.business_group_id,u.full_name owner_name,g.name group_name
                       FROM activities a JOIN users u ON u.id=a.owner_id LEFT JOIN business_groups g ON g.id=a.business_group_id WHERE a.id=?""",record_id)
        return {"item":row_to_dict(cur,cur.fetchone()),"scope":user["data_scope"]}

@app.get("/api/quotations/{record_id}")
def quotation_detail(record_id:int, request:Request):
    user=current_user(request)
    with db_cursor() as cur:
        ensure_record_in_scope(cur,user,"quotations",record_id)
        cur.execute("""SELECT q.id,q.quote_no,q.total_amount,q.status,q.owner_id,q.business_group_id,u.full_name owner_name,g.name group_name
                       FROM quotations q JOIN users u ON u.id=q.owner_id LEFT JOIN business_groups g ON g.id=q.business_group_id WHERE q.id=?""",record_id)
        return {"item":row_to_dict(cur,cur.fetchone()),"scope":user["data_scope"]}

@app.get("/api/data/export")
def export_scoped_data(request:Request):
    user=current_user(request)
    wb=Workbook(); wb.remove(wb.active)
    specs=[
      ("KhachHang","c","customers c JOIN users u ON u.id=c.owner_id LEFT JOIN business_groups g ON g.id=c.business_group_id",["ID","Tên","Điện thoại","Email","Chủ sở hữu","Nhóm"],"SELECT c.id,c.name,c.phone,c.email,u.full_name,g.name"),
      ("CoHoi","o","opportunities o JOIN users u ON u.id=o.owner_id LEFT JOIN business_groups g ON g.id=o.business_group_id",["ID","Tiêu đề","Giá trị","Giai đoạn","Chủ sở hữu","Nhóm"],"SELECT o.id,o.title,o.value,o.stage,u.full_name,g.name"),
      ("HoatDong","a","activities a JOIN users u ON u.id=a.owner_id LEFT JOIN business_groups g ON g.id=a.business_group_id",["ID","Nội dung","Loại","Chủ sở hữu","Nhóm"],"SELECT a.id,a.subject,a.activity_type,u.full_name,g.name"),
      ("BaoGia","q","quotations q JOIN users u ON u.id=q.owner_id LEFT JOIN business_groups g ON g.id=q.business_group_id",["ID","Số báo giá","Tổng tiền","Trạng thái","Chủ sở hữu","Nhóm"],"SELECT q.id,q.quote_no,q.total_amount,q.status,u.full_name,g.name"),
    ]
    with db_cursor() as cur:
        for title,alias,from_sql,headers,select_sql in specs:
            clause,args=data_scope_clause(user,alias)
            cur.execute(f"{select_sql} FROM {from_sql} WHERE {clause} ORDER BY {alias}.id",*args)
            rows=cur.fetchall(); ws=wb.create_sheet(title); ws.append(headers)
            for row in rows: ws.append(list(row))
    data=io.BytesIO(); wb.save(data); data.seek(0)
    return StreamingResponse(data,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":"attachment; filename=du-lieu-theo-pham-vi.xlsx"})

@app.get("/api/meta")
def meta(request:Request):
    user=current_user(request)
    with db_cursor() as cur:
        cur.execute("SELECT id,code,name FROM roles ORDER BY id"); roles=rows_to_dicts(cur,cur.fetchall())
        cur.execute("SELECT id,name FROM business_groups ORDER BY id"); groups=rows_to_dicts(cur,cur.fetchall())
    return {"roles":roles,"groups":groups,"current_user":user}

@app.get("/api/users")
def list_users(request:Request,q:str="",group:int|None=None,role:str="",status:str="",page:int=1,per_page:int=20):
    user=current_user(request); require_role(user,"ADMIN","DIRECTOR")
    page=max(1,page); per_page=max(1,min(100,per_page)); offset=(page-1)*per_page
    wh=["(u.full_name LIKE ? OR u.email LIKE ? OR g.name LIKE ?)"]; s=f"%{q}%"; params=[s,s,s]
    if group: wh.append("u.business_group_id=?"); params.append(group)
    if status: wh.append("u.status=?"); params.append(status)
    if role: wh.append("EXISTS(SELECT 1 FROM user_roles ur2 JOIN roles r2 ON r2.id=ur2.role_id WHERE ur2.user_id=u.id AND r2.code=?)"); params.append(role)
    where=" AND ".join(wh)
    with db_cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM users u LEFT JOIN business_groups g ON g.id=u.business_group_id WHERE {where}",*params); total=cur.fetchone()[0]
        cur.execute(f"""SELECT u.id,u.full_name,u.email,u.status,u.data_scope,u.business_group_id,u.is_active,g.name group_name
                        FROM users u LEFT JOIN business_groups g ON g.id=u.business_group_id WHERE {where}
                        ORDER BY u.id OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",*(params+[offset,per_page]))
        items=rows_to_dicts(cur,cur.fetchall())
        for item in items:item["roles"]=get_roles(cur,item["id"])
    return {"items":items,"page":page,"per_page":per_page,"total":total,"pages":max(1,(total+per_page-1)//per_page)}

class UserCreateIn(BaseModel):
    full_name:str; email:str; business_group_id:Optional[int]=None; role_ids:list[int]; data_scope:str="self"

def _roles_and_scope(cur, role_ids:list[int], business_group_id:Optional[int]):
    unique_ids=list(dict.fromkeys(role_ids))
    if not unique_ids:
        raise HTTPException(400,"Phải chọn ít nhất một vai trò cho tài khoản.")
    placeholders=",".join("?" for _ in unique_ids)
    cur.execute(f"SELECT id,code FROM roles WHERE id IN ({placeholders})",*unique_ids)
    selected=rows_to_dicts(cur,cur.fetchall())
    if len(selected)!=len(unique_ids):
        raise HTTPException(400,"Danh sách vai trò không hợp lệ. Hãy tải lại dữ liệu.")
    codes={r["code"] for r in selected}
    if "TEAM_LEADER" in codes and not business_group_id:
        raise HTTPException(400,"Trưởng nhóm phải được gán vào một nhóm kinh doanh cụ thể.")
    if business_group_id:
        cur.execute("SELECT 1 FROM business_groups WHERE id=?",business_group_id)
        if not cur.fetchone():
            raise HTTPException(400,"Nhóm kinh doanh không hợp lệ. Hãy chọn lại.")
    if codes & {"ADMIN","DIRECTOR"}:
        scope="all"
    elif "TEAM_LEADER" in codes:
        scope="group"
    else:
        scope="self"
    return unique_ids,codes,scope

@app.post("/api/users")
def create_user_api(body:UserCreateIn,request:Request):
    actor=current_user(request); require_role(actor,"ADMIN")
    temp="Temp@"+new_token()[:8]
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT 1 FROM users WHERE email=?",body.email.lower())
        if cur.fetchone(): raise HTTPException(409,"Email đã tồn tại. Hãy dùng email công ty khác.")
        role_ids,codes,scope=_roles_and_scope(cur,body.role_ids,body.business_group_id)
        cur.execute("INSERT INTO users(full_name,email,password_hash,status,data_scope,business_group_id,is_active) OUTPUT INSERTED.id VALUES(?,?,?,N'pending',?,?,0)",body.full_name,body.email.lower(),hash_password(temp),scope,body.business_group_id)
        uid=cur.fetchone()[0]
        for rid in role_ids:cur.execute("INSERT INTO user_roles(user_id,role_id) VALUES(?,?)",uid,rid)
        token=new_token(); cur.execute("INSERT INTO account_activation_tokens(user_id,token_hash,expires_at) VALUES(?,?,?)",uid,hash_token(token),utcnow()+timedelta(hours=24))
        link=f"{FRONTEND_ORIGIN}/activate?token={token}"
        cur.execute("INSERT INTO outbox_emails(recipient,subject,body) VALUES(?,?,?)",body.email,"Kích hoạt tài khoản CRM",f"Mật khẩu tạm: {temp}\nKích hoạt: {link}")
    return {"message":"Tạo tài khoản thành công. Email kích hoạt kèm mật khẩu tạm đã được tạo trong Email demo.","user_id":uid,"data_scope":scope}

class UserUpdateIn(BaseModel):
    full_name:str; email:str; business_group_id:Optional[int]=None; data_scope:str="self"; status:str="active"
@app.put("/api/users/{user_id}")
def update_user_api(user_id:int,body:UserUpdateIn,request:Request):
    actor=current_user(request);require_role(actor,"ADMIN")
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT id FROM users WHERE email=? AND id<>?",body.email.lower(),user_id)
        if cur.fetchone():raise HTTPException(409,"Email đã tồn tại. Hãy dùng email khác.")
        if body.status not in {"active","pending","locked"}:raise HTTPException(400,"Trạng thái tài khoản không hợp lệ.")
        codes=set(get_roles(cur,user_id))
        if "TEAM_LEADER" in codes and not body.business_group_id:
            raise HTTPException(400,"Trưởng nhóm phải được gán vào một nhóm kinh doanh cụ thể.")
        if body.business_group_id:
            cur.execute("SELECT 1 FROM business_groups WHERE id=?",body.business_group_id)
            if not cur.fetchone():raise HTTPException(400,"Nhóm kinh doanh không hợp lệ. Hãy chọn lại.")
        scope="all" if codes & {"ADMIN","DIRECTOR"} else ("group" if "TEAM_LEADER" in codes else "self")
        is_active=1 if body.status=="active" else 0
        cur.execute("UPDATE users SET full_name=?,email=?,business_group_id=?,data_scope=?,status=?,is_active=?,updated_at=? WHERE id=?",body.full_name,body.email.lower(),body.business_group_id,scope,body.status,is_active,utcnow(),user_id)
        if cur.rowcount==0:raise HTTPException(404,"Không tìm thấy tài khoản. Hãy làm mới danh sách.")
        if not is_active:
            cur.execute("UPDATE login_sessions SET revoked_at=? WHERE user_id=? AND revoked_at IS NULL",utcnow(),user_id)
    return {"message":"Đã cập nhật tài khoản và đồng bộ trạng thái đăng nhập."}

@app.post("/api/auth/activate/{token}")
def activate(token:str):
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT id,user_id,expires_at,used_at FROM account_activation_tokens WHERE token_hash=?",hash_token(token)); row=row_to_dict(cur,cur.fetchone())
        if not row or row["used_at"] or row["expires_at"]<utcnow():raise HTTPException(400,"Liên kết kích hoạt không hợp lệ hoặc hết hạn. Hãy liên hệ quản trị viên.")
        cur.execute("UPDATE users SET status=N'active',is_active=1 WHERE id=?",row["user_id"]);cur.execute("UPDATE account_activation_tokens SET used_at=? WHERE id=?",utcnow(),row["id"])
    return {"message":"Kích hoạt tài khoản thành công."}

class RoleAssignmentIn(BaseModel): role_ids:list[int]; business_group_id:Optional[int]=None
@app.put("/api/users/{user_id}/roles")
def assign_roles(user_id:int,body:RoleAssignmentIn,request:Request):
    actor=current_user(request);require_role(actor,"ADMIN")
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT id FROM users WHERE id=?",user_id)
        if not cur.fetchone():raise HTTPException(404,"Không tìm thấy người dùng cần phân quyền.")
        role_ids,codes,scope=_roles_and_scope(cur,body.role_ids,body.business_group_id)
        if user_id==actor["id"] and "ADMIN" in actor["roles"] and "ADMIN" not in codes:
            raise HTTPException(403,"Bạn không thể tự thu hồi vai trò Quản trị của chính mình. Hãy nhờ một quản trị viên khác thực hiện.")
        cur.execute("DELETE FROM user_roles WHERE user_id=?",user_id)
        for rid in role_ids:cur.execute("INSERT INTO user_roles(user_id,role_id) VALUES(?,?)",user_id,rid)
        cur.execute("UPDATE users SET business_group_id=?,data_scope=?,updated_at=? WHERE id=?",body.business_group_id,scope,utcnow(),user_id)
    return {"message":"Đã cập nhật nhiều vai trò, nhóm kinh doanh và phạm vi dữ liệu tương ứng.","data_scope":scope}

class LockIn(BaseModel): receiver_user_id:int
@app.post("/api/users/{user_id}/lock-and-handover")
def lock_and_handover(user_id:int,body:LockIn,request:Request):
    actor=current_user(request);require_role(actor,"ADMIN")
    if user_id==body.receiver_user_id:raise HTTPException(400,"Người nhận bàn giao phải khác người bị khóa. Hãy chọn nhân viên khác.")
    if user_id==actor["id"]:raise HTTPException(400,"Bạn không thể tự khóa tài khoản đang dùng. Hãy nhờ quản trị viên khác thực hiện.")
    conn=connect();cur=conn.cursor()
    try:
        cur.execute("SELECT id,is_active FROM users WHERE id=?",user_id);target=cur.fetchone()
        cur.execute("SELECT id,is_active FROM users WHERE id=?",body.receiver_user_id);receiver=cur.fetchone()
        if not target:raise HTTPException(404,"Không tìm thấy tài khoản cần khóa.")
        if not target[1]:raise HTTPException(400,"Tài khoản này đã bị khóa trước đó.")
        if not receiver or not receiver[1]:raise HTTPException(400,"Người nhận bàn giao không hợp lệ hoặc đang bị khóa.")
        cur.execute("SELECT COUNT(*) FROM customers WHERE owner_id=?",user_id);cc=cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM opportunities WHERE owner_id=?",user_id);oc=cur.fetchone()[0]
        cur.execute("UPDATE customers SET owner_id=?,business_group_id=(SELECT business_group_id FROM users WHERE id=?) WHERE owner_id=?",body.receiver_user_id,body.receiver_user_id,user_id)
        cur.execute("UPDATE opportunities SET owner_id=?,business_group_id=(SELECT business_group_id FROM users WHERE id=?) WHERE owner_id=?",body.receiver_user_id,body.receiver_user_id,user_id)
        cur.execute("UPDATE users SET is_active=0,status=N'locked',updated_at=? WHERE id=?",utcnow(),user_id)
        cur.execute("UPDATE login_sessions SET revoked_at=? WHERE user_id=? AND revoked_at IS NULL",utcnow(),user_id)
        cur.execute("INSERT INTO handover_logs(from_user_id,to_user_id,admin_id,customer_count,opportunity_count) VALUES(?,?,?,?,?)",user_id,body.receiver_user_id,actor["id"],cc,oc)
        conn.commit()
    except HTTPException:
        conn.rollback();raise
    except Exception:
        conn.rollback();raise
    finally:conn.close()
    return {"message":"Đã bàn giao toàn bộ khách hàng/cơ hội, ghi nhật ký và khóa tài khoản.","customer_count":cc,"opportunity_count":oc}

@app.get("/api/handover-logs")
def handover_logs(request:Request):
    actor=current_user(request);require_role(actor,"ADMIN")
    with db_cursor() as cur:
        cur.execute("""SELECT TOP 100 h.id,fu.full_name from_user,tu.full_name to_user,au.full_name admin_user,h.customer_count,h.opportunity_count,h.created_at
                       FROM handover_logs h JOIN users fu ON fu.id=h.from_user_id JOIN users tu ON tu.id=h.to_user_id JOIN users au ON au.id=h.admin_id ORDER BY h.id DESC""")
        return {"items":rows_to_dicts(cur,cur.fetchall())}

@app.get("/api/outbox")
def outbox(request:Request):
    actor=current_user(request);require_role(actor,"ADMIN")
    with db_cursor() as cur:
        cur.execute("SELECT TOP 100 id,recipient,subject,body,created_at FROM outbox_emails ORDER BY id DESC")
        return {"items":rows_to_dicts(cur,cur.fetchall())}
