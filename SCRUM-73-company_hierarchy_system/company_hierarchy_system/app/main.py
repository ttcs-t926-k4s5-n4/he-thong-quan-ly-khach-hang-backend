from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, crud
from .database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Company Hierarchy Management API")

@app.post("/customers/", response_model=schemas.Customer, status_code=status.HTTP_201_CREATED)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    return crud.create_customer(db=db, customer=customer)

@app.put("/customers/{customer_id}/parent/{parent_id}", response_model=schemas.Customer)
def set_parent(customer_id: int, parent_id: int, db: Session = Depends(get_db)):
    # REQUIREMENT: "Gắn một khách hàng làm công ty con của khách hàng khác"
    return crud.set_customer_parent(db=db, customer_id=customer_id, parent_id=parent_id)

@app.get("/customers/{customer_id}/group-stats", response_model=schemas.HierarchyResponse)
def get_group_stats(customer_id: int, db: Session = Depends(get_db)):
    # REQUIREMENT: "Hiển thị tổng giá trị hợp đồng của cả nhóm công ty"
    stats = crud.get_company_group_stats(db, customer_id=customer_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Customer not found")
    return stats

# Demo endpoint to add opportunities (to test total value calculation)
@app.post("/test/opportunities/", status_code=status.HTTP_201_CREATED)
def add_opportunity(customer_id: int, title: str, value: float, db: Session = Depends(get_db)):
    opp = models.Opportunity(customer_id=customer_id, title=title, value=value)
    db.add(opp)
    db.commit()
    return {"message": "Opportunity added"}
