from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import datetime

class CategoryCreate(BaseModel):
    name: str
    parent_id: Optional[UUID] = None
    sort_order: int = 0

class CategoryResponse(BaseModel):
    id: UUID
    name: str
    parent_id: Optional[UUID]
    sort_order: int
    model_config = {"from_attributes": True}

class ProductCreate(BaseModel):
    sku: str
    name: str
    category_id: Optional[UUID] = None
    base_price: Decimal
    cost_price: Optional[Decimal] = None
    barcode: Optional[str] = None
    variants: List[dict] = []
    image_url: Optional[str] = None
    is_active: bool = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[UUID] = None
    base_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    barcode: Optional[str] = None
    variants: Optional[List[dict]] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class ProductResponse(BaseModel):
    id: UUID
    sku: str
    name: str
    category_id: Optional[UUID]
    base_price: Decimal
    cost_price: Optional[Decimal]
    barcode: Optional[str]
    variants: List[dict]
    image_url: Optional[str]
    is_active: bool
    updated_at: Optional[datetime]
    model_config = {"from_attributes": True}

class PaginatedProducts(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    per_page: int
