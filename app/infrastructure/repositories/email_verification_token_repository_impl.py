from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.domain.entities.email_verification_token import EmailVerificationToken
from app.domain.repositories.email_verification_token_repository import EmailVerificationTokenRepository

class EmailVerificationTokenRepositoryImpl(EmailVerificationTokenRepository):
    async def create(self, db: AsyncSession, entity: EmailVerificationToken) -> EmailVerificationToken:
        db.add(entity)
        await db.commit()
        await db.refresh(entity)
        return entity

    async def get_by_hashed_token(self, db: AsyncSession, hashed_token: str):
        res = await db.execute(select(EmailVerificationToken).where(EmailVerificationToken.hashed_token == hashed_token))
        return res.scalars().first()

    async def mark_used(self, db: AsyncSession, entity: EmailVerificationToken) -> None:
        entity.used_at = datetime.utcnow()
        await db.commit()
