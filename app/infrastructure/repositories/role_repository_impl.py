from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, delete, and_
from sqlalchemy.future import select

from app.domain.entities.role import Role, user_roles

class RoleRepositoryImpl:
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Role]:
        res = await db.execute(select(Role).where(Role.name == name))
        return res.scalars().first()

    async def list_for_user(self, db: AsyncSession, user_id) -> List[Role]:
        stmt = (
            select(Role)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == user_id)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def add_role_to_user(self, db: AsyncSession, user_id, role: Role) -> None:
        exists_stmt = (
            select(user_roles.c.user_id)
            .where(and_(user_roles.c.user_id == user_id, user_roles.c.role_id == role.id))
            .limit(1)
        )
        res = await db.execute(exists_stmt)
        if res.scalar_one_or_none() is None:
            await db.execute(insert(user_roles).values(user_id=user_id, role_id=role.id))
            await db.commit()

    async def remove_role_from_user(self, db: AsyncSession, user_id, role: Role) -> None:
        await db.execute(
            delete(user_roles).where(
                and_(user_roles.c.user_id == user_id, user_roles.c.role_id == role.id)
            )
        )
        await db.commit()
