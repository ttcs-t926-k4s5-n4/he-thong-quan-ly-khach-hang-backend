import hashlib,secrets,time
from flask import current_app
from werkzeug.security import check_password_hash
from app.db import get_db

def token_hash(raw): return hashlib.sha256(raw.encode()).hexdigest()

def authenticate(email,password):
    db=get_db();cur=db.cursor()
    cur.execute("SELECT id,full_name,email,password_hash,role FROM dbo.users WHERE LOWER(email)=LOWER(?)",(email.strip().lower(),))
    row=cur.fetchone()
    if row is None or not check_password_hash(str(row[3]),password): return None
    return {"id":int(row[0]),"full_name":str(row[1]),"email":str(row[2]),"role":str(row[4])}

def create_session(user_id):
    db=get_db();cur=db.cursor();raw=secrets.token_urlsafe(32);now=int(time.time());exp=now+int(current_app.config["SESSION_TTL_SECONDS"])
    cur.execute("""
      INSERT INTO dbo.login_sessions(token_hash,user_id,created_at,last_seen_at,expires_at,revoked_at)
      VALUES(?,?,?,?,?,NULL)
    """,(token_hash(raw),user_id,now,now,exp));db.commit();return raw

def validate_and_extend(raw):
    db=get_db();cur=db.cursor();now=int(time.time());hashed=token_hash(raw)
    cur.execute("""
      SELECT s.user_id,u.full_name,u.email,u.role
      FROM dbo.login_sessions s JOIN dbo.users u ON u.id=s.user_id
      WHERE s.token_hash=? AND s.revoked_at IS NULL AND s.expires_at>?
    """,(hashed,now))
    row=cur.fetchone()
    if row is None:return None
    exp=now+int(current_app.config["SESSION_TTL_SECONDS"])
    cur.execute("""
      UPDATE dbo.login_sessions SET last_seen_at=?,expires_at=?
      WHERE token_hash=? AND revoked_at IS NULL AND expires_at>?
    """,(now,exp,hashed,now))
    if cur.rowcount!=1:db.rollback();return None
    db.commit()
    return {"id":int(row[0]),"full_name":str(row[1]),"email":str(row[2]),"role":str(row[3])}

def revoke_session(raw):
    db=get_db();cur=db.cursor()
    cur.execute("UPDATE dbo.login_sessions SET revoked_at=? WHERE token_hash=? AND revoked_at IS NULL",(int(time.time()),token_hash(raw)))
    db.commit()
