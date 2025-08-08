from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.role import Role

class RoleRepository:
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Role]:
        raise NotImplementedError

    async def list_for_user(self, db: AsyncSession, user_id) -> List[Role]:
        raise NotImplementedError

    async def add_role_to_user(self, db: AsyncSession, user_id, role: Role) -> None:
        raise NotImplementedError

    async def remove_role_from_user(self, db: AsyncSession, user_id, role: Role) -> None:
        raise NotImplementedError

    async def user_has_any(self, db: AsyncSession, user_id, names: list[str]) -> bool:
        raise NotImplementedError
