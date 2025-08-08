from pydantic import BaseModel, EmailStr, Field

class PasswordForgotRequest(BaseModel):
    email: EmailStr

class PasswordResetRequest(BaseModel):
    token: str = Field(..., min_length=20)
    new_password: str = Field(..., min_length=8, max_length=128)

class MessageResponse(BaseModel):
    message: str
