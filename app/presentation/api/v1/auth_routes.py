from app.application.use_cases.apple_oauth_use_cases import AppleOAuthUseCases
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import get_db
from app.presentation.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, MessageResponse
from app.application.use_cases.auth_use_cases import AuthUseCases
from app.application.use_cases.google_oauth_use_cases import GoogleOAuthUseCases
from app.presentation.deps.current_user import get_current_user
from app.presentation.schemas.user_schema import UserResponse
from app.domain.entities.user import User


router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

auth_use_case = AuthUseCases()
google_use_case = GoogleOAuthUseCases()
apple_use_case = AppleOAuthUseCases() 

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




@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


