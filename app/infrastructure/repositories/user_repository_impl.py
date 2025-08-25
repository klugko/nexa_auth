from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_, update
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository

class UserRepositoryImpl(UserRepository):
    async def get_by_email(self, db: AsyncSession, email: str):
        result = await db.execute(select(User).where(User.email == email))
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
        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user.id)
        )
        return result.scalars().first()
    
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
        stmt = select(User).options(selectinload(User.roles))
        cnt_stmt = select(func.count()).select_from(User)

        # Filtres
        if keyword:
            kw = f"%{keyword.lower()}%"
            cond = or_(
                func.lower(User.email).like(kw),
                func.lower(User.first_name).like(kw),
                func.lower(User.last_name).like(kw),
                User.phone.ilike(f"%{keyword}%"),
            )
            stmt = stmt.where(cond)
            cnt_stmt = cnt_stmt.where(cond)

        # Tri
        colmap = {
            "created_at": User.created_at,
            "email": User.email,
            "first_name": User.first_name,
            "last_name": User.last_name,
        }
        sort_col = colmap.get(sort_by, User.created_at)
        order_expr = sort_col.desc() if sort_dir == "desc" else sort_col.asc()
        stmt = stmt.order_by(order_expr)

        # Pagination
        offset = (page - 1) * size
        stmt = stmt.limit(size).offset(offset)

        # Exécution
        res_items = await db.execute(stmt)
        items = list(res_items.scalars().unique().all()) 
        res_cnt = await db.execute(cnt_stmt)
        total = int(res_cnt.scalar_one())

        return items, total

    async def update_admin(self, db: AsyncSession, user: User, **fields) -> User:
        for k, v in fields.items():
            setattr(user, k, v)
        await db.commit()
        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user.id)
        )
        return result.scalars().first()

    async def delete_by_id(self, db: AsyncSession, user_id: UUID) -> bool:
        res = await db.execute(select(User).where(User.id == user_id))
        u = res.scalars().first()
        if not u:
            return False
        await db.delete(u)
        await db.commit()
        return True
    
    async def set_active(self, db: AsyncSession, user: User, active: bool) -> User:
        user.is_active = active
        if not active:
            user.refresh_revoked_at = datetime.utcnow()
        await db.commit()
        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user.id)
        )
        return result.scalars().first()

    async def revoke_refresh_now(self, db: AsyncSession, user: User) -> User:
        user.refresh_revoked_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        return user
