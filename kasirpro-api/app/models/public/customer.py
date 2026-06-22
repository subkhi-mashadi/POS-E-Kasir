from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import TIMESTAMPTZ
import uuid
from app.core.database import Base

class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), unique=True, nullable=True)
    email = Column(String(255), nullable=True)
    points = Column(Integer, default=0)
    tier = Column(String(20), default="bronze")  # bronze|silver|gold|platinum
    branch_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(TIMESTAMPTZ, server_default=func.now())
