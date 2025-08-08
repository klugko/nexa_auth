from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_db
from app.presentation.deps.role_guard import require_roles
from app.application.use_cases.admin_user_use_cases import AdminUserUseCases
from app.presentation.schemas.admin_user_schema import (
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserOut,
    PaginatedUsers,
    AllowedSort,
    AllowedOrder,
)

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Admin • Users"],
    dependencies=[Depends(require_roles("admin"))],  # Guard admin global
)

uc = AdminUserUseCases()

def _to_out(u) -> AdminUserOut:
    return AdminUserOut(
        id=u.id,
        email=u.email,
        first_name=u.first_name,
        last_name=u.last_name,
        phone=u.phone,
        position=u.position,
        avatar_url=u.avatar_url,
        is_active=u.is_active,
        email_verified=getattr(u, "email_verified", None),
        created_at=u.created_at,
        roles=[r.name for r in (u.roles or [])],
    )

@router.get("", response_model=PaginatedUsers, summary="List users (admin)")
async def list_users(
    keyword: Optional[str] = Query(None, description="Recherche par email, prénom, nom, téléphone"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: AllowedSort = Query("created_at"),
    sort_dir: AllowedOrder = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    items, total = await uc.list_users(
        db,
        keyword=keyword,
        page=page,
        size=size,
        sort_by=str(sort_by),
        sort_dir=str(sort_dir),
    )
    return {
        "page": page,
        "size": size,
        "total": total,
        "items": [_to_out(u) for u in items],
    }

@router.post("", response_model=AdminUserOut, summary="Create user (admin)")
async def create_user(data: AdminUserCreate, db: AsyncSession = Depends(get_db)):
    u = await uc.create_user(
        db,
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        position=data.position,
        is_active=data.is_active,
        email_verified=data.email_verified,
    )
    return _to_out(u)

@router.put("/{user_id}", response_model=AdminUserOut, summary="Replace/update user (admin)")
@router.patch("/{user_id}", response_model=AdminUserOut, summary="Partial update user (admin)")
async def update_user(user_id: UUID, data: AdminUserUpdate, db: AsyncSession = Depends(get_db)):
    u = await uc.update_user(
        db,
        user_id=user_id,
        email=data.email,
        new_password=data.new_password,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        position=data.position,
        is_active=data.is_active,
        email_verified=data.email_verified,
    )
    return _to_out(u)

@router.delete("/{user_id}", summary="Delete user (admin)", status_code=204)
async def delete_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    await uc.delete_user(db, user_id=user_id)
    return
