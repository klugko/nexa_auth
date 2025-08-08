from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.verification_code import VerificationCode

class VerificationCodeRepository:
    async def create(self, db: AsyncSession, entity: VerificationCode) -> VerificationCode:
        raise NotImplementedError

    async def get_latest_pending_by_user_and_type(self, db: AsyncSession, user_id, type_: str) -> Optional[VerificationCode]:
        raise NotImplementedError

    async def get_by_hashed_code(self, db: AsyncSession, hashed_code: str) -> Optional[VerificationCode]:
        raise NotImplementedError

    async def mark_used(self, db: AsyncSession, entity: VerificationCode) -> None:
        raise NotImplementedError

    async def delete_expired(self, db: AsyncSession) -> int:
        raise NotImplementedError
