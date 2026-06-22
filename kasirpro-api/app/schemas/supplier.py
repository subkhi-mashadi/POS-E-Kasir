from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List

class SupplierCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True

class SupplierResponse(BaseModel):
    id: UUID
    name: str
    phone: Optional[str]
    address: Optional[str]
    is_active: bool
    model_config = {"from_attributes": True}

class PurchaseOrderItem(BaseModel):
    product_id: str
    qty: int
    unit_cost: float

class PurchaseOrderCreate(BaseModel):
    items: List[PurchaseOrderItem]

    def model_dump(self, **kwargs):
        d = super().model_dump(**kwargs)
        d["items"] = [i if isinstance(i, dict) else i for i in d["items"]]
        return d
