from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.user_resume import UserResume
from uuid import UUID

class UserResumeRepository:
    async def create_or_replace(self, db: AsyncSession, user_id: UUID, path: str) -> UserResume:
        raise NotImplementedError
