from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.domain.entities.black_listed_token import BlacklistedToken
from app.domain.repositories.blacklisted_token_repository import BlacklistedTokenRepository

class BlacklistedTokenRepositoryImpl(BlacklistedTokenRepository):
    async def add(self, db: AsyncSession, token: str) -> None:
        """
        Insert token into blacklist. Idempotent thanks to ON CONFLICT DO NOTHING.
        """
        stmt = pg_insert(BlacklistedToken).values(token=token)
        stmt = stmt.on_conflict_do_nothing(index_elements=["token"])
        await db.execute(stmt)
        await db.commit()

    async def exists(self, db: AsyncSession, token: str) -> bool:
        result = await db.execute(
            select(BlacklistedToken.id).where(BlacklistedToken.token == token)
        )
        return result.scalar_one_or_none() is not None
