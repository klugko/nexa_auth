from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_db
from app.presentation.deps.current_user import get_current_user
from app.domain.entities.user import User
from app.application.use_cases.skill_summary_use_cases import SkillSummaryUseCases
from app.presentation.schemas.skill_summary_schema import SkillSummaryResponse

router = APIRouter(prefix="/api/v1/users/me", tags=["Users • Resume/Skills"])

uc = SkillSummaryUseCases()

@router.get("/skills/summary", response_model=SkillSummaryResponse, summary="Résumé des compétences (clustering + score global)")
async def skill_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await uc.my_summary(db, user=current_user)
