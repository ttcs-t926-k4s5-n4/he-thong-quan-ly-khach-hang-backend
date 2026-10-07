from pydantic import BaseModel
from typing import List, Optional

class CustomerImportRow(BaseModel):
    row_index: int
    name: str
    tax_id: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    status: str = "valid" # "valid", "duplicate", "error"
    error_message: Optional[str] = None
    existing_id: Optional[int] = None

class ImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows: int
    duplicate_rows: int
    error_rows: int
    rows: List[CustomerImportRow]

class ImportConfirmRequest(BaseModel):
    rows: List[int] # List of row indices to import
