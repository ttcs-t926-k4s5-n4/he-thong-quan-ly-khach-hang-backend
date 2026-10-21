from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

engine = create_engine("sqlite:///./scrum_94.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Opportunity(Base):
    __tablename__ = "transfer_opportunities"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    owner_id = Column(String, index=True, nullable=False)


class Activity(Base):
    __tablename__ = "transfer_activities"
    id = Column(Integer, primary_key=True)
    opportunity_id = Column(Integer, index=True, nullable=False)
    kind = Column(String, nullable=False)
    details = Column(String, nullable=False)
    actor_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class TransferLog(Base):
    __tablename__ = "ownership_transfer_logs"
    id = Column(Integer, primary_key=True)
    opportunity_id = Column(Integer, index=True, nullable=False)
    from_owner = Column(String, nullable=False)
    to_owner = Column(String, nullable=False)
    actor_id = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(engine)
app = FastAPI(title="SCRUM-94 Opportunity Transfer API")


def db_session():
    db = SessionLocal()
    try: yield db
    finally: db.close()


class OpportunityInput(BaseModel):
    name: str
    owner_id: str


class TransferInput(BaseModel):
    opportunity_ids: List[int] = Field(min_length=1)
    to_owner: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    reason: str = Field(min_length=3)


class ActivityInput(BaseModel):
    kind: str
    details: str
    actor_id: str


@app.post("/opportunities", status_code=201)
def create_opportunity(data: OpportunityInput, db: Session = Depends(db_session)):
    row = Opportunity(**data.model_dump()); db.add(row); db.commit(); db.refresh(row); return row


@app.post("/opportunities/{opportunity_id}/activities", status_code=201)
def add_activity(opportunity_id: int, data: ActivityInput, db: Session = Depends(db_session)):
    if db.get(Opportunity, opportunity_id) is None: raise HTTPException(404, "Opportunity not found")
    row = Activity(opportunity_id=opportunity_id, **data.model_dump()); db.add(row); db.commit(); db.refresh(row); return row


@app.post("/ownership/transfers")
def transfer_ownership(data: TransferInput, db: Session = Depends(db_session)):
    ids = list(dict.fromkeys(data.opportunity_ids))
    rows = db.query(Opportunity).filter(Opportunity.id.in_(ids)).with_for_update().all()
    found = {row.id for row in rows}
    missing = sorted(set(ids) - found)
    if missing: raise HTTPException(404, {"message": "Some opportunities do not exist", "missing_ids": missing})
    try:
        for row in rows:
            previous = row.owner_id
            if previous == data.to_owner: continue
            db.add(TransferLog(opportunity_id=row.id, from_owner=previous, to_owner=data.to_owner, actor_id=data.actor_id, reason=data.reason.strip()))
            row.owner_id = data.to_owner
        db.commit()
    except Exception:
        db.rollback(); raise
    return {"transferred_count": len(rows), "opportunities": rows}


@app.get("/opportunities")
def list_opportunities(owner_id: str, db: Session = Depends(db_session)):
    return db.query(Opportunity).filter(Opportunity.owner_id == owner_id).order_by(Opportunity.id.desc()).all()


@app.get("/opportunities/{opportunity_id}/history")
def opportunity_history(opportunity_id: int, db: Session = Depends(db_session)):
    if db.get(Opportunity, opportunity_id) is None: raise HTTPException(404, "Opportunity not found")
    activities = db.query(Activity).filter_by(opportunity_id=opportunity_id).all()
    transfers = db.query(TransferLog).filter_by(opportunity_id=opportunity_id).all()
    return {"activities": activities, "ownership_transfers": transfers}
