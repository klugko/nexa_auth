from app.application.use_cases.apple_oauth_use_cases import AppleOAuthUseCases
from app.application.use_cases.microsoft_oauth_use_cases import MicrosoftOAuthUseCases
from app.application.use_cases.phone_verification_use_cases import PhoneVerificationUseCases
from app.application.use_cases.user_profile_use_cases import UserProfileUseCases
from app.application.use_cases.user_use_case import UserUseCases
from app.presentation.schemas.phone_verification_schema import PhoneVerifyRequest, PhoneVerifyResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import get_db
from app.presentation.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, MessageResponse
from app.application.use_cases.auth_use_cases import AuthUseCases
from app.application.use_cases.google_oauth_use_cases import GoogleOAuthUseCases
from app.presentation.deps.current_user import get_current_user
from app.presentation.schemas.user_schema import UserResponse, UserUpdateMeRequest
from app.domain.entities.user import User
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.presentation.schemas.validate_schema import TokenValidationResponse
from app.infrastructure.security.jwt_service import JWTService
from app.application.use_cases.password_reset_use_cases import PasswordResetUseCases
from app.presentation.schemas.password_reset_schema import PasswordForgotRequest, PasswordResetRequest, MessageResponse as PwdMessageResponse
from app.application.use_cases.email_verification_use_cases import EmailVerificationUseCases
from app.presentation.schemas.email_verification_schema import (
    EmailVerificationSendRequest,
    EmailVerificationConfirmRequest,
    MessageResponse as EmailVerifyMessageRespon)



router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

auth_use_case = AuthUseCases()
google_use_case = GoogleOAuthUseCases()
apple_use_case = AppleOAuthUseCases() 
ms_use_case = MicrosoftOAuthUseCases()
pwd_uc = PasswordResetUseCases()
email_verify_uc = EmailVerificationUseCases()
uc = UserProfileUseCases()
phone_uc = PhoneVerificationUseCases()

bearer = HTTPBearer(auto_error=False) 
jwt_service = JWTService()
user_uc = UserUseCases()

