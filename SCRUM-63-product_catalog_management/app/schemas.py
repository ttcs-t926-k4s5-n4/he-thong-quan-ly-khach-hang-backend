from pydantic import BaseModel, Field
from typing import Optional, List

# Base schema for Product
class ProductBase(BaseModel):
    code: str
    name: str
    product_type: str = Field(..., description="One-time or Subscription")
    unit: str
    list_price: float
    floor_price: float
    is_active: bool = True

# Schema for creating a product (including cost_price)
class ProductCreate(ProductBase):
    cost_price: float

# Schema for updating a product
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    product_type: Optional[str] = None
    unit: Optional[str] = None
    list_price: Optional[float] = None
    floor_price: Optional[float] = None
    cost_price: Optional[float] = None
    is_active: Optional[bool] = None

# Public response schema (No cost_price)
class Product(ProductBase):
    id: int

    class Config:
        from_attributes = True

# Admin response schema (Includes cost_price)
class ProductAdmin(Product):
    cost_price: float

# Schema for Quote items (simulated)
class QuoteItemCreate(BaseModel):
    quote_id: int
    product_id: int
    quantity: int
    applied_price: float
