from pydantic import BaseModel, Field


class RoleOut(BaseModel):
    id: int
    code: str
    name: str

    model_config = {"from_attributes": True}


class BusinessGroupOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    roles: list[RoleOut] = []
    business_group: BusinessGroupOut | None = None

    model_config = {"from_attributes": True}


class RoleAssignmentIn(BaseModel):
    role_ids: list[int] = Field(default_factory=list)
    business_group_id: int | None = None
