from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, root_validator


class LeadCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: Optional[str] = None
    phone: Optional[str] = None
    region: Optional[str] = None
    industry: Optional[str] = None


class LeadOut(LeadCreate):
    id: int
    assigned_to: Optional[str]
    assignment_status: Literal["pending", "assigned", "manual_queue"]
    assigned_by_rule_id: Optional[int]
    created_at: datetime
    assigned_at: Optional[datetime]

    class Config:
        orm_mode = True
        from_attributes = True


class AssignmentRuleInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    priority: int = Field(ge=1)
    region: Optional[str] = None
    industry: Optional[str] = None
    mode: Literal["fixed", "round_robin"] = "fixed"
    assignees: List[str] = Field(min_items=1)

    @root_validator(skip_on_failure=True)
    def validate_rule(cls, values):
        people = [person.strip() for person in values.get("assignees", [])]
        if not people or any(not person for person in people):
            raise ValueError("assignees phải chứa ít nhất một tên hoặc ID hợp lệ")
        if values.get("mode") == "fixed" and len(people) != 1:
            raise ValueError("Rule fixed cần đúng một assignee; dùng round_robin để phân chia cho nhóm")
        values["assignees"] = people
        return values


class AssignmentRuleOut(AssignmentRuleInput):
    id: int

    class Config:
        orm_mode = True
        from_attributes = True


class RuleSet(BaseModel):
    rules: List[AssignmentRuleInput]

    @root_validator(skip_on_failure=True)
    def priorities_are_unique(cls, values):
        priorities = [rule.priority for rule in values.get("rules", [])]
        if len(priorities) != len(set(priorities)):
            raise ValueError("Mỗi rule cần có priority duy nhất")
        return values


class ManualAssignment(BaseModel):
    assignee: str = Field(min_length=1, max_length=200)
