from sqlalchemy.orm import Session
from sqlalchemy import or_
from . import models, schemas

def get_lead(db: Session, lead_id: int):
    return db.query(models.Lead).filter(models.Lead.id == lead_id).first()

def get_leads(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Lead).offset(skip).limit(limit).all()

def create_lead(db: Session, lead: schemas.LeadCreate):
    db_lead = models.Lead(**lead.model_dump())
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead


def find_duplicates(db: Session, lead: schemas.LeadCreate):
    # Tìm kiếm trùng lặp theo email OR phone OR company_name
    # Chỉ tìm những lead chưa bị merge
    query = db.query(models.Lead).filter(
        models.Lead.is_merged == False,
        or_(
            (models.Lead.email == lead.email) if lead.email else False,
            (models.Lead.phone == lead.phone) if lead.phone else False,
            (models.Lead.company_name == lead.company_name) if lead.company_name else False,
        )
    )
    return query.all()

def create_lead_history(db: Session, history: schemas.LeadHistoryCreate, lead_id: int):
    db_history = models.LeadHistory(**history.model_dump(), lead_id=lead_id)
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history

def merge_leads(db: Session, source_id: int, target_id: int, merged_by: str):
    source_lead = get_lead(db, source_id)
    target_lead = get_lead(db, target_id)

    if not source_lead or not target_lead:
        return None

    # 1. Chuyển toàn bộ lịch sử từ source sang target
    histories = db.query(models.LeadHistory).filter(models.LeadHistory.lead_id == source_id).all()
    for h in histories:
        h.lead_id = target_id
    
    # 2. Đánh dấu source lead là đã merge
    source_lead.is_merged = True
    source_lead.merged_into_id = target_id

    # 3. Lưu log merge
    log = models.MergeLog(source_lead_id=source_id, target_lead_id=target_id, merged_by=merged_by)
    db.add(log)

    db.commit()
    return target_lead
