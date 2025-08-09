import uuid
from datetime import datetime
from sqlalchemy import DateTime, SmallInteger, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base

class UserScore(Base):
    """
    Score agrégé utilisateur (0..100), recalculable à la demande.
    Clé primaire = user_id (1-1).
    """
    __tablename__ = "user_scores"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_scores_user"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    score: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)  # 0..100
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
