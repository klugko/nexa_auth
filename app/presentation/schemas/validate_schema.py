from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

class ValidatedUser(BaseModel):
    id: UUID
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool

    class Config:
        orm_mode = True

class TokenValidationResponse(BaseModel):
    valid: bool
    sub: Optional[str] = None
    iat: Optional[int] = None
    exp: Optional[int] = None
    user: Optional[ValidatedUser] = None
    kid: Optional[str] = None
    jwks_uri: str = "/.well-known/jwks.json"
    message: Optional[str] = None
