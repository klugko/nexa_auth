from fastapi import APIRouter, Depends
from app.presentation.deps.role_guard import require_roles
from app.domain.entities.user import User

router = APIRouter(prefix="/api/v1/rbac", tags=["RBAC"])

@router.get("/admin-ping", summary="Admin-only ping")
async def admin_ping(_: User = Depends(require_roles("admin"))):
    return {"ok": True, "scope": "admin"}

@router.get("/manager-or-admin", summary="Manager or Admin")
async def manager_or_admin(_: User = Depends(require_roles("manager", "admin"))):
    return {"ok": True, "scope": "manager|admin"}
