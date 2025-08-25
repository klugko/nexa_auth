from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl

user_repo = UserRepositoryImpl()

class AdminUserStatusUseCases:
    async def activate(self, db: AsyncSession, user_id: UUID):
        user = await user_repo.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
        return await user_repo.set_active(db, user, True)  

    async def deactivate(self, db: AsyncSession, user_id: UUID):
        user = await user_repo.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
        return await user_repo.set_active(db, user, False) 
