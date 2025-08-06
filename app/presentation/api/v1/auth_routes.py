from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import get_db
from app.presentation.schemas.auth_schema import (
    RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, MessageResponse
)
from app.application.use_cases.auth_use_cases import AuthUseCases
from app.infrastructure.security.jwt_service import JWTService

router = APIRouter(prefix="/auth/v1", tags=["Auth"])
auth_use_case = AuthUseCases()
jwt_service = JWTService()

@router.post("/register", response_model=MessageResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        await auth_use_case.register(db, data.email, data.password)
        return {"message": "Inscription réussie"}
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne lors de l'inscription")

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        access_token, refresh_token = await auth_use_case.login(db, data.email, data.password)
        return {"access_token": access_token, "refresh_token": refresh_token}
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne lors de la connexion")

@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        access_token = await auth_use_case.refresh(db, data.refresh_token)
        return {"access_token": access_token, "refresh_token": data.refresh_token}
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne lors du rafraîchissement du token")

@router.post("/logout", response_model=MessageResponse)
async def logout(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await auth_use_case.logout(db, data.refresh_token)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne lors de la déconnexion")

@router.get("/me")
async def get_me(current_user=Depends(jwt_service.get_current_user)):
    """Retourne les informations de l'utilisateur connecté"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }
