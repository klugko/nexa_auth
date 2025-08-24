from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.domain.entities.user_skill import UserSkill
from app.domain.repositories.user_skill_repository import UserSkillRepository

class UserSkillRepositoryImpl(UserSkillRepository):
    async def upsert_bulk(self, db: AsyncSession, user_id: UUID, items: List[Dict[str, Any]]) -> None:
        """
        'items' est une liste de dicts normalisés par ResumeParserService.extract_skills():
        {
          "name": str,
          "score": int,
          "category": str | None,
          "years_experience_months": int | None,
          "seniority": str | None,
          "confidence": int | None,
          "last_used_year": int | None
        }
        """
        await db.execute(delete(UserSkill).where(UserSkill.user_id == user_id))
        for it in items:
            db.add(UserSkill(
                user_id=user_id,
                skill=it["name"],
                score=int(it.get("score", 0)),
                category=it.get("category"),
                years_experience_months=it.get("years_experience_months"),
                seniority=it.get("seniority"),
                confidence=it.get("confidence"),
                last_used_year=it.get("last_used_year"),
            ))
        await db.commit()

    async def list_for_user(self, db: AsyncSession, user_id: UUID) -> List[UserSkill]:
        res = await db.execute(
            select(UserSkill)
            .where(UserSkill.user_id == user_id)
            .order_by(UserSkill.score.desc(), UserSkill.skill.asc())
        )
        return list(res.scalars().all())
