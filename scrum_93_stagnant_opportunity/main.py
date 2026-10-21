from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, Date, DateTime, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

engine = create_engine("sqlite:///./scrum_93.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Opportunity(Base):
    __tablename__ = "stagnant_opportunities"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    owner_id = Column(String, index=True, nullable=False)
    team_id = Column(String, index=True, nullable=False)
    stage = Column(String, index=True, nullable=False)
    status = Column(String, default="open", index=True)
    expected_close = Column(Date, nullable=True)


class Activity(Base):
    __tablename__ = "opportunity_activities"
    id = Column(Integer, primary_key=True)
    opportunity_id = Column(Integer, index=True, nullable=False)
    kind = Column(String, nullable=False)
    actor_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class StageThreshold(Base):
    __tablename__ = "stage_thresholds"
    id = Column(Integer, primary_key=True)
    stage = Column(String, unique=True, nullable=False)
    inactive_days = Column(Integer, nullable=False)


class OpportunityFlag(Base):
    __tablename__ = "opportunity_flags"
    id = Column(Integer, primary_key=True)
    opportunity_id = Column(Integer, index=True, nullable=False)
    reason = Column(String, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


Base.metadata.create_all(engine)
app = FastAPI(title="SCRUM-93 Stagnation Alert API")


def db_session():
    db = SessionLocal()
    try: yield db
    finally: db.close()


class OpportunityInput(BaseModel):
    name: str
    owner_id: str
    team_id: str
    stage: str
    expected_close: Optional[date] = None


class ThresholdInput(BaseModel):
    stage: str
    inactive_days: int = Field(ge=1, le=365)


class ActivityInput(BaseModel):
    kind: str
    actor_id: str


@app.post("/opportunities", status_code=201)
def create_opportunity(data: OpportunityInput, db: Session = Depends(db_session)):
    row = Opportunity(**data.model_dump()); db.add(row); db.commit(); db.refresh(row); return row


@app.put("/settings/stage-threshold")
def set_threshold(data: ThresholdInput, db: Session = Depends(db_session)):
    row = db.query(StageThreshold).filter_by(stage=data.stage).first()
    if row is None: row = StageThreshold(stage=data.stage, inactive_days=data.inactive_days); db.add(row)
    else: row.inactive_days = data.inactive_days
    db.commit(); db.refresh(row); return row


@app.post("/opportunities/{opportunity_id}/activities", status_code=201)
def add_activity(opportunity_id: int, data: ActivityInput, db: Session = Depends(db_session)):
    if db.get(Opportunity, opportunity_id) is None: raise HTTPException(404, "Opportunity not found")
    row = Activity(opportunity_id=opportunity_id, **data.model_dump()); db.add(row)
    for flag in db.query(OpportunityFlag).filter_by(opportunity_id=opportunity_id, resolved_at=None).all(): flag.resolved_at = datetime.utcnow()
    db.commit(); db.refresh(row); return row


@app.post("/alerts/evaluate")
def evaluate_alerts(db: Session = Depends(db_session), today: date = date.today()):
    thresholds = {row.stage: row.inactive_days for row in db.query(StageThreshold).all()}
    created = []
    for opp in db.query(Opportunity).filter(Opportunity.status == "open").all():
        activity = db.query(Activity).filter_by(opportunity_id=opp.id).order_by(Activity.created_at.desc()).first()
        reasons = []
        limit = thresholds.get(opp.stage)
        if limit is not None:
            last_date = activity.created_at.date() if activity else None
            if last_date is None or (today - last_date).days >= limit: reasons.append(f"inactive_{limit}_days")
        if opp.expected_close and opp.expected_close < today: reasons.append("expected_close_overdue")
        active = db.query(OpportunityFlag).filter_by(opportunity_id=opp.id, resolved_at=None).all()
        existing = {f.reason: f for f in active}
        for reason in reasons:
            if reason not in existing:
                flag = OpportunityFlag(opportunity_id=opp.id, reason=reason); db.add(flag); created.append({"opportunity_id": opp.id, "reason": reason})
        for reason, flag in existing.items():
            if reason not in reasons: flag.resolved_at = datetime.utcnow()
    db.commit()
    return {"evaluated_at": datetime.utcnow(), "new_flags": created, "new_flag_count": len(created)}


@app.get("/alerts")
def get_alerts(team_id: Optional[str] = None, db: Session = Depends(db_session)):
    q = db.query(OpportunityFlag).filter(OpportunityFlag.resolved_at.is_(None))
    flags = q.order_by(OpportunityFlag.detected_at.desc()).all()
    results = []
    for flag in flags:
        opp = db.get(Opportunity, flag.opportunity_id)
        if opp and (team_id is None or opp.team_id == team_id):
            results.append({"flag_id": flag.id, "opportunity_id": opp.id, "name": opp.name, "owner_id": opp.owner_id, "team_id": opp.team_id, "stage": opp.stage, "reason": flag.reason, "detected_at": flag.detected_at})
    return results
