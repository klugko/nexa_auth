from typing import Optional

from fastapi import HTTPException, status
from app.infrastructure.security.password_hash import hash_password, verify_password
from app.infrastructure.security.jwt_service import JWTService
from app.domain.entities.user import User
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.blacklisted_token_repository_impl import BlacklistedTokenRepositoryImpl

jwt_service = JWTService()
user_repo = UserRepositoryImpl()
blacklist_repo = BlacklistedTokenRepositoryImpl()


class AuthUseCases:
    async def register(self, db: AsyncSession, email: str, password: str, first_name: Optional[str] = None,
                       last_name: Optional[str] = None):
        existing_user = await user_repo.get_by_email(db, email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Cet utilisateur existe déjà")
        user = User(
            email=email,
            hashed_password=hash_password(password),
            first_name=first_name,
            last_name=last_name
        )
        return await user_repo.create(db, user)

    async def login(self, db: AsyncSession, email: str, password: str):
        user = await user_repo.get_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Email ou mot de passe invalide")
        access_token = jwt_service.create_access_token(str(user.id))
        refresh_token = jwt_service.create_refresh_token(str(user.id))
        return access_token, refresh_token

    
    async def logout(self, db: AsyncSession, refresh_token: str):
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token manquant")
        try:
            await blacklist_repo.add(db, refresh_token)
            return {"message": "Déconnexion réussie"}
        except Exception:
            raise HTTPException(status_code=500, detail="Erreur interne lors de la déconnexion")
        
        
    async def refresh(self, db: AsyncSession, refresh_token: str):
        if await blacklist_repo.exists(db, refresh_token):
            raise HTTPException(status_code=401, detail="Token invalide")
        try:
            payload = jwt_service.decode_token(refresh_token)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Token invalide")
            return jwt_service.create_access_token(user_id)
        except Exception:
            raise HTTPException(status_code=401, detail="Token invalide")