@router.post("/register", response_model=MessageResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    await auth_use_case.register(db, data.email, data.password)
    return {"message": "Inscription réussie"}

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    access_token, refresh_token = await auth_use_case.login(db, data.email, data.password)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    access_token = await auth_use_case.refresh(db, data.refresh_token)
    return {"access_token": access_token, "refresh_token": data.refresh_token, "token_type": "bearer"}

@router.post("/logout", response_model=MessageResponse)
async def logout(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await auth_use_case.logout(db, data.refresh_token)

# --- Google OAuth2 ---
@router.get("/google/login")
async def google_login():
    """
    Returns a redirect to Google's consent screen.
    Frontend peut soit suivre cette redirection, soit récupérer l'URL et rediriger côté client.
    """
    url = google_use_case.get_login_url()
    return RedirectResponse(url)

@router.get("/google/redirect")
async def google_redirect(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="Opaque state for CSRF protection"),
    db: AsyncSession = Depends(get_db),
):
    """
    Google OAuth2 callback: exchanges code for tokens and returns our local JWTs.
    """
    data = await google_use_case.handle_callback(db, code, state)
    return data

# --- Apple OAuth2 ---
@router.get("/apple/login")
async def apple_login():
    """
    Redirects to Apple's consent screen.
    """
    url = apple_use_case.get_login_url()
    return RedirectResponse(url)

@router.get("/apple/redirect")
async def apple_redirect(
    code: str = Query(..., description="Authorization code from Apple"),
    state: str = Query(..., description="Opaque state for CSRF protection"),
    db: AsyncSession = Depends(get_db),
):
    """
    Apple OAuth2 callback: exchanges code for tokens and returns our local JWTs.
    """
    data = await apple_use_case.handle_callback(db, code, state)
    return data

# --- Microsoft OAuth2 ---
@router.get("/microsoft/login")
async def microsoft_login():
    """
    Redirects to Microsoft's consent screen (MS Identity Platform).
    """
    url = ms_use_case.get_login_url()
    return RedirectResponse(url)

@router.get("/microsoft/redirect")
async def microsoft_redirect(
    code: str = Query(..., description="Authorization code from Microsoft"),
    state: str = Query(..., description="Opaque state for CSRF protection"),
    db: AsyncSession = Depends(get_db),
):
    """
    Microsoft OAuth2 callback: exchanges code for tokens, verifies id_token via JWKS,
    validates access_token by calling Graph /me, then returns local JWTs.
    """
    data = await ms_use_case.handle_callback(db, code, state)
    return data

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# activer/désactiver compte
@router.get(
    "/validate-token",
    response_model=TokenValidationResponse,
    summary="Validate JWT and return associated user",
    description=(
        "Public endpoint for other services to validate a JWT (RS256). "
        "Provide the token via 'Authorization: Bearer <token>'."
    ),
)
async def validate_token(creds: HTTPAuthorizationCredentials = Depends(bearer), db: AsyncSession = Depends(get_db)):
    if not creds or not creds.scheme.lower() == "bearer":
        return TokenValidationResponse(valid=False, message="Token manquant")
    token = creds.credentials
    try:
        payload = jwt_service.decode_token(token)
        sub = payload.get("sub")
        iat = payload.get("iat")
        exp = payload.get("exp")
        if not sub:
            return TokenValidationResponse(valid=False, message="Claim 'sub' absent")

        from uuid import UUID
        user = await user_uc.get_by_id(db, UUID(sub))
        if not user or not user.is_active:
            return TokenValidationResponse(valid=False, sub=sub, iat=iat, exp=exp, message="Utilisateur inactif ou introuvable")

        return TokenValidationResponse(
            valid=True,
            sub=sub,
            iat=iat,
            exp=exp,
            user=user,
            kid=jwt_service.kid,
        )
    except Exception:
        return TokenValidationResponse(valid=False, message="Token invalide")

# reset password
@router.post("/password/forgot", response_model=PwdMessageResponse, summary="Start password reset flow (email)")
async def password_forgot(data: PasswordForgotRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    await pwd_uc.request_reset(db, data.email, ip, ua)
    return {"message": "Si un compte existe pour cet email, un lien de réinitialisation a été envoyé."}

@router.post("/password/reset", response_model=PwdMessageResponse, summary="Confirm password reset with token")
async def password_reset(data: PasswordResetRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    await pwd_uc.confirm_reset(db, data.token, data.new_password, ip, ua)
    return {"message": "Mot de passe réinitialisé avec succès."}

@router.post("/email/send-verification", response_model=EmailVerifyMessageRespon, summary="Send email verification link")
async def email_send_verification(data: EmailVerificationSendRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    await email_verify_uc.send_verification(db, data.email, ip, ua)
    return {"message": "Si un compte existe pour cet email, un lien de vérification a été envoyé."}

@router.post("/email/verify", response_model=EmailVerifyMessageRespon, summary="Confirm email verification with token")
async def email_verify(data: EmailVerificationConfirmRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    await email_verify_uc.confirm_verification(db, data.token, ip, ua)
    return {"message": "Adresse email vérifiée avec succès."}


@router.get("/me", response_model=UserResponse, summary="Get my profile")
async def get_me(current_user: User = Depends(get_current_user)):
    return await uc.get_me(current_user)

# update profile
@router.put("/me", response_model=UserResponse, summary="Update my profile")
async def update_me(data: UserUpdateMeRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = await uc.update_me(db, current_user,
                              first_name=data.first_name,
                              last_name=data.last_name,
                              phone=data.phone,
                              position=data.position)
    return user

@router.post("/me/avatar", response_model=UserResponse, summary="Upload my avatar")
async def upload_avatar(
    file: UploadFile = File(..., description="PNG/JPEG/WEBP image"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    raw = await file.read()
    avatar_url = await uc.update_avatar(db, current_user, raw_bytes=raw)
    return current_user

# otp
@router.post("/phone/send-otp", response_model=PhoneSendOtpResponse, summary="Envoyer OTP par SMS (auth)")
async def phone_send_otp(request: Request, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    await phone_uc.send_otp(db, user=current_user, ip=ip, ua=ua)
    return {"message": "Si un numéro est associé, un code a été envoyé par SMS."}

@router.post("/phone/verify", response_model=PhoneVerifyResponse, summary="Vérifier OTP SMS (auth)")
async def phone_verify(data: PhoneVerifyRequest, request: Request, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    ip = request.client.host if request.client else None
    await phone_uc.verify_otp(db, user=current_user, code=data.code, ip=ip)
    return {"message": "Téléphone vérifié avec succès.", "phone_verified": True}
