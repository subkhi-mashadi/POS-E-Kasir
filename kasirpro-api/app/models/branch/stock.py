from sqlalchemy import Column, String, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMPTZ
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Stock(Base):
    __tablename__ = "stock"
    __table_args__ = {"schema": "branch_template"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    variant_id = Column(UUID(as_uuid=True), nullable=True)
    qty = Column(Numeric(10, 2), default=0)
    min_qty = Column(Numeric(10, 2), default=5)
    location = Column(String(100), nullable=True)

class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = {"schema": "branch_template"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    delta = Column(Integer, nullable=False)
    type = Column(String(50), nullable=False)  # sale|purchase|adjustment|transfer_in|transfer_out|void
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    note = Column(String(500), nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(TIMESTAMPTZ, server_default=func.now())
