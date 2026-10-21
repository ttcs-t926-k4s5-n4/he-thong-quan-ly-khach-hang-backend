from pydantic import BaseModel
from typing import List, Optional

class OpportunityBase(BaseModel):
    title: str
    value: float

class Opportunity(OpportunityBase):
    id: int
    customer_id: int

    class Config:
        from_attributes = True

class CustomerBase(BaseModel):
    name: str
    tax_id: Optional[str] = None
    parent_id: Optional[int] = None

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int

    class Config:
        from_attributes = True

class HierarchyResponse(BaseModel):
    customer_id: int
    name: str
    total_group_value: float
    child_count: int
