from pydantic import BaseModel, conint, confloat
from typing import List, Optional

class SkillOut(BaseModel):
    skill: str
    score: conint(ge=0, le=100)
    category: Optional[str] = None
    years_experience: Optional[confloat(ge=0)] = None  
    seniority: Optional[str] = None
    confidence: Optional[conint(ge=0, le=100)] = None
    last_used_year: Optional[int] = None

class SkillsResponse(BaseModel):
    items: List[SkillOut]
