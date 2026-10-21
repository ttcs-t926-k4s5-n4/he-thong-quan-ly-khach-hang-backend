from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, crud, database

# Khởi tạo database
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Lead Deduplication System")

@app.post("/leads/", response_model=schemas.LeadOut)
def create_lead(lead: schemas.LeadCreate, db: Session = Depends(database.get_db)):
    # Bước 1: Kiểm tra trùng lặp
    duplicates = crud.find_duplicates(db, lead)
    if duplicates:
        # Trong thực tế, có thể trả về 409 Conflict hoặc một response đặc biệt để frontend cảnh báo
        # Ở đây mình sẽ trả về thông tin lead bị trùng để frontend xử lý cảnh báo
        raise HTTPException(
            status_code=409, 
            detail={
                "message": "Phát hiện lead trùng lặp", 
                "duplicates": [
                    {"id": d.id, "email": d.email, "phone": d.phone, "company_name": d.company_name} 
                    for d in duplicates
                ]
            }
        )
    
    return crud.create_lead(db=db, lead=lead)

@app.get("/leads/", response_model=List[schemas.LeadOut])
def read_leads(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return crud.get_leads(db, skip=skip, limit=limit)


@app.post("/leads/merge", response_model=schemas.LeadOut)
def merge_leads(request: schemas.MergeRequest, db: Session = Depends(database.get_db)):
    target_lead = crud.merge_leads(db, request.source_lead_id, request.target_lead_id, request.merged_by)
    if not target_lead:
        raise HTTPException(status_code=404, detail="Lead không tồn tại")
    return target_lead

@app.post("/leads/{lead_id}/history", response_model=schemas.LeadHistoryOut)
def add_history(lead_id: int, history: schemas.LeadHistoryCreate, db: Session = Depends(database.get_db)):
    lead = crud.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead không tồn tại")
    return crud.create_lead_history(db, history, lead_id)

@app.get("/leads/{lead_id}/history", response_model=List[schemas.LeadHistoryOut])
def read_history(lead_id: int, db: Session = Depends(database.get_db)):
    lead = crud.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead không tồn tại")
    return lead.history
