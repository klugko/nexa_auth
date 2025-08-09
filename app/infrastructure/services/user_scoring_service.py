from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from app.config import settings

@dataclass(frozen=True)
class UserSignals:
    email_verified: bool
    phone_verified: bool
    profile_completion_ratio: float   # 0..1
    skills_count: int
    skills_global_score: float       # 0..100
    resume_parsed_at: Optional[datetime]  # activité

class UserScoringService:
    """
    Combine des signaux hétérogènes en un score 0..100.
    Composants:
      - email_verified (binaire)
      - phone_verified (binaire)
      - profile_completion_ratio (0..1)
      - skills (count coverage + global skill score)
      - activity (decay sur récence du CV parsé)
    """

    def __init__(self):
        self.w_email = settings.scoring_w_email_verified
        self.w_phone = settings.scoring_w_phone_verified
        self.w_profile = settings.scoring_w_profile_completion
        self.w_skills = settings.scoring_w_skills
        self.w_activity = settings.scoring_w_activity

        self.half_life_days = settings.scoring_activity_half_life_days
        self.skills_count_cap = settings.scoring_skills_count_cap

    def _normalize_weights(self):
        s = self.w_email + self.w_phone + self.w_profile + self.w_skills + self.w_activity
        if s <= 0:
            return (0.2, 0.2, 0.2, 0.2, 0.2)
        return (
            self.w_email / s,
            self.w_phone / s,
            self.w_profile / s,
            self.w_skills / s,
            self.w_activity / s,
        )

    def _activity_factor(self, parsed_at: Optional[datetime]) -> float:
        if not parsed_at:
            return 0.0
        days = max(0.0, (datetime.utcnow() - parsed_at).total_seconds() / 86400.0)
        return 0.5 ** (days / max(1.0, float(self.half_life_days)))  # ∈ (0,1]

    def _skills_component(self, count: int, global_score: float) -> float:
        cov = min(1.0, max(0.0, count) / max(1, self.skills_count_cap))
        qual = max(0.0, min(100.0, global_score)) / 100.0
        return 100.0 * (0.5 * cov + 0.5 * qual)

    def compute(self, sig: UserSignals) -> dict:
        w_email, w_phone, w_profile, w_skills, w_act = self._normalize_weights()

        email_c = 100.0 if sig.email_verified else 0.0
        phone_c = 100.0 if sig.phone_verified else 0.0
        profile_c = 100.0 * max(0.0, min(1.0, sig.profile_completion_ratio))
        skills_c = self._skills_component(sig.skills_count, sig.skills_global_score)
        act_c = 100.0 * self._activity_factor(sig.resume_parsed_at)

        final = (
            w_email * email_c +
            w_phone * phone_c +
            w_profile * profile_c +
            w_skills * skills_c +
            w_act * act_c
        )
        return {
            "score": int(round(max(0.0, min(100.0, final)))),
            "components": {
                "email_verified": round(email_c, 1),
                "phone_verified": round(phone_c, 1),
                "profile_completion": round(profile_c, 1),
                "skills": round(skills_c, 1),
                "activity": round(act_c, 1),
                "weights": {
                    "email": w_email, "phone": w_phone, "profile": w_profile, "skills": w_skills, "activity": w_act
                }
            }
        }
