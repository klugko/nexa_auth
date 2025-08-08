from pydantic import BaseModel, EmailStr, Field, constr
from typing import Optional

class InvitationCreateRequest(BaseModel):
    email: EmailStr
    target_type: Optional[constr(strip_whitespace=True, max_length=50)] = None
    target_id: Optional[constr(strip_whitespace=True, max_length=64)] = None

class InvitationAcceptRequest(BaseModel):
    token: str = Field(..., min_length=20)
    first_name: Optional[constr(strip_whitespace=True, max_length=100)] = None
    last_name: Optional[constr(strip_whitespace=True, max_length=100)] = None
    password: Optional[constr(min_length=8, max_length=128)] = None

class MessageResponse(BaseModel):
    message: str
