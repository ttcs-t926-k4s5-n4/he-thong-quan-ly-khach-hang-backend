import sys,time
from pathlib import Path
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
import pyodbc
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));load_dotenv(ROOT/".env")
from app.db import build_connection_string
db=pyodbc.connect(build_connection_string(),autocommit=False,timeout=5);cur=db.cursor();email="employee@company.vn";now=int(time.time())
try:
    cur.execute("SELECT id FROM dbo.users WHERE LOWER(email)=LOWER(?)",(email,))
    if cur.fetchone() is None:
        cur.execute("INSERT INTO dbo.users(full_name,email,password_hash,role,created_at,updated_at) VALUES(?,?,?,?,?,?)",
          ("Nhân viên kinh doanh",email,generate_password_hash("Employee123",method="scrypt:32768:8:1"),"employee",now,now))
        db.commit()
    print("Tài khoản demo: employee@company.vn / Employee123")
finally:db.close()
