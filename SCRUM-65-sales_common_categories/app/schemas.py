from pydantic import BaseModel
from typing import List, Optional

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True

# CategoryValue Schemas
class CategoryValueBase(BaseModel):
    value: str
    display_order: int = 0

class CategoryValueCreate(CategoryValueBase):
    category_id: int

class CategoryValue(CategoryValueBase):
    id: int
    category_id: int

    class Config:
        from_attributes = True

# Response types
class CategoryWithValues(Category):
    values: List[CategoryValue] = []
