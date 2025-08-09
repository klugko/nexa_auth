from pydantic import BaseModel, conlist, conint, confloat
from typing import List, Optional

class ScoredSkill(BaseModel):
    name: str
    family: str
    weighted_score: confloat(ge=0, le=100)
    proficiency: conint(ge=0, le=100)
    experience_years: Optional[confloat(ge=0)] = None
    recency_factor: Optional[confloat(ge=0, le=1)] = None
    confidence: Optional[conint(ge=0, le=100)] = None

class FamilySummary(BaseModel):
    family: str
    score: confloat(ge=0, le=100)
    top_skills: List[ScoredSkill]

class SkillSummaryResponse(BaseModel):
    global_score: confloat(ge=0, le=100)
    family_count: int
    families: List[FamilySummary]
