from datetime import datetime
from sqlalchemy import DateTime, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base

class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(Text, nullable=False)  
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    ) 
    __table_args__ = (
        Index("ux_blacklisted_tokens_token", "token", unique=True),
    )
