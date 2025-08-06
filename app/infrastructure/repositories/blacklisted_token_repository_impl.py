from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.domain.entities.black_listed_token import BlacklistedToken
from app.domain.repositories.blacklisted_token_repository import BlacklistedTokenRepository

class BlacklistedTokenRepositoryImpl(BlacklistedTokenRepository):
    async def add(self, db: AsyncSession, token: str) -> None:
        try:
            db.add(BlacklistedToken(token=token))
            await db.commit()
        except IntegrityError:
            await db.rollback()  
        except Exception:
            await db.rollback()
            raise

    async def exists(self, db: AsyncSession, token: str) -> bool:
        result = await db.execute(select(BlacklistedToken).where(BlacklistedToken.token == token))
        return result.scalars().first() is not None
