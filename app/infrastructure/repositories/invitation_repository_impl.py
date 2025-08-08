from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.domain.entities.invitation import Invitation
from app.domain.repositories.invitation_repository import InvitationRepository

class InvitationRepositoryImpl(InvitationRepository):
    async def create(self, db: AsyncSession, entity: Invitation) -> Invitation:
        db.add(entity)
        await db.commit()
        await db.refresh(entity)
        return entity

    async def get_by_hashed_token(self, db: AsyncSession, hashed_token: str):
        res = await db.execute(select(Invitation).where(Invitation.hashed_token == hashed_token))
        return res.scalars().first()

    async def mark_used(self, db: AsyncSession, entity: Invitation) -> None:
        entity.status = "accepted"
        entity.used_at = datetime.utcnow()
        await db.commit()

    async def cancel(self, db: AsyncSession, entity: Invitation) -> None:
        entity.status = "cancelled"
        await db.commit()
