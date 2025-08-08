from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.user import User

class UserRepository:
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        raise NotImplementedError

    async def get_by_id(self, db: AsyncSession, user_id: UUID) -> Optional[User]:
        raise NotImplementedError

    async def create(self, db: AsyncSession, user: User) -> User:
        raise NotImplementedError
