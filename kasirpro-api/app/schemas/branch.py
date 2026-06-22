from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class BranchCreate(BaseModel):
    name: str
    code: str
    schema_name: str
    address: Optional[str] = None
    is_active: bool = True

class BranchResponse(BaseModel):
    id: UUID
    name: str
    code: str
    schema_name: str
    address: Optional[str]
    is_active: bool
    model_config = {"from_attributes": True}
