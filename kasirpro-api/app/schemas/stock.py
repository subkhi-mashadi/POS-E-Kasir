from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from decimal import Decimal

class StockResponse(BaseModel):
    product_id: UUID
    variant_id: Optional[UUID] = None
    qty: Decimal
    min_qty: Decimal
    model_config = {"from_attributes": True}

class StockAdjustRequest(BaseModel):
    branch_schema: str
    product_id: UUID
    delta: int
    note: Optional[str] = None

class StockTransferRequest(BaseModel):
    from_schema: str
    to_schema: str
    product_id: UUID
    qty: int
    note: Optional[str] = None

class StockMovementResponse(BaseModel):
    product_id: UUID
    delta: int
    type: str
    note: Optional[str] = None
    model_config = {"from_attributes": True}
