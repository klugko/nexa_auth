from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, delete
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
        await db.execute(insert(user_roles).values(user_id=user_id, role_id=role.id).prefix_with("ON CONFLICT DO NOTHING"))
        await db.commit()

    async def remove_role_from_user(self, db: AsyncSession, user_id, role: Role) -> None:
        await db.execute(delete(user_roles).where(user_roles.c.user_id == user_id, user_roles.c.role_id == role.id))
        await db.commit()

    async def user_has_any(self, db: AsyncSession, user_id, names: list[str]) -> bool:
        if not names:
            return True
        stmt = (
            select(Role.name)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == user_id, Role.name.in_(names))
            .limit(1)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none() is not None
