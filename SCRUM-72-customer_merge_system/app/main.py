from fastapi import FastAPI, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, crud
from .database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Customer Merge System API")

# Role Simulation (Simple header check)
async def verify_team_lead(x_role: str = Header(None)):
    if x_role != "TeamLead":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the Sales Team Lead has permission to perform a customer merge."
        )
    return True

@app.post("/customers/", response_model=schemas.Customer, status_code=status.HTTP_201_CREATED)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    db_cust = models.Customer(**customer.model_dump())
    db.add(db_cust)
    db.commit()
    db.refresh(db_cust)
    return db_cust

@app.get("/customers/{customer_id}/duplicates")
def find_duplicates(customer_id: int, db: Session = Depends(get_db)):
    duplicates = crud.find_duplicates(db, customer_id)
    # Transform result for the response
    result = []
    for item in duplicates:
        result.append({
            "customer": item["customer"],
            "reasons": item["reasons"]
        })
    return result

@app.get("/customers/{customer_id}", response_model=schemas.CustomerDetail)
def get_customer_details(customer_id: int, db: Session = Depends(get_db)):
    db_cust = crud.get_customer_details(db, customer_id)
    if not db_cust:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_cust

@app.post("/customers/merge", status_code=status.HTTP_200_OK)
def merge_customers(
    merge_req: schemas.MergeRequest,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_team_lead)
):
    # REQUIREMENT: "Chỉ Trưởng nhóm trở lên được thực hiện gộp"
    success = crud.merge_customers(db, merge_req)
    if success:
        return {"message": "Customers merged successfully. All related data has been moved."}
    raise HTTPException(status_code=500, detail="Merge failed")

# Demo Endpoint: Create related data for testing
@app.post("/test/contacts/", status_code=status.HTTP_201_CREATED)
def create_contact(name: str, customer_id: int, db: Session = Depends(get_db)):
    db_c = models.Contact(name=name, customer_id=customer_id)
    db.add(db_c)
    db.commit()
    return {"message": "Contact created"}

@app.post("/test/opportunities/", status_code=status.HTTP_201_CREATED)
def create_opp(title: str, customer_id: int, db: Session = Depends(get_db)):
    db_o = models.Opportunity(title=title, customer_id=customer_id)
    db.add(db_o)
    db.commit()
    return {"message": "Opportunity created"}
