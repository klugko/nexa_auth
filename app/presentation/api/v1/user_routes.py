from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_db
from app.presentation.deps.current_user import get_current_user
from app.presentation.schemas.user_schema import UserResponse, UserUpdateMeRequest
from app.application.use_cases.user_profile_use_cases import UserProfileUseCases
from app.domain.entities.user import User

router = APIRouter(prefix="/api/v1/users", tags=["Users"])

uc = UserProfileUseCases()

@router.get("/me", response_model=UserResponse, summary="Get my profile")
async def get_me(current_user: User = Depends(get_current_user)):
    return await uc.get_me(current_user)

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
