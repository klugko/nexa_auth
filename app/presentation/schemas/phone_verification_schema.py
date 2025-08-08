from pydantic import BaseModel, constr

class PhoneSendOtpResponse(BaseModel):
    message: str

class PhoneVerifyRequest(BaseModel):
    code: constr(strip_whitespace=True, min_length=4, max_length=10)

class PhoneVerifyResponse(BaseModel):
    message: str
    phone_verified: bool
