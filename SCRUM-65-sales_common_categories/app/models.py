from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)  # e.g., "Ngành nghề khách hàng"
    description = Column(String, nullable=True)

    values = relationship("CategoryValue", back_populates="category", cascade="all, delete-orphan")

class CategoryValue(Base):
    __tablename__ = "category_values"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    value = Column(String, nullable=False)
    display_order = Column(Integer, default=0)

    category = relationship("Category", back_populates="values")
    # This relationship is used to check for references during deletion
    referenced_by_leads = relationship("Lead", back_populates="category_value")

class Lead(Base):
    """
    Dummy model to simulate a Lead entity that references a category value.
    In a real system, this would be your actual Lead table.
    """
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    # Reference to the specific category value
    industry_value_id = Column(Integer, ForeignKey("category_values.id"), nullable=True)

    category_value = relationship("CategoryValue", back_populates="referenced_by_leads", foreign_keys=[industry_value_id])
