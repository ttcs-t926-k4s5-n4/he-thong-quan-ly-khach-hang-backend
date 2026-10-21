import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .main import app
from .database import Base, get_db
from .models import Lead, LeadHistory

# Sử dụng SQLite in-memory cho test
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_lead_success():
    response = client.post("/leads/", json={"email": "test@example.com", "full_name": "Test User"})
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

def test_detect_duplicate_lead():
    # Tạo lead đầu tiên
    client.post("/leads/", json={"email": "dup@example.com", "full_name": "Original"})
    
    # Tạo lead trùng email
    response = client.post("/leads/", json={"email": "dup@example.com", "full_name": "Duplicate"})
    assert response.status_code == 409
    assert "Phát hiện lead trùng lặp" in response.json()["detail"]["message"]

def test_merge_leads_and_preserve_history():
    # 1. Tạo 2 lead
    l1 = client.post("/leads/", json={"email": "l1@test.com", "full_name": "Lead 1"}).json()
    l2 = client.post("/leads/", json={"email": "l2@test.com", "full_name": "Lead 2"}).json()
    
    # 2. Thêm lịch sử cho cả 2
    client.post(f"/leads/{l1['id']}/history", json={"action": "Call", "details": "Called L1"})
    client.post(f"/leads/{l2['id']}/history", json={"action": "Email", "details": "Emailed L2"})
    
    # 3. Merge L1 vào L2
    merge_res = client.post("/leads/merge", json={
        "source_lead_id": l1['id'], 
        "target_lead_id": l2['id'], 
        "merged_by": "Admin"
    })
    assert merge_res.status_code == 200
    
    # 4. Kiểm tra L2 giờ đây có cả 2 lịch sử
    history_res = client.get(f"/leads/{l2['id']}/history")
    assert len(history_res.json()) == 2
    
    # 5. Kiểm tra L1 đã bị đánh dấu merge
    lead1_res = client.get(f"/leads/", params={"limit": 100}) # Lấy list để check
    # Tìm l1 trong list
    l1_status = next(item for item in lead1_res.json() if item['id'] == l1['id'])
    assert l1_status['is_merged'] is True
    assert l1_status['merged_into_id'] == l2['id']
