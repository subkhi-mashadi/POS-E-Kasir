from sqlalchemy import Column, String, Boolean, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id = Column(UUID(as_uuid=True), nullable=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("superadmin", "admin_cabang", "supervisor", "kasir", name="user_role"), nullable=False)
    permissions = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
