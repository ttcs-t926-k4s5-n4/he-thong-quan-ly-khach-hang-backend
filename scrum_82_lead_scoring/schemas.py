from datetime import datetime
from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field, root_validator

CRITERIA = {"industry", "company_size", "source", "interest_level"}


class LeadInput(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    source: Optional[str] = None
    interest_level: Optional[str] = None


class LeadCreate(LeadInput):
    pass


class LeadUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    email: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    source: Optional[str] = None
    interest_level: Optional[str] = None


class LeadOut(LeadInput):
    id: int
    score: float
    score_category: Literal["hot", "warm", "cold"]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class ScoreConfig(BaseModel):
    rules: Dict[str, Dict[str, float]]
    hot_min: float = Field(default=70, ge=0)
    warm_min: float = Field(default=40, ge=0)

    @root_validator(skip_on_failure=True)
    def validate_config(cls, values):
        rules = values.get("rules", {})
        unknown = set(rules) - CRITERIA
        if unknown:
            raise ValueError(f"Tiêu chí không hỗ trợ: {', '.join(sorted(unknown))}")
        if values.get("warm_min", 0) > values.get("hot_min", 0):
            raise ValueError("warm_min phải nhỏ hơn hoặc bằng hot_min")
        return values


class ScoreConfigOut(ScoreConfig):
    pass
