from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.user_skill_repository_impl import UserSkillRepositoryImpl
from app.infrastructure.services.skill_scoring_service import SkillScoringService, WeightConfig

skill_repo = UserSkillRepositoryImpl()
scorer = SkillScoringService()

def _months_to_years(m):
    if m is None: return None
    return round(m / 12.0, 1)

class SkillSummaryUseCases:
    async def my_summary(self, db: AsyncSession, *, user):
        items = await skill_repo.list_for_user(db, user.id)
        if not items:
            return {"global_score": 0.0, "family_count": 0, "families": []}

        scored = []
        for it in items:
            scored.append(
                scorer.score_skill(
                    name=it.skill,
                    score=it.score,
                    category=getattr(it, "category", None),
                    years_experience=_months_to_years(getattr(it, "years_experience_months", None)),
                    confidence=getattr(it, "confidence", None),
                    last_used_year=getattr(it, "last_used_year", None),
                )
            )

        return scorer.aggregate(scored)
