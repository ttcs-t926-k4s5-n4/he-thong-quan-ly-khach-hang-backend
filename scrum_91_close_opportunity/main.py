from datetime import date, datetime
from typing import Literal, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, Date, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

engine = create_engine("sqlite:///./scrum_91.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    owner_id = Column(String, nullable=False, index=True)
    team_id = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="open", index=True)
    amount = Column(Float, nullable=False, default=0)
    actual_value = Column(Float)
    close_date = Column(Date)
    loss_reason = Column(String)
    winning_competitor = Column(String)
    closed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OpportunityEvent(Base):
    __tablename__ = "opportunity_events"
    id = Column(Integer, primary_key=True)
    opportunity_id = Column(Integer, nullable=False, index=True)
    actor_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    reason = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(engine)
app = FastAPI(title="SCRUM-91 Opportunity Close API")


def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class OpportunityCreate(BaseModel):
    name: str = Field(min_length=1)
    owner_id: str
    team_id: str
    amount: float = Field(ge=0)


class CloseRequest(BaseModel):
    actor_id: str
    actual_value: Optional[float] = Field(default=None, ge=0)
    signed_date: Optional[date] = None
    loss_reason: Optional[str] = None
    winning_competitor: Optional[str] = None


class ReopenRequest(BaseModel):
    actor_id: str
    is_manager: bool
    reason: str = Field(min_length=3)


@app.post("/opportunities", status_code=201)
def create_opportunity(payload: OpportunityCreate, db: Session = Depends(db_session)):
    row = Opportunity(**payload.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return row


@app.post("/opportunities/{opportunity_id}/close/{result}")
def close_opportunity(opportunity_id: int, result: Literal["won", "lost"], payload: CloseRequest, db: Session = Depends(db_session)):
    row = db.get(Opportunity, opportunity_id)
    if row is None: raise HTTPException(404, "Opportunity not found")
    if row.status != "open": raise HTTPException(409, "Opportunity is already closed")
    if result == "won":
        if payload.actual_value is None or payload.signed_date is None:
            raise HTTPException(422, "Winning requires actual_value and signed_date")
        if payload.actual_value < 0: raise HTTPException(422, "actual_value must be non-negative")
        row.actual_value, row.close_date, row.status = payload.actual_value, payload.signed_date, "won"
    else:
        if not payload.loss_reason or not payload.loss_reason.strip():
            raise HTTPException(422, "Loss requires loss_reason")
        row.loss_reason = payload.loss_reason.strip()
        row.winning_competitor = payload.winning_competitor
        row.close_date, row.status = payload.signed_date or date.today(), "lost"
    row.closed_at = datetime.utcnow()
    db.add(OpportunityEvent(opportunity_id=row.id, actor_id=payload.actor_id, action=f"closed_{result}"))
    db.commit(); db.refresh(row)
    return row


@app.patch("/opportunities/{opportunity_id}")
def edit_open_opportunity(opportunity_id: int, payload: OpportunityCreate, db: Session = Depends(db_session)):
    row = db.get(Opportunity, opportunity_id)
    if row is None: raise HTTPException(404, "Opportunity not found")
    if row.status != "open": raise HTTPException(409, "Closed opportunity is locked; manager reopen is required")
    for key, value in payload.model_dump().items(): setattr(row, key, value)
    db.commit(); db.refresh(row)
    return row


@app.post("/opportunities/{opportunity_id}/reopen")
def reopen_opportunity(opportunity_id: int, payload: ReopenRequest, db: Session = Depends(db_session)):
    row = db.get(Opportunity, opportunity_id)
    if row is None: raise HTTPException(404, "Opportunity not found")
    if not payload.is_manager: raise HTTPException(403, "Manager role required")
    if row.status == "open": raise HTTPException(409, "Opportunity is already open")
    db.add(OpportunityEvent(opportunity_id=row.id, actor_id=payload.actor_id, action="reopened", reason=payload.reason))
    row.status, row.closed_at = "open", None
    db.commit(); db.refresh(row)
    return row


@app.get("/reports/won-revenue")
def won_revenue(owner_id: Optional[str] = None, team_id: Optional[str] = None, db: Session = Depends(db_session)):
    q = db.query(Opportunity).filter(Opportunity.status == "won")
    if owner_id: q = q.filter(Opportunity.owner_id == owner_id)
    if team_id: q = q.filter(Opportunity.team_id == team_id)
    rows = q.all()
    return {"won_count": len(rows), "actual_revenue": sum(r.actual_value or 0 for r in rows), "opportunities": rows}
