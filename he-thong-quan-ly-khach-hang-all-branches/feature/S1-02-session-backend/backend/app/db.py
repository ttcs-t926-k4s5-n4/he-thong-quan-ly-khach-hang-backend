import os,pyodbc
from flask import g
def _bool(name,default=False):
    value=os.getenv(name);return default if value is None else value.lower() in {"1","true","yes","on"}
def build_connection_string():
    parts=[
      f"DRIVER={{{os.getenv('SQL_SERVER_DRIVER','ODBC Driver 18 for SQL Server')}}}",
      f"SERVER={os.getenv('SQL_SERVER_HOST','localhost')},{os.getenv('SQL_SERVER_PORT','1433')}",
      f"DATABASE={os.getenv('SQL_SERVER_DATABASE','crm_db')}",
      f"Encrypt={os.getenv('SQL_SERVER_ENCRYPT','yes')}",
      f"TrustServerCertificate={os.getenv('SQL_SERVER_TRUST_CERTIFICATE','yes')}",
    ]
    if _bool("SQL_SERVER_TRUSTED_CONNECTION"):parts.append("Trusted_Connection=yes")
    else:parts += [f"UID={os.getenv('SQL_SERVER_USER','sa')}",f"PWD={os.getenv('SQL_SERVER_PASSWORD','')}"]
    return ";".join(parts)+";"
def get_db():
    if "db" not in g:g.db=pyodbc.connect(build_connection_string(),autocommit=False,timeout=5)
    return g.db
def close_db(_error=None):
    db=g.pop("db",None)
    if db is not None:db.close()
