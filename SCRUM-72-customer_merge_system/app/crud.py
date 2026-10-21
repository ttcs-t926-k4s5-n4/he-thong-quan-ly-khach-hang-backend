from sqlalchemy.orm import Session
from . import models, schemas
from fastapi import HTTPException, status
from thefuzz import fuzz # Library for fuzzy string matching

def get_customer_details(db: Session, customer_id: int):
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()

def find_duplicates(db: Session, customer_id: int):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        return []

    duplicates = []
    all_customers = db.query(models.Customer).filter(models.Customer.id != customer_id).all()

    for other in all_customers:
        is_duplicate = False
        reason = []

        # 1. Exact match on Tax ID
        if customer.tax_id and other.tax_id and customer.tax_id == other.tax_id:
            is_duplicate = True
            reason.append("Trùng mã số thuế")

        # 2. Exact match on Website
        if customer.website and other.website and customer.website == other.website:
            is_duplicate = True
            reason.append("Trùng website")

        # 3. Fuzzy match on Name (threshold 80%)
        if customer.name and other.name:
            similarity = fuzz.token_sort_ratio(customer.name, other.name)
            if similarity >= 80:
                is_duplicate = True
                reason.append(f"Tên gần giống ({similarity}%)")

        if is_duplicate:
            duplicates.append({
                "customer": other,
                "reasons": reason
            })

    return duplicates

def merge_customers(db: Session, merge_req: schemas.MergeRequest):
    source = db.query(models.Customer).filter(models.Customer.id == merge_req.source_customer_id).first()
    target = db.query(models.Customer).filter(models.Customer.id == merge_req.target_customer_id).first()

    if not source or not target:
        raise HTTPException(status_code=404, detail="One or both customers not found")

    try:
        # Move Contacts
        contacts = db.query(models.Contact).filter(models.Contact.customer_id == source.id).all()
        for c in contacts:
            c.customer_id = target.id

        # Move Opportunities
        opps = db.query(models.Opportunity).filter(models.Opportunity.customer_id == source.id).all()
        for o in opps:
            o.customer_id = target.id

        # Move Activities
        acts = db.query(models.Activity).filter(models.Activity.customer_id == source.id).all()
        for a in acts:
            a.customer_id = target.id

        # Finally, delete the source customer record
        db.delete(source)

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")
