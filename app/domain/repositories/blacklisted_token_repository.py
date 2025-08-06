from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

class BlacklistedTokenRepository:
    async def add(self, db: AsyncSession, token: str) -> None:
        raise NotImplementedError

    async def exists(self, db: AsyncSession, token: str) -> bool:
        raise NotImplementedError
