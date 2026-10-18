from datetime import datetime
from typing import Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

engine = create_engine("sqlite:///./scrum_102.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Customer(Base):
    __tablename__ = "timeline_customers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class TimelineEvent(Base):
    __tablename__ = "customer_timeline_events"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, index=True, nullable=False)
    kind = Column(String, index=True, nullable=False)
    actor_id = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    occurred_at = Column(DateTime, default=datetime.utcnow, index=True)


Base.metadata.create_all(engine)
app = FastAPI(title="SCRUM-102 Customer Timeline API")


def db_session():
    db = SessionLocal()
    try: yield db
    finally: db.close()


class CustomerInput(BaseModel):
    name: str = Field(min_length=1)


class EventInput(BaseModel):
    kind: Literal["activity", "opportunity_change", "quote_sent"]
    actor_id: str
    title: str
    details: Optional[str] = None
    occurred_at: Optional[datetime] = None


@app.post("/customers", status_code=201)
def create_customer(data: CustomerInput, db: Session = Depends(db_session)):
    row = Customer(**data.model_dump()); db.add(row); db.commit(); db.refresh(row); return row


@app.post("/customers/{customer_id}/timeline", status_code=201)
def append_event(customer_id: int, data: EventInput, db: Session = Depends(db_session)):
    if db.get(Customer, customer_id) is None: raise HTTPException(404, "Customer not found")
    row = TimelineEvent(customer_id=customer_id, **data.model_dump(exclude={"occurred_at"}), occurred_at=data.occurred_at or datetime.utcnow())
    db.add(row); db.commit(); db.refresh(row); return row


@app.get("/customers/{customer_id}/timeline")
def get_timeline(
    customer_id: int,
    kind: Optional[Literal["activity", "opportunity_change", "quote_sent"]] = None,
    actor_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(db_session),
):
    if db.get(Customer, customer_id) is None: raise HTTPException(404, "Customer not found")
    q = db.query(TimelineEvent).filter(TimelineEvent.customer_id == customer_id)
    if kind: q = q.filter(TimelineEvent.kind == kind)
    if actor_id: q = q.filter(TimelineEvent.actor_id == actor_id)
    if since: q = q.filter(TimelineEvent.occurred_at >= since.replace(tzinfo=None))
    if until: q = q.filter(TimelineEvent.occurred_at <= until.replace(tzinfo=None))
    total = q.count()
    events = q.order_by(TimelineEvent.occurred_at.desc(), TimelineEvent.id.desc()).offset(offset).limit(limit).all()
    return {"customer_id": customer_id, "total": total, "limit": limit, "offset": offset, "events": events}
