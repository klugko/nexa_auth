from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl

user_repo = UserRepositoryImpl()

class UserUseCases:
    async def get_by_id(self, db: AsyncSession, user_id: UUID):
        return await user_repo.get_by_id(db, user_id)
