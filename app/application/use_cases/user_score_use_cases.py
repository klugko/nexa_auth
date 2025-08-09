from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.repositories.user_score_repository_impl import UserScoreRepositoryImpl
from app.infrastructure.repositories.user_skill_repository_impl import UserSkillRepositoryImpl
from app.infrastructure.repositories.user_resume_repository_impl import UserResumeRepositoryImpl
from app.infrastructure.services.user_scoring_service import UserScoringService, UserSignals
from app.infrastructure.services.skill_scoring_service import SkillScoringService 

user_repo = UserRepositoryImpl()
score_repo = UserScoreRepositoryImpl()
skill_repo = UserSkillRepositoryImpl()
resume_repo = UserResumeRepositoryImpl()

scorer = UserScoringService()
skill_scorer = SkillScoringService()

def _months_to_years(m):
    if m is None: return None
    return round(m / 12.0, 1)

class UserScoreUseCases:
    async def _compute_signals(self, db: AsyncSession, *, user_id: UUID) -> dict:
        user = await user_repo.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

        fields = [user.first_name, user.last_name, user.phone, user.position, user.avatar_url]
        profile_ratio = sum(1 for v in fields if v and str(v).strip()) / 5.0

        skills = await skill_repo.list_for_user(db, user_id)
        scored = []
        for it in skills:
            scored.append(
                skill_scorer.score_skill(
                    name=it.skill,
                    score=it.score,
                    category=getattr(it, "category", None),
                    years_experience=_months_to_years(getattr(it, "years_experience_months", None)),
                    confidence=getattr(it, "confidence", None),
                    last_used_year=getattr(it, "last_used_year", None),
                )
            )
        agg = skill_scorer.aggregate(scored) if scored else {"global_score": 0.0}
        global_skill_score = float(agg["global_score"]) if "global_score" in agg else 0.0

        resume = await resume_repo.get_latest_for_user(db, user_id)
        parsed_at = resume.parsed_at if resume and resume.parsed_at else None

        sig = UserSignals(
            email_verified=bool(getattr(user, "email_verified", False)),
            phone_verified=bool(getattr(user, "phone_verified", False)),
            profile_completion_ratio=profile_ratio,
            skills_count=len(skills),
            skills_global_score=global_skill_score,
            resume_parsed_at=parsed_at
        )
        result = scorer.compute(sig)
        return {"user": user, "result": result}

    async def get_my_score(self, db: AsyncSession, *, user):
        data = await self._compute_signals(db, user_id=user.id)
        await score_repo.upsert(db, user.id, data["result"]["score"])
        return data["result"]

    async def recompute_for_user(self, db: AsyncSession, *, user_id: UUID):
        data = await self._compute_signals(db, user_id=user_id)
        entity = await score_repo.upsert(db, user_id, data["result"]["score"])
        return {"score": entity.score, "updated_at": entity.updated_at, "components": data["result"]["components"]}
