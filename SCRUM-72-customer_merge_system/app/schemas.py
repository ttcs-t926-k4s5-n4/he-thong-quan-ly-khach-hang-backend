from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Basic Customer Schema
class CustomerBase(BaseModel):
    name: str
    tax_id: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int

    class Config:
        from_attributes = True

# Related Entities Schemas
class ContactSchema(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True

class OpportunitySchema(BaseModel):
    id: int
    title: str
    value: Optional[float] = None
    stage: Optional[str] = None

    class Config:
        from_attributes = True

class ActivitySchema(BaseModel):
    id: int
    activity_type: str
    description: Optional[str] = None
    date: datetime

    class Config:
        from_attributes = True

# Comprehensive View for side-by-side comparison
class CustomerDetail(Customer):
    contacts: List[ContactSchema] = []
    opportunities: List[OpportunitySchema] = []
    activities: List[ActivitySchema] = []

# Merge Request Schema
class MergeRequest(BaseModel):
    source_customer_id: int # The one to be deleted/merged from
    target_customer_id: int # The one to be kept
