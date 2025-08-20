from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.infrastructure.db.session import get_db
from app.presentation.deps.role_guard import require_roles
from app.presentation.deps.current_user import get_current_user
from app.domain.entities.user import User

from app.presentation.schemas.audit_schema import AuditListResponse, AuditItem
from app.infrastructure.repositories.audit_log_repository_impl import AuditLogRepositoryImpl

router = APIRouter(prefix="/api/v1/audit", tags=["Audit"])
repo = AuditLogRepositoryImpl()

@router.get("", response_model=AuditListResponse, dependencies=[Depends(require_roles("admin"))], summary="Lister les logs d'audit (admin)")
async def list_audit(
    db: AsyncSession = Depends(get_db),
    user_id: Optional[UUID] = Query(default=None),
    action: Optional[str] = Query(default=None, max_length=64),
    dt_from: Optional[datetime] = Query(default=None),
    dt_to: Optional[datetime] = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    items = await repo.find(db, user_id=user_id, action=action, dt_from=dt_from, dt_to=dt_to, page=page, size=size)
    total = await repo.count(db, user_id=user_id, action=action, dt_from=dt_from, dt_to=dt_to)
    return {"items": items, "total": total, "page": page, "size": size}

@router.get("/me", response_model=AuditListResponse, summary="Mes logs d'activité")
async def my_audit(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    action: Optional[str] = Query(default=None, max_length=64),
    dt_from: Optional[datetime] = Query(default=None),
    dt_to: Optional[datetime] = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    user_id = current_user.id
    items = await repo.find(db, user_id=user_id, action=action, dt_from=dt_from, dt_to=dt_to, page=page, size=size)
    total = await repo.count(db, user_id=user_id, action=action, dt_from=dt_from, dt_to=dt_to)
    return {"items": items, "total": total, "page": page, "size": size}
