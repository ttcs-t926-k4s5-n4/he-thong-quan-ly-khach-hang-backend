from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint

from database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, index=True)
    phone = Column(String)
    company_name = Column(String)
    industry = Column(String, index=True)
    company_size = Column(String, index=True)
    source = Column(String, index=True)
    interest_level = Column(String, index=True)
    score = Column(Float, nullable=False, default=0, index=True)
    score_category = Column(String, nullable=False, default="cold", index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScoreRule(Base):
    __tablename__ = "score_rules"
    __table_args__ = (UniqueConstraint("criterion", "value", name="uq_score_rule_criterion_value"),)

    id = Column(Integer, primary_key=True)
    criterion = Column(String, nullable=False, index=True)
    value = Column(String, nullable=False)
    points = Column(Float, nullable=False)


class ScoreThreshold(Base):
    __tablename__ = "score_thresholds"

    id = Column(Integer, primary_key=True, default=1)
    hot_min = Column(Float, nullable=False, default=70)
    warm_min = Column(Float, nullable=False, default=40)
