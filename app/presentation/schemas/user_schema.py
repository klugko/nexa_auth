from pydantic import BaseModel, EmailStr, Field, constr
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    email_verified: Optional[bool] = None
    created_at: datetime
    
    class Config:
        orm_mode = True


class UserUpdateMeRequest(BaseModel):
    first_name: Optional[constr(strip_whitespace=True, min_length=1, max_length=100)] = None
    last_name: Optional[constr(strip_whitespace=True, min_length=1, max_length=100)] = None
    phone: Optional[constr(strip_whitespace=True, min_length=6, max_length=20)] = None
    position: Optional[constr(strip_whitespace=True, min_length=2, max_length=100)] = None