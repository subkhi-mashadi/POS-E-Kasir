from sqlalchemy import Column, String, Numeric
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMPTZ
import uuid
from app.core.database import Base

class Shift(Base):
    __tablename__ = "shifts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cashier_id = Column(UUID(as_uuid=True), nullable=False)
    opening_cash = Column(Numeric(12, 2), default=0)
    closing_cash = Column(Numeric(12, 2), nullable=True)
    opened_at = Column(TIMESTAMPTZ, nullable=False)
    closed_at = Column(TIMESTAMPTZ, nullable=True)
    status = Column(String(20), default="open")  # open|closed
