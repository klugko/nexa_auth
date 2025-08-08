from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_db
from app.presentation.deps.role_guard import require_roles
from app.presentation.deps.current_user import get_current_user
from app.domain.entities.user import User

from app.application.use_cases.invitation_use_cases import InvitationUseCases
from app.presentation.schemas.invitation_schema import InvitationCreateRequest, InvitationAcceptRequest, MessageResponse

router = APIRouter(prefix="/api/v1/invitations", tags=["Invitations"])
uc = InvitationUseCases()

@router.post("", response_model=MessageResponse, dependencies=[Depends(require_roles("admin", "manager"))], summary="Créer et envoyer une invitation (admin/manager)")
async def create_invitation(data: InvitationCreateRequest, request: Request, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    await uc.create_invitation(
        db,
        inviter_id=current_user.id,
        inviter_email=current_user.email,
        target_type=data.target_type,
        target_id=data.target_id,
        invitee_email=data.email,
        ip=ip,
        ua=ua,
    )
    return {"message": "Invitation envoyée si l’adresse est valide."}

@router.post("/accept", summary="Accepter une invitation (public)")
async def accept_invitation(data: InvitationAcceptRequest, db: AsyncSession = Depends(get_db)):
    res = await uc.accept_invitation(
        db,
        raw_token=data.token,
        first_name=data.first_name,
        last_name=data.last_name,
        password=data.password,
    )
    return res
