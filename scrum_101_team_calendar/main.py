from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

engine = create_engine("sqlite:///./scrum_101.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class CalendarItem(Base):
    __tablename__ = "calendar_items"
    id = Column(Integer, primary_key=True)
    kind = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    owner_id = Column(String, nullable=False, index=True)
    team_id = Column(String, nullable=False, index=True)
    starts_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ends_at = Column(DateTime(timezone=True), nullable=False, index=True)
    attendees = Column(String, nullable=False, default="")


Base.metadata.create_all(engine)
app = FastAPI(title="SCRUM-101 Team Calendar API")


def db_session():
    db = SessionLocal()
    try: yield db
    finally: db.close()


class CalendarCreate(BaseModel):
    kind: Literal["meeting", "task"]
    title: str = Field(min_length=1)
    owner_id: str
    team_id: str
    starts_at: datetime
    ends_at: datetime
    attendees: List[str] = []

    @field_validator("starts_at", "ends_at")
    @classmethod
    def timezone_required(cls, value):
        if value.tzinfo is None or value.utcoffset() is None: raise ValueError("Datetime must include timezone offset")
        return value


@app.post("/calendar/items", status_code=201)
def create_item(data: CalendarCreate, db: Session = Depends(db_session)):
    start, end = data.starts_at.astimezone(timezone.utc), data.ends_at.astimezone(timezone.utc)
    if end <= start: raise HTTPException(422, "ends_at must be after starts_at")
    attendees = sorted(set(data.attendees + [data.owner_id]))
    if data.kind == "meeting":
        overlaps = db.query(CalendarItem).filter(
            CalendarItem.kind == "meeting", CalendarItem.starts_at < end.replace(tzinfo=None),
            CalendarItem.ends_at > start.replace(tzinfo=None)
        ).all()
        conflicts = [item.id for item in overlaps if set(item.attendees.split(",")) & set(attendees)]
        if conflicts: raise HTTPException(409, {"message": "Meeting overlaps an existing meeting", "conflicting_item_ids": conflicts})
    item = CalendarItem(kind=data.kind, title=data.title, owner_id=data.owner_id, team_id=data.team_id,
                        starts_at=start.replace(tzinfo=None), ends_at=end.replace(tzinfo=None), attendees=",".join(attendees))
    db.add(item); db.commit(); db.refresh(item); return item


@app.get("/calendar")
def calendar_view(
    view: Literal["day", "week", "month"],
    at: datetime,
    timezone_name: str = "UTC",
    owner_id: Optional[str] = None,
    team_id: Optional[str] = None,
    db: Session = Depends(db_session),
):
    try: tz = ZoneInfo(timezone_name)
    except Exception: raise HTTPException(422, "Unknown timezone")
    local = at.replace(tzinfo=tz) if at.tzinfo is None else at.astimezone(tz)
    day = local.date()
    if view == "day": start_day = day
    elif view == "week": start_day = day - timedelta(days=day.weekday())
    else: start_day = day.replace(day=1)
    start_local = datetime.combine(start_day, datetime.min.time(), tzinfo=tz)
    if view == "day": end_local = start_local + timedelta(days=1)
    elif view == "week": end_local = start_local + timedelta(days=7)
    else:
        next_month = (start_day.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_local = datetime.combine(next_month, datetime.min.time(), tzinfo=tz)
    q = db.query(CalendarItem).filter(CalendarItem.starts_at < end_local.astimezone(timezone.utc).replace(tzinfo=None), CalendarItem.ends_at >= start_local.astimezone(timezone.utc).replace(tzinfo=None))
    if owner_id: q = q.filter(CalendarItem.owner_id == owner_id)
    if team_id: q = q.filter(CalendarItem.team_id == team_id)
    rows = q.order_by(CalendarItem.starts_at).all()
    return {"view": view, "timezone": timezone_name, "starts_at": start_local, "ends_at": end_local, "items": rows}
