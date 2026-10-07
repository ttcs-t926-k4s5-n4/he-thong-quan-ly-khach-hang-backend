from app.database import SessionLocal
from app.models import Customer, Contact, Opportunity, Activity

def seed_data():
    db = SessionLocal()
    try:
        # 1. Tạo khách hàng trùng nhau theo Mã số thuế
        c1 = Customer(name="Công ty ABC", tax_id="123456789", website="abc.com")
        c2 = Customer(name="Công ty ABC Co., Ltd", tax_id="123456789", website="abc.com")

        # 2. Tạo khách hàng trùng nhau theo Tên (Fuzzy match)
        c3 = Customer(name="Tập đoàn Vingroup", tax_id="999001", website="vin.com")
        c4 = Customer(name="Vingroup Tập đoàn", tax_id="999002", website="vin.com")

        # 3. Tạo khách hàng không trùng
        c5 = Customer(name="Công ty XYZ", tax_id="888000", website="xyz.com")

        db.add_all([c1, c2, c3, c4, c5])
        db.commit()

        # Tạo dữ liệu liên quan cho C1 và C2 để test gộp
        contact1 = Contact(customer_id=c1.id, name="Nguyễn Văn A", email="a@abc.com")
        contact2 = Contact(customer_id=c2.id, name="Trần Thị B", email="b@abc.com")
        opp1 = Opportunity(customer_id=c1.id, title="Hợp đồng phần mềm", value=1000, stage="Negotiation")
        opp2 = Opportunity(customer_id=c2.id, title="Gói bảo trì", value=500, stage="Closing")

        db.add_all([contact1, contact2, opp1, opp2])
        db.commit()

        print("✅ Đã đổ dữ liệu mẫu thành công! Hãy thử tìm trùng lặp cho Customer ID 1 hoặc 3.")

    except Exception as e:
        print(f"❌ Lỗi seed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
