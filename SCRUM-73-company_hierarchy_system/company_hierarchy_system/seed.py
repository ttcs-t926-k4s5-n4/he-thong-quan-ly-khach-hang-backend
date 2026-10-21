from app.database import SessionLocal
from app.models import Customer, Opportunity

def seed_data():
    db = SessionLocal()
    try:
        # 1. Tạo Tập đoàn Mẹ (Root)
        parent = Customer(name="Tập đoàn Vingroup", tax_id="ROOT001")
        db.add(parent)
        db.commit()
        db.refresh(parent)

        # 2. Tạo Công ty con cấp 1
        child1 = Customer(name="VinFast", tax_id="CHILD001", parent_id=parent.id)
        child2 = Customer(name="Vinhomes", tax_id="CHILD002", parent_id=parent.id)
        db.add_all([child1, child2])
        db.commit()

        # 3. Tạo Công ty cháu (con của VinFast)
        grandchild1 = Customer(name="VinFast Battery", tax_id="GCHILD001", parent_id=child1.id)
        db.add(grandchild1)
        db.commit()

        # 4. Thêm giá trị hợp đồng (Opportunities) cho mỗi cấp
        # Mẹ: 100tr
        db.add(Opportunity(customer_id=parent.id, title="Hợp đồng tập đoàn", value=100000000))
        # Con 1 (VinFast): 50tr
        db.add(Opportunity(customer_id=child1.id, title="Hợp đồng xe", value=50000000))
        # Con 2 (Vinhomes): 30tr
        db.add(Opportunity(customer_id=child2.id, title="Hợp đồng nhà", value=30000000))
        # Cháu (Battery): 20tr
        db.add(Opportunity(customer_id=grandchild1.id, title="Hợp đồng pin", value=20000000))

        db.commit()
        print("✅ Đã đổ dữ liệu mẫu phân cấp thành công!")
        print(f"Tổng giá trị kỳ vọng cho Vingroup: 100 + 50 + 30 + 20 = 200 triệu")

    except Exception as e:
        print(f"❌ Lỗi seed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
