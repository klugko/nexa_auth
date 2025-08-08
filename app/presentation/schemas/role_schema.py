from pydantic import BaseModel, constr
from uuid import UUID
from typing import List

class RoleAssignRequest(BaseModel):
    role: constr(strip_whitespace=True, min_length=3, max_length=50)

class AdminUserRolesResponse(BaseModel):
    user_id: UUID
    roles: List[str]
