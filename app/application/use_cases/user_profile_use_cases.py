import io
from typing import Optional
from PIL import Image
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.storage.local_storage_service import LocalStorageService 

user_repo = UserRepositoryImpl()
storage = LocalStorageService()  

ALLOWED_FORMATS = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}

class UserProfileUseCases:
    async def get_me(self, user):
        return user

    async def update_me(self, db: AsyncSession, user, *, first_name: Optional[str], last_name: Optional[str], phone: Optional[str], position: Optional[str]):
        return await user_repo.update_profile(
            db, user,
            first_name=first_name, last_name=last_name,
            phone=phone, position=position
        )

    async def update_avatar(self, db: AsyncSession, user, *, raw_bytes: bytes) -> str:
        if len(raw_bytes) > settings.avatar_max_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Fichier trop volumineux")

        try:
            im = Image.open(io.BytesIO(raw_bytes))
            im.verify()
        except Exception:
            raise HTTPException(status_code=400, detail="Fichier image invalide")

        im = Image.open(io.BytesIO(raw_bytes))
        w, h = im.size
        if w < settings.avatar_min_width or h < settings.avatar_min_height:
            raise HTTPException(status_code=400, detail="Image trop petite")
        if w > settings.avatar_max_width or h > settings.avatar_max_height:
            raise HTTPException(status_code=400, detail="Image trop grande")

        fmt = (im.format or "").upper()
        if fmt not in ALLOWED_FORMATS:
            raise HTTPException(status_code=400, detail="Format non supporté (PNG, JPEG, WEBP)")
        ext = ALLOWED_FORMATS[fmt]

        avatar_url = await storage.save_avatar(user_id=str(user.id), content=raw_bytes, ext=ext)

        await user_repo.update_avatar_url(db, user, avatar_url)
        return avatar_url
