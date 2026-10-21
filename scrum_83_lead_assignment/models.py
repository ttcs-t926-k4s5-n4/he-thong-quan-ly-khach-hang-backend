from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text

from database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, index=True)
    phone = Column(String)
    region = Column(String, index=True)
    industry = Column(String, index=True)
    assigned_to = Column(String, nullable=True, index=True)
    assignment_status = Column(String, nullable=False, default="pending", index=True)
    assigned_by_rule_id = Column(Integer, ForeignKey("assignment_rules.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)


class AssignmentRule(Base):
    __tablename__ = "assignment_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    priority = Column(Integer, nullable=False, unique=True, index=True)
    region = Column(String, nullable=True, index=True)
    industry = Column(String, nullable=True, index=True)
    mode = Column(String, nullable=False, default="fixed")
    assignees = Column(JSON, nullable=False)
    rotation_index = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class AssignmentJob(Base):
    __tablename__ = "assignment_jobs"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="pending", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    error = Column(Text, nullable=True)
    queued_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
