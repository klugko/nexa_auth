from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.password_reset_token import PasswordResetToken

class PasswordResetTokenRepository:
    async def create(self, db: AsyncSession, entity: PasswordResetToken) -> PasswordResetToken:
        raise NotImplementedError

    async def get_by_hashed_token(self, db: AsyncSession, hashed_token: str) -> Optional[PasswordResetToken]:
        raise NotImplementedError

    async def mark_used(self, db: AsyncSession, entity: PasswordResetToken) -> None:
        raise NotImplementedError

    async def delete_expired(self, db: AsyncSession) -> int:
        raise NotImplementedError
