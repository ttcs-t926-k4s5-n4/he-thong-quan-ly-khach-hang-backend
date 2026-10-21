from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    phone = Column(String, index=True)
    company_name = Column(String, index=True)
    full_name = Column(String)
    is_merged = Column(Boolean, default=False)
    merged_into_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    history = relationship("LeadHistory", back_populates="lead")

class LeadHistory(Base):
    __tablename__ = "lead_history"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    action = Column(String)  # e.g., "Call", "Email", "Note"
    details = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="history")

class MergeLog(Base):
    __tablename__ = "merge_logs"

    id = Column(Integer, primary_key=True, index=True)
    source_lead_id = Column(Integer)
    target_lead_id = Column(Integer)
    merged_at = Column(DateTime, default=datetime.utcnow)
    merged_by = Column(String)


