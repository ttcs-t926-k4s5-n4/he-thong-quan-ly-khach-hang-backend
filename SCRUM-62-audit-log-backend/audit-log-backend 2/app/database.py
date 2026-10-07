"""
Database configuration - Cấu hình kết nối cơ sở dữ liệu
Sử dụng SQLite để đơn giản, có thể chuyển sang PostgreSQL khi triển khai production.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database - file sẽ được tạo tự động trong thư mục project
SQLALCHEMY_DATABASE_URL = "sqlite:///./audit_log.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Cần thiết cho SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency injection: Tạo và đóng database session cho mỗi request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
