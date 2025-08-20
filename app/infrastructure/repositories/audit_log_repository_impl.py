from typing import Iterable, List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, and_, func, delete, desc

from app.domain.entities.audit_log import AuditLog
from app.domain.repositories.audit_log_repository import AuditLogRepository

class AuditLogRepositoryImpl(AuditLogRepository):
    async def bulk_insert(self, db: AsyncSession, rows: Iterable[dict]) -> int:
        rows = list(rows)
        if not rows:
            return 0
        stmt = insert(AuditLog).values(rows)
        await db.execute(stmt)
        await db.commit()
        return len(rows)

    async def find(self, db: AsyncSession,
                   *, user_id: Optional[UUID], action: Optional[str],
                   dt_from: Optional[datetime], dt_to: Optional[datetime],
                   page: int, size: int) -> List[AuditLog]:
        conds = []
        if user_id: conds.append(AuditLog.user_id == user_id)
        if action:  conds.append(AuditLog.action == action)
        if dt_from: conds.append(AuditLog.created_at >= dt_from)
        if dt_to:   conds.append(AuditLog.created_at <= dt_to)

        stmt = (select(AuditLog)
                .where(and_(*conds) if conds else True)
                .order_by(desc(AuditLog.created_at))
                .offset(max(0, (page - 1) * size)).limit(size))
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def count(self, db: AsyncSession,
                    *, user_id: Optional[UUID], action: Optional[str],
                    dt_from: Optional[datetime], dt_to: Optional[datetime]) -> int:
        conds = []
        if user_id: conds.append(AuditLog.user_id == user_id)
        if action:  conds.append(AuditLog.action == action)
        if dt_from: conds.append(AuditLog.created_at >= dt_from)
        if dt_to:   conds.append(AuditLog.created_at <= dt_to)
        stmt = select(func.count()).select_from(AuditLog).where(and_(*conds) if conds else True)
        res = await db.execute(stmt)
        return int(res.scalar_one())

    async def delete_older_than(self, db: AsyncSession, *, before: datetime) -> int:
        res = await db.execute(delete(AuditLog).where(AuditLog.created_at < before))
        await db.commit()
        return res.rowcount or 0
