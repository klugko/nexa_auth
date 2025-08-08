from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.domain.entities.auth_provider import AuthProvider
from app.domain.repositories.auth_provider_repository import AuthProviderRepository

class AuthProviderRepositoryImpl(AuthProviderRepository):
    async def get_by_provider_and_user_id(
        self, db: AsyncSession, provider_name: str, provider_user_id: str
    ):
        q = select(AuthProvider).where(
            AuthProvider.provider_name == provider_name,
            AuthProvider.provider_user_id == provider_user_id
        )
        res = await db.execute(q)
        return res.scalars().first()

    async def create(self, db: AsyncSession, entity: AuthProvider):
        db.add(entity)
        await db.commit()
        await db.refresh(entity)
        return entity
