from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import get_db
from app.presentation.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, MessageResponse
from app.application.use_cases.auth_use_cases import AuthUseCases

router = APIRouter(prefix="/auth/v1", tags=["Auth"])
auth_use_case = AuthUseCases()

@router.post("/register", response_model=MessageResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    await auth_use_case.register(db, data.email, data.password)
    return {"message": "Inscription réussie"}

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    access_token, refresh_token = await auth_use_case.login(db, data.email, data.password)
    return {"access_token": access_token, "refresh_token": refresh_token}

@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest):
    access_token = await auth_use_case.refresh(data.refresh_token)
    return {"access_token": access_token, "refresh_token": data.refresh_token}

@router.post("/logout", response_model=MessageResponse)
async def logout(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await auth_use_case.logout(db, data.refresh_token)
