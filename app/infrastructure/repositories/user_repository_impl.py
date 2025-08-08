from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from sqlalchemy.future import select
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository

class UserRepositoryImpl(UserRepository):
    async def get_by_email(self, db: AsyncSession, email: str):
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_by_id(self, db: AsyncSession, user_id: UUID):
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def create(self, db: AsyncSession, user: User):
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    async def set_email_verified(self, db: AsyncSession, user_id, verified: bool) -> None:
        await db.execute(update(User).where(User.id == user_id).values(email_verified=verified))
        await db.commit()
