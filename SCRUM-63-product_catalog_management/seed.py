from app.database import SessionLocal
from app.models import Product, QuoteItem

def seed_data():
    db = SessionLocal()
    try:
        products = [
            {
                "code": "PROD001", "name": "Phần mềm Kế toán v1", "product_type": "One-time",
                "unit": "Bộ", "list_price": 10000000, "floor_price": 8000000, "cost_price": 5000000
            },
            {
                "code": "SERV001", "name": "Gói bảo trì năm", "product_type": "Subscription",
                "unit": "Năm", "list_price": 2000000, "floor_price": 1500000, "cost_price": 800000
            },
            {
                "code": "PROD002", "name": "Thiết bị quét mã vạch", "product_type": "One-time",
                "unit": "Cái", "list_price": 5000000, "floor_price": 4000000, "cost_price": 3000000
            },
        ]

        for p_data in products:
            prod = db.query(Product).filter(Product.code == p_data["code"]).first()
            if not prod:
                db.add(Product(**p_data))

        db.commit()

        # Tạo một báo giá mẫu tham chiếu đến PROD001 để test chặn xóa
        p1 = db.query(Product).filter(Product.code == "PROD001").first()
        if p1:
            db.add(QuoteItem(quote_id=101, product_id=p1.id, quantity=1, applied_price=9000000))
            db.commit()

        print("✅ Đã đổ dữ liệu mẫu thành công!")
    except Exception as e:
        print(f"❌ Lỗi seed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
