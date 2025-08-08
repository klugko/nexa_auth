import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.db.base import Base
from app.domain.entities.role import user_roles, Role


class User(Base):
    """
    User entity representing application users.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False) 
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)        
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)    
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    refresh_revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True) 
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)  # NEW
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    auth_providers = relationship("AuthProvider", back_populates="user", cascade="all, delete-orphan")
