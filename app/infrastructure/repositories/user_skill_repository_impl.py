from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.domain.entities.user_skill import UserSkill
from app.domain.repositories.user_skill_repository import UserSkillRepository

class UserSkillRepositoryImpl(UserSkillRepository):
    async def upsert_bulk(self, db: AsyncSession, user_id: UUID, items: list[tuple[str, int]]) -> None:
        await db.execute(delete(UserSkill).where(UserSkill.user_id == user_id))
        for skill, score in items:
            db.add(UserSkill(user_id=user_id, skill=skill, score=int(score)))
        await db.commit()

    async def list_for_user(self, db: AsyncSession, user_id: UUID) -> List[UserSkill]:
        res = await db.execute(select(UserSkill).where(UserSkill.user_id == user_id).order_by(UserSkill.score.desc(), UserSkill.skill.asc()))
        return list(res.scalars().all())
