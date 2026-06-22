from sqlalchemy import Column, String, Numeric, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMPTZ
import uuid
from app.core.database import Base

def make_transaction_model(schema: str):
    class Transaction(Base):
        __tablename__ = "transactions"
        __table_args__ = {"schema": schema}

        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        local_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
        invoice_no = Column(String(50))
        cashier_id = Column(UUID(as_uuid=True), nullable=False)
        customer_id = Column(UUID(as_uuid=True), nullable=True)
        subtotal = Column(Numeric(12, 2), default=0)
        discount = Column(Numeric(12, 2), default=0)
        tax = Column(Numeric(12, 2), default=0)
        total = Column(Numeric(12, 2), default=0)
        payment_method = Column(String(50))  # cash|qris|transfer|debit|credit|split
        payment_detail = Column(JSON, default={})
        sync_status = Column(String(20), default="synced")  # pending_sync|synced|failed
        synced_at = Column(TIMESTAMPTZ, nullable=True)
        created_at = Column(TIMESTAMPTZ, nullable=False)
    return Transaction
