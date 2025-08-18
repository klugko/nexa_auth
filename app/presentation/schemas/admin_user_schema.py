from pydantic import BaseModel, EmailStr, Field, constr
from uuid import UUID
from typing import Optional, List, Literal  
from datetime import datetime

AllowedSort = Literal["created_at", "email", "first_name", "last_name"]
AllowedOrder = Literal["asc", "desc"]

class AdminUserCreate(BaseModel):
    email: EmailStr
    password: Optional[constr(min_length=8, max_length=128)] = None
    first_name: Optional[constr(strip_whitespace=True, max_length=100)] = None
    last_name: Optional[constr(strip_whitespace=True, max_length=100)] = None
    phone: Optional[constr(strip_whitespace=True, max_length=20)] = None
    position: Optional[constr(strip_whitespace=True, max_length=100)] = None
    is_active: bool = True
    email_verified: Optional[bool] = None

class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    new_password: Optional[constr(min_length=8, max_length=128)] = Field(None, description="Set a new password")
    first_name: Optional[constr(strip_whitespace=True, max_length=100)] = None
    last_name: Optional[constr(strip_whitespace=True, max_length=100)] = None
    phone: Optional[constr(strip_whitespace=True, max_length=20)] = None
    position: Optional[constr(strip_whitespace=True, max_length=100)] = None
    is_active: Optional[bool] = None
    email_verified: Optional[bool] = None

class AdminUserOut(BaseModel):
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
    roles: List[str] = []

    class Config:
        from_attributes = True

class PaginatedUsers(BaseModel):
    page: int
    size: int
    total: int
    items: List[AdminUserOut]
