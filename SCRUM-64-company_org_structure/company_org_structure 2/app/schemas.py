from pydantic import BaseModel
from typing import List, Optional

class AreaBase(BaseModel):
    name: str

class AreaCreate(AreaBase):
    pass

class Area(AreaBase):
    id: int
    class Config:
        from_attributes = True

class EmployeeBase(BaseModel):
    name: str
    role: str
    group_id: Optional[int] = None

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase):
    id: int
    class Config:
        from_attributes = True

class GroupBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    lead_id: Optional[int] = None
    area_id: Optional[int] = None

class GroupCreate(GroupBase):
    pass

class Group(GroupBase):
    id: int
    class Config:
        from_attributes = True

class DataScopeResponse(BaseModel):
    team_lead_id: int
    group_name: str
    accessible_group_ids: List[int]
    accessible_employee_ids: List[int]
