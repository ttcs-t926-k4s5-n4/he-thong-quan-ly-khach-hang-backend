from app.db import init_db, get_connection
from app.security import hash_password

def seed():
    init_db()
    conn = get_connection()

    # Seed Admin User
    conn.execute(
        "INSERT OR IGNORE INTO users(email, password_hash, role) VALUES(?,?,?)",
        ("admin@company.local", hash_password("Admin@123"), "admin")
    )

    # Seed Normal User
    conn.execute(
        "INSERT OR IGNORE INTO users(email, password_hash, role) VALUES(?,?,?)",
        ("user@company.local", hash_password("User@123"), "user")
    )

    conn.commit()
    conn.close()
    print("Database S1-01 seeded successfully!")

if __name__ == "__main__":
    seed()
