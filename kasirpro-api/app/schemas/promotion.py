from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

class PromotionCreate(BaseModel):
    name: str
    type: str  # percentage | fixed | buy_x_get_y
    conditions: dict = {}
    discount_value: Decimal
    start_at: datetime
    end_at: datetime

class PromotionResponse(BaseModel):
    id: UUID
    name: str
    type: str
    conditions: dict
    discount_value: Decimal
    start_at: datetime
    end_at: datetime
    model_config = {"from_attributes": True}

class ApplyPromotionRequest(BaseModel):
    subtotal: float
    items: List[dict] = []
