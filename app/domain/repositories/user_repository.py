from typing import Optional
from app.domain.entities.user import User
from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository:
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        raise NotImplementedError

    async def create(self, db: AsyncSession, user: User) -> User:
        raise NotImplementedError
