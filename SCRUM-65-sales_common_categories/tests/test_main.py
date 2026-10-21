from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import Category, CategoryValue, Lead

# Setup Test Database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def setup_module(module):
    Base.metadata.create_all(bind=engine)

def teardown_module(module):
    Base.metadata.drop_all(bind=engine)

def test_create_and_delete_category_value():
    # 1. Create a category
    cat_resp = client.post("/categories/", json={"name": "Industry", "description": "Test Cat"})
    category_id = cat_resp.json()["id"]

    # 2. Create a value
    val_resp = client.post("/categories/values/", json={"category_id": category_id, "value": "Tech", "display_order": 1})
    value_id = val_resp.json()["id"]

    # 3. Try to delete - should work (no references)
    del_resp = client.delete(f"/categories/values/{value_id}")
    assert del_resp.status_code == 204

def test_block_delete_if_referenced():
    # 1. Setup: Category and Value
    db = TestingSessionLocal()
    cat = Category(name="Industry Test")
    db.add(cat)
    db.commit()

    val = CategoryValue(category_id=cat.id, value="Fintech", display_order=1)
    db.add(val)
    db.commit()

    # 2. Create a Lead that references this value
    lead = Lead(name="Test Lead", industry_value_id=val.id)
    db.add(lead)
    db.commit()
    db.close()

    # 3. Attempt to delete the value via API
    del_resp = client.delete(f"/categories/values/{val.id}")

    # MUST BE 400 BAD REQUEST as per Jira requirement
    assert del_resp.status_code == 400
    assert "being referenced" in del_resp.json()["detail"]
