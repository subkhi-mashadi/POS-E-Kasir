from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class Branch(Base):
    __tablename__ = "branches"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    schema_name = Column(String(100), unique=True, nullable=False)
    address = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
