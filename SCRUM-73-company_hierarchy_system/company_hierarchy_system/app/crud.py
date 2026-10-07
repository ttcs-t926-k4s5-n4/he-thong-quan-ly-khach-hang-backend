from sqlalchemy.orm import Session
from . import models, schemas
from fastapi import HTTPException

def get_customer(db: Session, customer_id: int):
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()

def create_customer(db: Session, customer: schemas.CustomerCreate):
    db_cust = models.Customer(**customer.model_dump())
    db.add(db_cust)
    db.commit()
    db.refresh(db_cust)
    return db_cust

def set_customer_parent(db: Session, customer_id: int, parent_id: int):
    customer = get_customer(db, customer_id)
    parent = get_customer(db, parent_id)

    if not customer or not parent:
        raise HTTPException(status_code=404, detail="Customer or Parent not found")

    if customer_id == parent_id:
        raise HTTPException(status_code=400, detail="A customer cannot be their own parent")

    # Avoid circular reference (simple check: is the new parent actually a child of the customer?)
    curr = parent
    while curr:
        if curr.parent_id == customer_id:
            raise HTTPException(status_code=400, detail="Circular reference detected")
        curr = curr.parent

    customer.parent_id = parent_id
    db.commit()
    db.refresh(customer)
    return customer

def calculate_total_value(db: Session, customer: models.Customer):
    """
    Recursively calculate the total value of a company and all its descendants.
    """
    # Value of the current company
    current_value = sum(opp.value for opp in customer.opportunities)

    # Value of all child companies (recursive)
    children_value = 0
    for child in customer.children:
        children_value += calculate_total_value(db, child)

    return current_value + children_value

def get_company_group_stats(db: Session, customer_id: int):
    customer = get_customer(db, customer_id)
    if not customer:
        return None

    total_value = calculate_total_value(db, customer)

    # Count total descendants (recursive)
    def count_descendants(cust):
        count = 0
        for child in cust.children:
            count += 1 + count_descendants(child)
        return count

    return {
        "customer_id": customer.id,
        "name": customer.name,
        "total_group_value": total_value,
        "child_count": count_descendants(customer)
    }
