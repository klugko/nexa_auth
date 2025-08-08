from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, desc, and_
from app.domain.entities.verification_code import VerificationCode
from app.domain.repositories.verification_code_repository import VerificationCodeRepository

class VerificationCodeRepositoryImpl(VerificationCodeRepository):
    async def create(self, db: AsyncSession, entity: VerificationCode) -> VerificationCode:
        db.add(entity)
        await db.commit()
        await db.refresh(entity)
        return entity

    async def get_latest_pending_by_user_and_type(self, db: AsyncSession, user_id, type_: str):
        stmt = (
            select(VerificationCode)
            .where(
                VerificationCode.user_id == user_id,
                VerificationCode.type == type_,
                VerificationCode.used_at.is_(None),
                VerificationCode.expires_at > datetime.utcnow(),
            )
            .order_by(desc(VerificationCode.created_at))
            .limit(1)
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    async def get_by_hashed_code(self, db: AsyncSession, hashed_code: str):
        res = await db.execute(select(VerificationCode).where(VerificationCode.hashed_code == hashed_code))
        return res.scalars().first()

    async def mark_used(self, db: AsyncSession, entity: VerificationCode) -> None:
        entity.used_at = datetime.utcnow()
        await db.commit()

    async def delete_expired(self, db: AsyncSession) -> int:
        q = delete(VerificationCode).where(VerificationCode.expires_at <= datetime.utcnow())
        res = await db.execute(q)
        await db.commit()
        return res.rowcount or 0
