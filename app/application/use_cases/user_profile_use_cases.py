import io
from uuid import UUID
from typing import Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image

from app.config import settings
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.storage.local_storage_service import LocalStorageService

user_repo = UserRepositoryImpl()

# Pour évoluer vers S3, on pourra basculer une Fabrique ici selon settings.storage_backend
storage = LocalStorageService()

ALLOWED_FORMATS = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}

class UserProfileUseCases:
    async def get_me(self, user):
        return user

    async def update_me(self, db: AsyncSession, user, *, first_name: Optional[str], last_name: Optional[str], phone: Optional[str], position: Optional[str]):
        return await user_repo.update_profile(db, user, first_name=first_name, last_name=last_name, phone=phone, position=position)

    async def update_avatar(self, db: AsyncSession, user, *, raw_bytes: bytes) -> str:
        # 1) taille max
        if len(raw_bytes) > settings.avatar_max_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Fichier trop volumineux")

        # 2) validation image
        try:
            im = Image.open(io.BytesIO(raw_bytes))
            im.verify()  # vérifie la structure
        except Exception:
            raise HTTPException(status_code=400, detail="Fichier image invalide")

        # Re-ouvre pour charger les dimensions (verify() ferme le parser)
        im = Image.open(io.BytesIO(raw_bytes))
        width, height = im.size
        if width < settings.avatar_min_width or height < settings.avatar_min_height:
            raise HTTPException(status_code=400, detail="Image trop petite")
        if width > settings.avatar_max_width or height > settings.avatar_max_height:
            raise HTTPException(status_code=400, detail="Image trop grande")

        fmt = (im.format or "").upper()
        if fmt not in ALLOWED_FORMATS:
            raise HTTPException(status_code=400, detail="Format non supporté (PNG, JPEG, WEBP)")

        ext = ALLOWED_FORMATS[fmt]

        # Option: normaliser/compresser ici si besoin (ex: re-save)
        # Ici, on sauvegarde tel quel pour éviter une recompression.

        # 3) enregistrer via Storage
        avatar_url = await storage.save_avatar(user_id=str(user.id), content=raw_bytes, ext=ext)

        # 4) mettre à jour User
        await user_repo.update_avatar_url(db, user, avatar_url)
        return avatar_url
