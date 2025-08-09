from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.user_score import UserScore

class UserScoreRepository:
    async def get_by_user_id(self, db: AsyncSession, user_id: UUID) -> Optional[UserScore]:
        raise NotImplementedError

    async def upsert(self, db: AsyncSession, user_id: UUID, score: int) -> UserScore:
        raise NotImplementedError
