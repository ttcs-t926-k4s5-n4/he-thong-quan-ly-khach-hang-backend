from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import Product, QuoteItem

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_catalog.db"
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

def test_cost_price_security():
    # Create product
    client.post("/products/", json={
        "code": "T1", "name": "Test", "product_type": "One-time",
        "unit": "Unit", "list_price": 100, "floor_price": 80, "cost_price": 50
    })

    # Attempt to access admin endpoint without role
    resp = client.get("/products/1/admin")
    assert resp.status_code == 403

    # Access with role
    resp = client.get("/products/1/admin", headers={"X-Role": "SalesDirector"})
    assert resp.status_code == 200
    assert resp.json()["cost_price"] == 50

def test_block_delete_if_referenced():
    db = TestingSessionLocal()
    p = Product(code="T2", name="Test 2", product_type="One-time", unit="Unit",
               list_price=100, floor_price=80, cost_price=50)
    db.add(p)
    db.commit()

    # Reference in a quote
    db.add(QuoteItem(quote_id=201, product_id=p.id, quantity=1, applied_price=90))
    db.commit()
    db.close()

    # Attempt delete
    resp = client.delete(f"/products/{p.id}")
    assert resp.status_code == 204 # Returns 204 but logic marks as inactive

    # Verify it is now inactive instead of gone
    db = TestingSessionLocal()
    prod = db.query(Product).filter(Product.id == p.id).first()
    assert prod.is_active is False
    db.close()
