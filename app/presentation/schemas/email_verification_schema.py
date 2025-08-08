from pydantic import BaseModel, EmailStr, Field

class EmailVerificationSendRequest(BaseModel):
    email: EmailStr

class EmailVerificationConfirmRequest(BaseModel):
    token: str = Field(..., min_length=20)

class MessageResponse(BaseModel):
    message: str
