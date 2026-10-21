from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class LeadBase(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    full_name: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(LeadBase):
    pass

class LeadOut(LeadBase):
    id: int
    is_merged: bool
    merged_into_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

class LeadHistoryBase(BaseModel):
    action: str
    details: str

class LeadHistoryCreate(LeadHistoryBase):
    pass

class LeadHistoryOut(LeadHistoryBase):
    id: int
    lead_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MergeRequest(BaseModel):
    source_lead_id: int
    target_lead_id: int
    merged_by: str


