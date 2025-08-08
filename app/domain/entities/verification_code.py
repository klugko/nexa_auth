import uuid
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base

class VerificationCode(Base):
    """
    One-time verification code (only SHA-256 hex digest stored).
    type: e.g. 'PHONE'
    """
    __tablename__ = "verification_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # 'PHONE'
    hashed_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # sha256 hex
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    @staticmethod
    def default_expiry(minutes: int) -> datetime:
        return datetime.utcnow() + timedelta(minutes=minutes)
