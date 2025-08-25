from pydantic import BaseModel, EmailStr, Field

class EmailVerificationSendRequest(BaseModel):
    email: EmailStr

class EmailVerificationConfirmRequest(BaseModel):
    token: str 

class MessageResponse(BaseModel):
    message: str
