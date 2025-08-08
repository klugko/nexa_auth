from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.invitation import Invitation

class InvitationRepository:
    async def create(self, db: AsyncSession, entity: Invitation) -> Invitation:
        raise NotImplementedError

    async def get_by_hashed_token(self, db: AsyncSession, hashed_token: str) -> Optional[Invitation]:
        raise NotImplementedError

    async def mark_used(self, db: AsyncSession, entity: Invitation) -> None:
        raise NotImplementedError

    async def cancel(self, db: AsyncSession, entity: Invitation) -> None:
        raise NotImplementedError
