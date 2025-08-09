from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.infrastructure.db.session import get_db
from app.presentation.deps.current_user import get_current_user
from app.presentation.deps.role_guard import require_roles
from app.domain.entities.user import User
from app.application.use_cases.user_score_use_cases import UserScoreUseCases
from app.presentation.schemas.user_score_schema import UserScoreResponse, AdminRecomputeScoreResponse

router = APIRouter(prefix="/api/v1/users", tags=["Users • Score"])
uc = UserScoreUseCases()

@router.get("/me/score", response_model=UserScoreResponse, summary="Mon score agrégé (0..100)")
async def my_score(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await uc.get_my_score(db, user=current_user)

@router.post("/{user_id}/recompute-score", response_model=AdminRecomputeScoreResponse, summary="Recalculer le score d'un user (admin)", dependencies=[Depends(require_roles("admin"))])
async def recompute_score(user_id: UUID, db: AsyncSession = Depends(get_db)):
    return await uc.recompute_for_user(db, user_id=user_id)
