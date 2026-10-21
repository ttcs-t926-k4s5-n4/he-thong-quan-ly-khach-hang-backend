from app.database import SessionLocal
from app.models import Category, CategoryValue

def seed_data():
    db = SessionLocal()
    try:
        # 1. Định nghĩa các danh mục chính
        categories_data = [
            {"name": "Ngành nghề khách hàng", "description": "Phân loại ngành nghề của khách hàng"},
            {"name": "Quy mô doanh nghiệp", "description": "Phân loại quy mô dựa trên nhân sự/doanh thu"},
            {"name": "Nguồn lead", "description": "Kênh tiếp cận khách hàng"},
            {"name": "Loại hoạt động", "description": "Phân loại hoạt động chăm sóc khách hàng"},
        ]

        for cat_data in categories_data:
            cat = db.query(Category).filter(Category.name == cat_data["name"]).first()
            if not cat:
                cat = Category(**cat_data)
                db.add(cat)
                db.commit()
                db.refresh(cat)

            # 2. Thêm các giá trị mẫu cho từng danh mục
            values_map = {
                "Ngành nghề khách hàng": ["Công nghệ thông tin", "Sản xuất", "Dịch vụ", "Thương mại", "Y tế"],
                "Quy mô doanh nghiệp": ["Siêu nhỏ (<10 người)", "Nhỏ (10-50 người)", "Vừa (50-200 người)", "Lớn (>200 người)"],
                "Nguồn lead": ["Facebook", "Google Ads", "Referral", "Cold Call", "Event"],
                "Loại hoạt động": ["Gọi điện", "Gặp mặt trực tiếp", "Gửi Email", "Chat Zalo/Messenger"],
            }

            values = values_map.get(cat.name, [])
            for index, val_text in enumerate(values):
                # Tránh trùng lặp
                exists = db.query(CategoryValue).filter(
                    CategoryValue.category_id == cat.id,
                    CategoryValue.value == val_text
                ).first()

                if not exists:
                    db_val = CategoryValue(
                        category_id=cat.id,
                        value=val_text,
                        display_order=index + 1
                    )
                    db.add(db_val)

        db.commit()
        print("✅ Đã đổ dữ liệu mẫu thành công vào database!")

    except Exception as e:
        print(f"❌ Lỗi khi seed dữ liệu: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
