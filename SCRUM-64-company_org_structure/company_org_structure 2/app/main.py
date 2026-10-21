from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, crud
from .database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Company Org Structure API")

@app.post("/areas/", response_model=schemas.Area, status_code=status.HTTP_201_CREATED)
def create_area(area: schemas.AreaCreate, db: Session = Depends(get_db)):
    return crud.create_area(db=db, area=area)

@app.post("/employees/", response_model=schemas.Employee, status_code=status.HTTP_201_CREATED)
def create_employee(employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    return crud.create_employee(db=db, employee=employee)

@app.post("/groups/", response_model=schemas.Group, status_code=status.HTTP_201_CREATED)
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    return crud.create_group(db=db, group=group)

@app.get("/data-scope/{lead_id}", response_model=schemas.DataScopeResponse)
def get_data_scope(lead_id: int, db: Session = Depends(get_db)):
    # REQUIREMENT: "Quyết định phạm vi dữ liệu mà Trưởng nhóm nhìn thấy"
    # Trưởng nhóm thấy dữ liệu của nhóm mình và tất cả các nhóm con bên dưới
    return crud.get_employee_data_scope(db, lead_id=lead_id)
