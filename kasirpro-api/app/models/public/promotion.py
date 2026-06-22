from sqlalchemy import Column, String, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMPTZ
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Promotion(Base):
    __tablename__ = "promotions"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)   # percentage | fixed | buy_x_get_y
    conditions = Column(JSON, default={})
    discount_value = Column(Numeric(10, 2), nullable=False)
    start_at = Column(TIMESTAMPTZ, nullable=False)
    end_at = Column(TIMESTAMPTZ, nullable=False)
    created_at = Column(TIMESTAMPTZ, server_default=func.now())
