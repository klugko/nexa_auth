from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository

class UserRepositoryImpl(UserRepository):
    async def get_by_email(self, db: AsyncSession, email: str):
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_by_id(self, db: AsyncSession, user_id: UUID):
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()
    
    async def get_by_id(self, db: AsyncSession, user_id: UUID):
        result = await db.execute(
            select(User)
            .options(selectinload(User.roles))  
            .where(User.id == user_id)
        )
        return result.scalars().first()

    async def create(self, db: AsyncSession, user: User):
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    async def set_email_verified(self, db: AsyncSession, user_id, verified: bool) -> None:
        await db.execute(update(User).where(User.id == user_id).values(email_verified=verified))
        await db.commit()

    async def update_profile(self, db: AsyncSession, user: User, *, first_name: Optional[str], last_name: Optional[str], phone: Optional[str], position: Optional[str]) -> User:
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if phone is not None:
            user.phone = phone
        if position is not None:
            user.position = position
        await db.commit()
        await db.refresh(user)
        return user

    async def update_avatar_url(self, db: AsyncSession, user: User, avatar_url: str) -> User:
        user.avatar_url = avatar_url
        await db.commit()
        await db.refresh(user)
        return user
