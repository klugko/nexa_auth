import uuid
from typing import Optional
from sqlalchemy import String, Integer, SmallInteger, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base

class UserSkill(Base):
    __tablename__ = "user_skills"
    __table_args__ = (
        UniqueConstraint("user_id", "skill", name="uq_user_skill"),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_user_skills_score"),
        CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 100)", name="ck_user_skills_conf"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    skill: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0..100
    category: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)                  
    years_experience_months: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    seniority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)                
    confidence: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)            
    last_used_year: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)       
