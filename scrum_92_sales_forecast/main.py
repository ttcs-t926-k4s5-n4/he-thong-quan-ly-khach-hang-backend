from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, Date, Float, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

engine = create_engine("sqlite:///./scrum_92.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Opportunity(Base):
    __tablename__ = "forecast_opportunities"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    owner_id = Column(String, index=True, nullable=False)
    team_id = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    probability = Column(Float, nullable=False, default=0.0)
    expected_close = Column(Date, nullable=False, index=True)
    status = Column(String, nullable=False, default="open", index=True)
    actual_value = Column(Float)


class Target(Base):
    __tablename__ = "forecast_targets"
    id = Column(Integer, primary_key=True)
    period = Column(String, nullable=False, index=True)
    period_key = Column(String, nullable=False, index=True)
    owner_id = Column(String, nullable=True, index=True)
    team_id = Column(String, nullable=True, index=True)
    amount = Column(Float, nullable=False)


Base.metadata.create_all(engine)
app = FastAPI(title="SCRUM-92 Weighted Sales Forecast API")


def db_session():
    db = SessionLocal()
    try: yield db
    finally: db.close()


class OpportunityInput(BaseModel):
    name: str
    owner_id: str
    team_id: str
    amount: float = Field(ge=0)
    probability: float = Field(ge=0, le=1)
    expected_close: date


class TargetInput(BaseModel):
    period: str = Field(pattern="^(month|quarter)$")
    period_key: str
    owner_id: Optional[str] = None
    team_id: Optional[str] = None
    amount: float = Field(ge=0)


def period_key(day: date, period: str):
    if period == "month": return day.strftime("%Y-%m")
    quarter = (day.month - 1) // 3 + 1
    return f"{day.year}-Q{quarter}"


@app.post("/opportunities", status_code=201)
def add_opportunity(data: OpportunityInput, db: Session = Depends(db_session)):
    row = Opportunity(**data.model_dump()); db.add(row); db.commit(); db.refresh(row); return row


@app.post("/targets", status_code=201)
def set_target(data: TargetInput, db: Session = Depends(db_session)):
    row = Target(**data.model_dump()); db.add(row); db.commit(); db.refresh(row); return row


@app.get("/forecast")
def forecast(period: str = "month", owner_id: Optional[str] = None, team_id: Optional[str] = None, db: Session = Depends(db_session)):
    if period not in {"month", "quarter"}: raise HTTPException(422, "period must be month or quarter")
    q = db.query(Opportunity).filter(Opportunity.status == "open")
    if owner_id: q = q.filter(Opportunity.owner_id == owner_id)
    if team_id: q = q.filter(Opportunity.team_id == team_id)
    grouped = {}
    for row in q.all():
        key = period_key(row.expected_close, period)
        bucket = grouped.setdefault(key, {"weighted_forecast": 0.0, "pipeline_amount": 0.0, "opportunity_count": 0})
        bucket["weighted_forecast"] += row.amount * row.probability
        bucket["pipeline_amount"] += row.amount
        bucket["opportunity_count"] += 1
    out = []
    for key, bucket in sorted(grouped.items()):
        tq = db.query(Target).filter(Target.period == period, Target.period_key == key)
        if owner_id: tq = tq.filter(Target.owner_id == owner_id)
        if team_id: tq = tq.filter(Target.team_id == team_id)
        target = sum(t.amount for t in tq.all())
        actual_q = db.query(Opportunity).filter(Opportunity.status == "won")
        if owner_id: actual_q = actual_q.filter(Opportunity.owner_id == owner_id)
        if team_id: actual_q = actual_q.filter(Opportunity.team_id == team_id)
        actual = sum((o.actual_value if o.actual_value is not None else o.amount) for o in actual_q.all() if o.expected_close and period_key(o.expected_close, period) == key)
        out.append({"period": key, **bucket, "target": target, "actual_won": actual, "forecast_vs_target": bucket["weighted_forecast"] - target})
    return {"period_type": period, "owner_id": owner_id, "team_id": team_id, "results": out}
