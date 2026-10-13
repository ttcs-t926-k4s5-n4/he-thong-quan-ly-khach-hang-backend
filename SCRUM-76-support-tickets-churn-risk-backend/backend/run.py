import os
import sys
from pathlib import Path

# Tß╗▒ ─æß╗Öng k├¡ch hoß║ít m├┤i tr╞░ß╗¥ng ß║úo (.venv) nß║┐u ng╞░ß╗¥i d├╣ng g├╡ `python run.py` bß║▒ng Python hß╗ç thß╗æng
backend_dir = Path(__file__).resolve().parent
venv_python = backend_dir / ".venv" / "Scripts" / "python.exe"

if venv_python.exists() and sys.executable.lower() != str(venv_python).lower():
    try:
        import pyodbc  # noqa: F401
    except ImportError:
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)

from app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    print(f"\n≡ƒÜÇ CRM Backend ─æang chß║íy tß║íi http://{host}:{port}")
    print(f"≡ƒôè CSDL SQL Server: {os.environ.get('SQL_SERVER_DATABASE', 'crm_db')}")
    print("=" * 60 + "\n")
    app.run(
        host=host,
        port=port,
        debug=app.config.get("DEBUG", True),
    )

