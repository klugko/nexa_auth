from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.domain.entities.user_skill import UserSkill
from app.domain.repositories.user_skill_repository import UserSkillRepository

class UserSkillRepositoryImpl(UserSkillRepository):
    async def upsert_bulk(self, db: AsyncSession, user_id: UUID, items) -> None:
        """
        items peut être:
        - liste[tuple(name:str, score:int)]  (compat MVP)
        - liste[dict{name, score, category?, years_experience_months?, seniority?, confidence?, last_used_year?}]
        Stratégie MVP: remplacement complet des compétences du user (performant & simple).
        """
        await db.execute(delete(UserSkill).where(UserSkill.user_id == user_id))

        for it in items:
            if isinstance(it, tuple):
                name, score = it[0], int(it[1])
                db.add(UserSkill(user_id=user_id, skill=name, score=score))
            else:
                db.add(UserSkill(
                    user_id=user_id,
                    skill=it["name"],
                    score=int(it["score"]),
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
            .order_by(UserSkill.score.desc(), UserSkill.confidence.desc().nullslast(), UserSkill.skill.asc())
        )
        return list(res.scalars().all())
