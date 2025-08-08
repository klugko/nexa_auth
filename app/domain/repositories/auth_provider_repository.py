from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.auth_provider import AuthProvider

class AuthProviderRepository:
    async def get_by_provider_and_user_id(
        self, db: AsyncSession, provider_name: str, provider_user_id: str
    ) -> Optional[AuthProvider]:
        raise NotImplementedError

    async def create(self, db: AsyncSession, entity: AuthProvider) -> AuthProvider:
        raise NotImplementedError
