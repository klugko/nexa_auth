from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.user_resume import UserResume

class UserResumeRepository:
    async def create_or_replace(self, db: AsyncSession, user_id: UUID, path: str) -> UserResume:
        raise NotImplementedError

    async def set_parsed_now(self, db: AsyncSession, resume: UserResume) -> None:
        raise NotImplementedError

    async def get_latest_for_user(self, db: AsyncSession, user_id: UUID) -> Optional[UserResume]:
        raise NotImplementedError
