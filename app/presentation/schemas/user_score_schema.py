from pydantic import BaseModel, conint
from typing import Dict, Any

class UserScoreResponse(BaseModel):
    score: conint(ge=0, le=100)
    components: Dict[str, Any]

class AdminRecomputeScoreResponse(BaseModel):
    score: conint(ge=0, le=100)
    updated_at: str
    components: Dict[str, Any]
