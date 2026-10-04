import sys,time
from pathlib import Path
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
import pyodbc
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT)); load_dotenv(ROOT/".env")
from app.db import build_connection_string

USERS=[
 ("Quản trị viên","admin@company.vn","Admin123","admin"),
 ("Giám đốc kinh doanh","manager@company.vn","Manager123","manager"),
 ("Nhân viên kinh doanh","employee@company.vn","Employee123","employee"),
]
db=pyodbc.connect(build_connection_string(),autocommit=False,timeout=5); cur=db.cursor(); now=int(time.time())
try:
    for full_name,email,password,role in USERS:
        cur.execute("SELECT id FROM dbo.users WHERE LOWER(email)=LOWER(?)",(email,))
        if cur.fetchone() is None:
            cur.execute("""
                INSERT INTO dbo.users(full_name,email,password_hash,role,failed_login_attempts,locked_until,created_at,updated_at)
                VALUES(?,?,?,?,0,NULL,?,?)
            """,(full_name,email,generate_password_hash(password,method="scrypt:32768:8:1"),role,now,now))
    db.commit()
    print("Đã tạo tài khoản demo S1-01.")
finally:
    db.close()
