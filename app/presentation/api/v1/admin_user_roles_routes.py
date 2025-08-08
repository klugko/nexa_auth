from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_db
from app.presentation.deps.role_guard import require_roles
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.repositories.role_repository_impl import RoleRepositoryImpl
from app.presentation.schemas.role_schema import RoleAssignRequest, AdminUserRolesResponse

router = APIRouter(
    prefix="/api/v1/admin/users",
    tags=["Admin • Users"],
    dependencies=[Depends(require_roles("admin"))],  # Guard admin global à ce router
)

user_repo = UserRepositoryImpl()
role_repo = RoleRepositoryImpl()

@router.post("/{user_id}/roles", response_model=AdminUserRolesResponse, summary="Attribuer un rôle à un utilisateur (admin)")
async def admin_assign_role(user_id: UUID, data: RoleAssignRequest, db: AsyncSession = Depends(get_db)):
    user = await user_repo.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    role = await role_repo.get_by_name(db, data.role.lower())
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rôle inconnu")

    await role_repo.add_role_to_user(db, user.id, role)
    roles = [r.name for r in await role_repo.list_for_user(db, user.id)]
    return {"user_id": user.id, "roles": roles}

@router.delete("/{user_id}/roles/{role_name}", response_model=AdminUserRolesResponse, summary="Retirer un rôle à un utilisateur (admin)")
async def admin_remove_role(user_id: UUID, role_name: str, db: AsyncSession = Depends(get_db)):
    user = await user_repo.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    role = await role_repo.get_by_name(db, role_name.lower())
    if not role:
        roles = [r.name for r in await role_repo.list_for_user(db, user.id)]
        return {"user_id": user.id, "roles": roles}

    await role_repo.remove_role_from_user(db, user.id, role)
    roles = [r.name for r in await role_repo.list_for_user(db, user.id)]
    return {"user_id": user.id, "roles": roles}
