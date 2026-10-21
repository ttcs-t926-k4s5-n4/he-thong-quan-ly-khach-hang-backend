from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, crud
from .database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sales Common Categories API")

@app.post("/categories/", response_model=schemas.Category, status_code=status.HTTP_201_CREATED)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    return crud.create_category(db=db, category=category)

@app.get("/categories/", response_model=List[schemas.Category])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_categories(db, skip=skip, limit=limit)

@app.get("/categories/{category_id}/values", response_model=List[schemas.CategoryValue])
def read_category_values(category_id: int, db: Session = Depends(get_db)):
    return crud.get_category_values(db, category_id=category_id)

@app.post("/categories/values/", response_model=schemas.CategoryValue, status_code=status.HTTP_201_CREATED)
def create_category_value(value: schemas.CategoryValueCreate, db: Session = Depends(get_db)):
    return crud.create_category_value(db=db, category_value=value)

@app.put("/categories/values/{value_id}", response_model=schemas.CategoryValue)
def update_category_value(value_id: int, update_data: schemas.CategoryValueBase, db: Session = Depends(get_db)):
    db_val = crud.update_category_value(db=db, value_id=value_id, update_data=update_data)
    if not db_val:
        raise HTTPException(status_code=404, detail="Category value not found")
    return db_val

@app.delete("/categories/values/{value_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category_value(value_id: int, db: Session = Depends(get_db)):
    success = crud.delete_category_value(db=db, value_id=value_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category value not found")
    return None

# Dummy endpoint to create a lead referencing a value (to test the deletion constraint)
@app.post("/test/leads/", status_code=status.HTTP_201_CREATED)
def create_test_lead(name: str, value_id: int, db: Session = Depends(get_db)):
    db_lead = models.Lead(name=name, industry_value_id=value_id)
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return {"message": "Lead created", "lead_id": db_lead.id}
