from sqlalchemy import Column, String, Boolean, Numeric, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMPTZ
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    parent_id = Column(UUID(as_uuid=True), nullable=True)
    sort_order = Column(Integer, default=0)

class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("public.categories.id"), nullable=True)
    base_price = Column(Numeric(12, 2), nullable=False, default=0)
    cost_price = Column(Numeric(12, 2), nullable=True)
    barcode = Column(String(100), unique=True, nullable=True)
    variants = Column(JSON, default=[])
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMPTZ, server_default=func.now())
    updated_at = Column(TIMESTAMPTZ, server_default=func.now(), onupdate=func.now())
