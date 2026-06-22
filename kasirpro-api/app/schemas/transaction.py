from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

class TransactionItemCreate(BaseModel):
    product_id: UUID
    variant_id: Optional[UUID] = None
    qty: int
    unit_price: Decimal
    discount: Decimal = Decimal("0")
    subtotal: Decimal

class TransactionCreate(BaseModel):
    branch_schema: str = "public"
    local_id: UUID
    cashier_id: UUID
    customer_id: Optional[UUID] = None
    items: List[TransactionItemCreate]
    subtotal: Decimal
    discount: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")
    total: Decimal
    payment_method: str  # cash|qris|transfer|debit|credit|split
    payment_detail: dict = {}
    created_at: Optional[str] = None

class TransactionResponse(BaseModel):
    id: UUID
    local_id: UUID
    invoice_no: str
    total: Decimal
    sync_status: str
    model_config = {"from_attributes": True}

class SyncTransactionRequest(BaseModel):
    branch_schema: str = "public"
    transactions: List[TransactionCreate]
