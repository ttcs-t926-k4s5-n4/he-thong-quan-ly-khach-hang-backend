from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    tax_id = Column(String, unique=True, index=True, nullable=True)

    # Self-referencing relationship for Parent-Child hierarchy
    parent_id = Column(Integer, ForeignKey("customers.id"), nullable=True)

    # Relationships
    children = relationship("Customer", backref="parent", remote_side=[id])
    opportunities = relationship("Opportunity", back_populates="customer")

class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    title = Column(String, nullable=False)
    value = Column(Float, default=0.0) # The contract/opportunity value

    customer = relationship("Customer", back_populates="opportunities")
