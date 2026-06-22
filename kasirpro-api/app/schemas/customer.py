from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional

class CustomerCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    branch_id: Optional[UUID] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class CustomerResponse(BaseModel):
    id: UUID
    name: str
    phone: Optional[str]
    email: Optional[str]
    points: int
    tier: str
    model_config = {"from_attributes": True}
