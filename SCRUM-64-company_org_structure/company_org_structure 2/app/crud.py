from sqlalchemy.orm import Session
from . import models, schemas
from fastapi import HTTPException

def create_area(db: Session, area: schemas.AreaCreate):
    db_area = models.GeographicalArea(**area.model_dump())
    db.add(db_area)
    db.commit()
    db.refresh(db_area)
    return db_area

def create_employee(db: Session, employee: schemas.EmployeeCreate):
    db_emp = models.Employee(**employee.model_dump())
    db.add(db_emp)
    db.commit()
    db.refresh(db_emp)
    return db_emp

def create_group(db: Session, group: schemas.GroupCreate):
    db_group = models.SalesGroup(**group.model_dump())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

def get_employee_data_scope(db: Session, lead_id: int):
    # 1. Find the group this lead is leading
    group = db.query(models.SalesGroup).filter(models.SalesGroup.lead_id == lead_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Employee is not a team lead of any group")

    # 2. Recursively find all child groups
    accessible_groups = {group.id}

    def find_children(parent_id):
        children = db.query(models.SalesGroup).filter(models.SalesGroup.parent_id == parent_id).all()
        for child in children:
            accessible_groups.add(child.id)
            find_children(child.id)

    find_children(group.id)

    # 3. Find all employees in these groups
    employees = db.query(models.Employee).filter(
        models.Employee.group_id.in_(list(accessible_groups))
    ).all()

    employee_ids = [e.id for e in employees]

    return {
        "team_lead_id": lead_id,
        "group_name": group.name,
        "accessible_group_ids": list(accessible_groups),
        "accessible_employee_ids": employee_ids
    }
