from datetime import datetime
from typing import List, Optional, Tuple
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

    async def set_email_verified(self, db: AsyncSession, user_id, verified: bool) -> None:
        raise NotImplementedError

    async def update_profile(self, db: AsyncSession, user: User, *, first_name: Optional[str], last_name: Optional[str], phone: Optional[str], position: Optional[str]) -> User:
        raise NotImplementedError

    async def update_avatar_url(self, db: AsyncSession, user: User, avatar_url: str) -> User:
        raise NotImplementedError
    
    async def list_paginated(
        self,
        db: AsyncSession,
        *,
        keyword: Optional[str],
        page: int,
        size: int,
        sort_by: str,
        sort_dir: str,
    ) -> Tuple[List[User], int]:
        raise NotImplementedError

    async def update_admin(self, db: AsyncSession, user: User, **fields) -> User:
        raise NotImplementedError

    async def delete_by_id(self, db: AsyncSession, user_id: UUID) -> bool:
        raise NotImplementedError

    async def set_active(self, db: AsyncSession, user: User, active: bool) -> User:
        raise NotImplementedError

    async def revoke_refresh_now(self, db: AsyncSession, user: User) -> User:
        raise NotImplementedError