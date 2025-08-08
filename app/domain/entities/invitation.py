import uuid
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base

class Invitation(Base):
    """
    Email invitation with one-time, time-limited token.
    Token stored as SHA-256 hex digest (64 chars). Never store raw token.
    """
    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    inviter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    hashed_token: Mapped[str] = mapped_column(String(500), unique=True, index=True, nullable=False) 
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending") 
    target_type: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)      
    target_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)       
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    @staticmethod
    def default_expiry(minutes: int) -> datetime:
        return datetime.utcnow() + timedelta(minutes=minutes)
