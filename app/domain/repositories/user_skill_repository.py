from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.domain.entities.user_skill import UserSkill

class UserSkillRepository:
    async def upsert_bulk(self, db: AsyncSession, user_id: UUID, items: list[tuple[str, int]]) -> None:
        raise NotImplementedError

    async def list_for_user(self, db: AsyncSession, user_id: UUID) -> List[UserSkill]:
        raise NotImplementedError
