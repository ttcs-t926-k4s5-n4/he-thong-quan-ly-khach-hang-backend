from sqlalchemy import Column, Integer, String
from .database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    tax_id = Column(String, unique=True, index=True, nullable=True)
    website = Column(String, nullable=True)
    phone = Column(String, nullable=True)
