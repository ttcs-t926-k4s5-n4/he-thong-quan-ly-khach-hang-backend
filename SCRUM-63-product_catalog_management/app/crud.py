from sqlalchemy.orm import Session
from . import models, schemas
from fastapi import HTTPException, status

def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate):
    # Check for duplicate code
    db_prod = db.query(models.Product).filter(models.Product.code == product.code).first()
    if db_prod:
        raise HTTPException(status_code=400, detail="Product code already exists")

    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, update_data: schemas.ProductUpdate):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        return None

    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        return False

    # REQUIREMENT: "Sản phẩm đã xuất hiện trong báo giá thì không xoá được, chỉ ngừng kinh doanh"
    is_referenced = db.query(models.QuoteItem).filter(models.QuoteItem.product_id == product_id).first() is not None

    if is_referenced:
        # Set to inactive instead of deleting
        db_product.is_active = False
        db.commit()
        return "discontinued" # Special return value to indicate status change

    db.delete(db_product)
    db.commit()
    return "deleted"

def create_quote_item(db: Session, item: schemas.QuoteItemCreate):
    db_item = models.QuoteItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
