from fastapi.security import HTTPBearer
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from jose import jwt
from datetime import datetime, timedelta
from app.config import settings

bearer_scheme = HTTPBearer()

class JWTService:
    def __init__(self):
        with open(settings.jwt_private_key_path, "rb") as f:
            self.private_key = f.read()
        with open(settings.jwt_public_key_path, "rb") as f:
            self.public_key = f.read()

    def create_token(self, subject: str, expires_delta: timedelta) -> str:
        to_encode = {
            "sub": subject,
            "exp": datetime.utcnow() + expires_delta,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(to_encode, self.private_key, algorithm=settings.jwt_algorithm)

    def create_access_token(self, subject: str) -> str:
        return self.create_token(subject, timedelta(minutes=settings.jwt_access_token_expire_minutes))

    def create_refresh_token(self, subject: str) -> str:
        return self.create_token(subject, timedelta(days=settings.jwt_refresh_token_expire_days))

    def decode_token(self, token: str):
        return jwt.decode(token, self.public_key, algorithms=[settings.jwt_algorithm])

    async def get_current_user(
        self,
        credentials = Depends(bearer_scheme),
        db: AsyncSession = Depends(get_db)
    ):
        token = credentials.credentials
        try:
            payload = self.decode_token(token)
            user_id: str = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Token invalide")
            user = await UserRepositoryImpl().get_by_id(db, int(user_id))
            if not user:
                raise HTTPException(status_code=404, detail="Utilisateur introuvable")
            return user
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="Token invalide ou expiré")
