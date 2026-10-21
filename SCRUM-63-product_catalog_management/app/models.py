from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    product_type = Column(String, nullable=False) # "One-time" or "Subscription"
    unit = Column(String, nullable=False)         # e.g., "Cái", "Tháng", "Gói"
    list_price = Column(Float, nullable=False)     # Giá niêm yết
    floor_price = Column(Float, nullable=False)    # Giá sàn
    cost_price = Column(Float, nullable=False)     # Giá vốn (Confidential)
    is_active = Column(Boolean, default=True)     # Trạng thái kinh doanh

    # Reference to check if product is used in any quotes
    quote_items = relationship("QuoteItem", back_populates="product")

class QuoteItem(Base):
    """
    Dummy model to represent a line item in a Quote.
    Used to enforce the 'cannot delete if referenced' rule.
    """
    __tablename__ = "quote_items"

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    applied_price = Column(Float, nullable=False)

    product = relationship("Product", back_populates="quote_items")
