from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import get_db
from app.presentation.schemas.auth_schema import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshRequest, MessageResponse
)
from app.application.use_cases.auth_use_cases import AuthUseCases
from app.infrastructure.security.jwt_service import JWTService
from jose import JWTError
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl

router = APIRouter(prefix="/auth/v1", tags=["Auth"])
auth_use_case = AuthUseCases()
jwt_service = JWTService()
user_repo = UserRepositoryImpl()


def get_current_user(token: str = Depends(jwt_service.decode_token), db: AsyncSession = Depends(get_db)):
    """Extract and return current user from JWT."""
    try:
        payload = token
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalide")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Impossible de valider le token")


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
async def get_me(current_user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        user = await user_repo.get_by_id(db, current_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "is_active": user.is_active,
            "created_at": user.created_at
        }
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne lors de la récupération du profil utilisateur")
