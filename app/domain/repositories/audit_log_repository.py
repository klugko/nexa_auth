from typing import Iterable, List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.audit_log import AuditLog

class AuditLogRepository:
    async def bulk_insert(self, db: AsyncSession, rows: Iterable[dict]) -> int:
        raise NotImplementedError

    async def find(
        self, db: AsyncSession,
        *, user_id: Optional[UUID], action: Optional[str],
        dt_from: Optional[datetime], dt_to: Optional[datetime],
        page: int, size: int
    ) -> List[AuditLog]:
        raise NotImplementedError

    async def count(
        self, db: AsyncSession,
        *, user_id: Optional[UUID], action: Optional[str],
        dt_from: Optional[datetime], dt_to: Optional[datetime],
    ) -> int:
        raise NotImplementedError

    async def delete_older_than(self, db: AsyncSession, *, before: datetime) -> int:
        raise NotImplementedError
