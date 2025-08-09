from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from uuid import UUID
from datetime import datetime

from app.domain.entities.user_resume import UserResume
from app.domain.repositories.user_resume_repository import UserResumeRepository

class UserResumeRepositoryImpl(UserResumeRepository):
    async def create_or_replace(self, db: AsyncSession, user_id: UUID, path: str) -> UserResume:
        await db.execute(delete(UserResume).where(UserResume.user_id == user_id))
        entity = UserResume(user_id=user_id, path=path, parsed_at=None)
        db.add(entity)
        await db.commit()
        await db.refresh(entity)
        return entity

    async def set_parsed_now(self, db: AsyncSession, resume: UserResume) -> None:
        resume.parsed_at = datetime.utcnow()
        await db.commit()
