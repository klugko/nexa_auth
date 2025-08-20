from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, conint

class AuditItem(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    action: str
    resource: str
    ip: Optional[str] = None
    ua: Optional[str] = None
    created_at: datetime
    meta: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class AuditQuery(BaseModel):
    user_id: Optional[UUID] = None
    action: Optional[str] = Field(None, max_length=64)
    dt_from: Optional[datetime] = None
    dt_to: Optional[datetime] = None
    page: conint(ge=1) = 1
    size: conint(ge=1, le=100) = 20

class AuditListResponse(BaseModel):
    items: List[AuditItem]
    total: int
    page: int
    size: int
