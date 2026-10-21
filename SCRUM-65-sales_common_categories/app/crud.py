from sqlalchemy.orm import Session
from . import models, schemas
from fastapi import HTTPException, status

# Categories
def get_category(db: Session, category_id: int):
    return db.query(models.Category).filter(models.Category.id == category_id).first()

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Category).offset(skip).limit(limit).all()

def create_category(db: Session, category: schemas.CategoryCreate):
    db_category = models.Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# Category Values
def get_category_values(db: Session, category_id: int):
    # Sort by display_order as requested
    return db.query(models.CategoryValue)\
        .filter(models.CategoryValue.category_id == category_id)\
        .order_by(models.CategoryValue.display_order).all()

def create_category_value(db: Session, category_value: schemas.CategoryValueCreate):
    db_val = models.CategoryValue(**category_value.model_dump())
    db.add(db_val)
    db.commit()
    db.refresh(db_val)
    return db_val

def update_category_value(db: Session, value_id: int, update_data: schemas.CategoryValueBase):
    db_val = db.query(models.CategoryValue).filter(models.CategoryValue.id == value_id).first()
    if not db_val:
        return None

    for key, value in update_data.model_dump().items():
        setattr(db_val, key, value)

    db.commit()
    db.refresh(db_val)
    return db_val

def delete_category_value(db: Session, value_id: int):
    db_val = db.query(models.CategoryValue).filter(models.CategoryValue.id == value_id).first()
    if not db_val:
        return False

    # REQUIREMENT: "Giá trị đang được tham chiếu thì không xóa được"
    # Check if any lead references this value
    is_referenced = db.query(models.Lead).filter(models.Lead.industry_value_id == value_id).first() is not None
    if is_referenced:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete this value because it is being referenced by one or more leads."
        )

    db.delete(db_val)
    db.commit()
    return True
