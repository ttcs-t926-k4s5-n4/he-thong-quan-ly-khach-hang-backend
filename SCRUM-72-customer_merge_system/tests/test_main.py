from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import Customer, Contact, Opportunity

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_merge.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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

def test_duplicate_detection():
    # Create two customers with same tax ID
    client.post("/customers/", json={"name": "Company A", "tax_id": "111", "website": "a.com"})
    client.post("/customers/", json={"name": "Company A Ltd", "tax_id": "111", "website": "a.com"})

    resp = client.get("/customers/1/duplicates")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert "Trùng mã số thuế" in resp.json()[0]["reasons"][0]

def test_merge_security():
    # Create two customers
    client.post("/customers/", json={"name": "C1", "tax_id": "1", "website": "1.com"})
    client.post("/customers/", json={"name": "C2", "tax_id": "2", "website": "2.com"})

    # Merge without role
    resp = client.post("/customers/merge", json={"source_customer_id": 1, "target_customer_id": 2})
    assert resp.status_code == 403

    # Merge with TeamLead role
    resp = client.post("/customers/merge", json={"source_customer_id": 1, "target_customer_id": 2},
                       headers={"X-Role": "TeamLead"})
    assert resp.status_code == 200

def test_merge_data_integrity():
    # Create Customers
    c1_resp = client.post("/customers/", json={"name": "C1", "tax_id": "T1", "website": "w1.com"})
    c2_resp = client.post("/customers/", json={"name": "C2", "tax_id": "T2", "website": "w2.com"})
    c1_id = c1_resp.json()["id"]
    c2_id = c2_resp.json()["id"]

    # Add a contact to C1
    client.post("/test/contacts/", json={"name": "John Doe", "customer_id": c1_id})

    # Merge C1 into C2
    client.post("/customers/merge", json={"source_customer_id": c1_id, "target_customer_id": c2_id},
                headers={"X-Role": "TeamLead"})

    # Verify C1 is gone, C2 has the contact
    resp_c1 = client.get(f"/customers/{c1_id}")
    assert resp_c1.status_code == 404

    resp_c2 = client.get(f"/customers/{c2_id}")
    assert resp_c2.status_code == 200
    # In the real app, CustomerDetail schema would show the contacts
    # Let's check if the contact now belongs to C2 in the DB
    db = TestingSessionLocal()
    contact = db.query(Contact).filter(Contact.name == "John Doe").first()
    assert contact.customer_id == c2_id
    db.close()
