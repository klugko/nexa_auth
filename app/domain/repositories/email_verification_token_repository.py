from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.email_verification_token import EmailVerificationToken

class EmailVerificationTokenRepository:
    async def create(self, db: AsyncSession, entity: EmailVerificationToken) -> EmailVerificationToken:
        raise NotImplementedError

    async def get_by_hashed_token(self, db: AsyncSession, hashed_token: str) -> Optional[EmailVerificationToken]:
        raise NotImplementedError

    async def mark_used(self, db: AsyncSession, entity: EmailVerificationToken) -> None:
        raise NotImplementedError
