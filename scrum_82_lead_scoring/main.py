from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)
app = FastAPI(title="SCRUM-82 Lead Scoring API", version="1.0.0")
CRITERIA = ("industry", "company_size", "source", "interest_level")


def serialize(model):
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


def get_thresholds(db: Session):
    thresholds = db.query(models.ScoreThreshold).filter_by(id=1).first()
    if thresholds is None:
        thresholds = models.ScoreThreshold(id=1, hot_min=70, warm_min=40)
        db.add(thresholds)
        db.flush()
    return thresholds


def recalculate_score(db: Session, lead: models.Lead):
    rules = db.query(models.ScoreRule).all()
    points = {
        (rule.criterion, rule.value.strip().casefold()): rule.points
        for rule in rules
    }
    score = sum(
        points.get((criterion, (getattr(lead, criterion) or "").strip().casefold()), 0)
        for criterion in CRITERIA
    )
    thresholds = get_thresholds(db)
    lead.score = score
    lead.score_category = "hot" if score >= thresholds.hot_min else (
        "warm" if score >= thresholds.warm_min else "cold"
    )
    lead.updated_at = datetime.utcnow()


def current_config(db: Session):
    thresholds = get_thresholds(db)
    rules = {}
    for rule in db.query(models.ScoreRule).order_by(models.ScoreRule.id).all():
        rules.setdefault(rule.criterion, {})[rule.value] = rule.points
    return {"rules": rules, "hot_min": thresholds.hot_min, "warm_min": thresholds.warm_min}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/scoring/config", response_model=schemas.ScoreConfigOut)
def get_scoring_config(db: Session = Depends(get_db)):
    return current_config(db)


@app.put("/scoring/config", response_model=schemas.ScoreConfigOut)
def set_scoring_config(config: schemas.ScoreConfig, db: Session = Depends(get_db)):
    try:
        db.query(models.ScoreRule).delete(synchronize_session=False)
        for criterion, values in config.rules.items():
            for value, points in values.items():
                normalized_value = value.strip()
                if normalized_value:
                    db.add(models.ScoreRule(criterion=criterion, value=normalized_value, points=points))
        thresholds = get_thresholds(db)
        thresholds.hot_min = config.hot_min
        thresholds.warm_min = config.warm_min
        db.flush()
        for lead in db.query(models.Lead).all():
            recalculate_score(db, lead)
        db.commit()
        return current_config(db)
    except Exception:
        db.rollback()
        raise


@app.post("/leads", response_model=schemas.LeadOut, status_code=201)
def create_lead(lead_data: schemas.LeadCreate, db: Session = Depends(get_db)):
    lead = models.Lead(**serialize(lead_data))
    recalculate_score(db, lead)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@app.patch("/leads/{lead_id}", response_model=schemas.LeadOut)
def update_lead(lead_id: int, changes: schemas.LeadUpdate, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter_by(id=lead_id).first()
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead không tồn tại")
    fields = changes.model_dump(exclude_unset=True) if hasattr(changes, "model_dump") else changes.dict(exclude_unset=True)
    for field, value in fields.items():
        setattr(lead, field, value)
    recalculate_score(db, lead)
    db.commit()
    db.refresh(lead)
    return lead


@app.get("/leads/priority", response_model=List[schemas.LeadOut])
def list_leads_by_priority(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    # Every active lead remains in the results; this endpoint only sorts by priority.
    return (
        db.query(models.Lead)
        .filter(models.Lead.is_active.is_(True))
        .order_by(models.Lead.score.desc(), models.Lead.created_at.asc(), models.Lead.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@app.get("/leads/{lead_id}", response_model=schemas.LeadOut)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter_by(id=lead_id).first()
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead không tồn tại")
    return lead
