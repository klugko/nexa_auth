from datetime import datetime
from typing import Optional
from uuid import UUID
from app.domain.entities.user_resume import UserResume
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domain.entities.user_score import UserScore
from app.domain.repositories.user_score_repository import UserScoreRepository

class UserScoreRepositoryImpl(UserScoreRepository):
    async def get_by_user_id(self, db: AsyncSession, user_id: UUID) -> Optional[UserScore]:
        res = await db.execute(select(UserScore).where(UserScore.user_id == user_id))
        return res.scalars().first()

    async def upsert(self, db: AsyncSession, user_id: UUID, score: int) -> UserScore:
        entity = await self.get_by_user_id(db, user_id)
        if entity:
            entity.score = int(score)
            entity.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(entity)
            return entity
        entity = UserScore(user_id=user_id, score=int(score), updated_at=datetime.utcnow())
        db.add(entity)
        await db.commit()
        await db.refresh(entity)
        return entity
    
    async def get_latest_for_user(self, db: AsyncSession, user_id: UUID) -> Optional[UserResume]:
        res = await db.execute(
            select(UserResume).where(UserResume.user_id == user_id).order_by(desc(UserResume.parsed_at.nullslast()), desc(UserResume.id)).limit(1)
        )
        return res.scalars().first()
