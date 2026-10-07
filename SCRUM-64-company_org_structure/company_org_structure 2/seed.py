from app.database import SessionLocal
from app.models import Customer, SalesGroup, Employee, GeographicalArea

def seed_data():
    db = SessionLocal()
    try:
        # 1. Tạo khu vực địa lý
        area_south = GeographicalArea(name="Miền Nam")
        area_north = GeographicalArea(name="Miền Bắc")
        db.add_all([area_south, area_north])
        db.commit()

        # 2. Tạo nhân viên
        director = Employee(name="Nguyễn Giám Đốc", role="Director")
        lead1 = Employee(name="Trần Trưởng Nhóm 1", role="TeamLead")
        lead2 = Employee(name="Lê Trưởng Nhóm 2", role="TeamLead")
        staff1 = Employee(name="Staff A", role="Staff")
        staff2 = Employee(name="Staff B", role="Staff")
        staff3 = Employee(name="Staff C", role="Staff")
        db.add_all([director, lead1, lead2, staff1, staff2, staff3])
        db.commit()

        # 3. Tạo cấu trúc nhóm (Hierarchy)
        # Nhóm chính (Root)
        root_group = SalesGroup(name="Khối Kinh doanh", lead_id=director.id, area_id=area_south.id)
        db.add(root_group)
        db.commit()

        # Nhóm con 1 (Lead by lead1)
        group1 = SalesGroup(name="Nhóm Kinh doanh Miền Nam", parent_id=root_group.id, lead_id=lead1.id, area_id=area_south.id)
        db.add(group1)
        db.commit()

        # Nhóm con 2 (Lead by lead2, thuộc group1)
        group2 = SalesGroup(name="Nhóm Kinh doanh HCM", parent_id=group1.id, lead_id=lead2.id, area_id=area_south.id)
        db.add(group2)
        db.commit()

        # Gán nhân viên vào nhóm
        staff1.group_id = group1.id
        staff2.group_id = group2.id
        staff3.group_id = group2.id
        db.commit()

        print("✅ Đã đổ dữ liệu mẫu cấu trúc tổ chức thành công!")
        print(f"Demo: Trưởng nhóm {lead1.name} sẽ thấy dữ liệu của Nhóm Miền Nam và Nhóm HCM.")

    except Exception as e:
        print(f"❌ Lỗi seed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
