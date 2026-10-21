from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    tax_id = Column(String, index=True, nullable=True) # Mã số thuế
    website = Column(String, index=True, nullable=True)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    contacts = relationship("Contact", back_populates="customer", cascade="all, delete-orphan")
    opportunities = relationship("Opportunity", back_populates="customer", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="customer", cascade="all, delete-orphan")

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    customer = relationship("Customer", back_populates="contacts")

class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    title = Column(String, nullable=False)
    value = Column(Float, nullable=True)
    stage = Column(String, nullable=True)

    customer = relationship("Customer", back_populates="opportunities")

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    activity_type = Column(String, nullable=False) # e.g., Call, Email, Meeting
    description = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)

    customer = relationship("Customer", back_populates="activities")
