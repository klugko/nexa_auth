from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.infrastructure.repositories.role_repository_impl import RoleRepositoryImpl

role_repo = RoleRepositoryImpl()

class RbacUseCases:
    async def add_role(self, db: AsyncSession, user, role_name: str):
        role = await role_repo.get_by_name(db, role_name)
        if not role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rôle inconnu")
        await role_repo.add_role_to_user(db, user.id, role)

    async def remove_role(self, db: AsyncSession, user, role_name: str):
        role = await role_repo.get_by_name(db, role_name)
        if not role:
            return
        await role_repo.remove_role_from_user(db, user.id, role)
