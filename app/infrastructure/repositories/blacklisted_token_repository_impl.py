from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domain.entities.black_listed_token import BlacklistedToken
from app.domain.repositories.blacklisted_token_repository import BlacklistedTokenRepository

class BlacklistedTokenRepositoryImpl(BlacklistedTokenRepository):
    async def add(self, db: AsyncSession, token: str) -> None:
        db.add(BlacklistedToken(token=token))
        await db.commit()

    async def exists(self, db: AsyncSession, token: str) -> bool:
        result = await db.execute(select(BlacklistedToken).where(BlacklistedToken.token == token))
        return result.scalars().first() is not None
