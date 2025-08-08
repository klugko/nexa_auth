from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from sqlalchemy.future import select
from app.domain.entities.password_reset_token import PasswordResetToken
from app.domain.repositories.password_reset_token_repository import PasswordResetTokenRepository

class PasswordResetTokenRepositoryImpl(PasswordResetTokenRepository):
    async def create(self, db: AsyncSession, entity: PasswordResetToken) -> PasswordResetToken:
        db.add(entity)
        await db.commit()
        await db.refresh(entity)
        return entity

    async def get_by_hashed_token(self, db: AsyncSession, hashed_token: str):
        res = await db.execute(select(PasswordResetToken).where(PasswordResetToken.hashed_token == hashed_token))
        return res.scalars().first()

    async def mark_used(self, db: AsyncSession, entity: PasswordResetToken) -> None:
        entity.used_at = datetime.utcnow()
        await db.commit()

    async def delete_expired(self, db: AsyncSession) -> int:
        q = delete(PasswordResetToken).where(PasswordResetToken.expires_at < datetime.utcnow())
        res = await db.execute(q)
        await db.commit()
        return res.rowcount or 0
