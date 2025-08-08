import hashlib
import random
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infrastructure.services.rate_limiter import rate_limiter
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.repositories.verification_code_repository_impl import VerificationCodeRepositoryImpl
from app.infrastructure.sms.factory import get_sms_provider
from app.domain.entities.verification_code import VerificationCode

user_repo = UserRepositoryImpl()
code_repo = VerificationCodeRepositoryImpl()
sms = get_sms_provider()

def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"

PHONE_TYPE = "PHONE"

class PhoneVerificationUseCases:
    async def send_otp(self, db: AsyncSession, *, user, ip: Optional[str], ua: Optional[str]) -> None:
        if not user.phone:
            raise HTTPException(status_code=400, detail="Aucun numéro de téléphone. Mettez à jour votre profil.")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Compte inactif")

        key = f"phoneotp_send:{user.id}:{user.phone}:{ip}"
        if not rate_limiter.allow(key, settings.phone_otp_rate_max_per_key, settings.phone_otp_rate_window_seconds):
            raise HTTPException(status_code=429, detail="Trop de requêtes, réessayez plus tard")

        code = _generate_otp()
        hashed = _sha256_hex(code)

        entity = VerificationCode(
            user_id=user.id,
            type=PHONE_TYPE,
            hashed_code=hashed,
            expires_at=VerificationCode.default_expiry(settings.phone_otp_expire_minutes),
            ip_address=ip,
            user_agent=ua[:255] if ua else None,
        )
        await code_repo.create(db, entity)

        msg = f"{settings.sms_sender_id} code: {code}. Valid {settings.phone_otp_expire_minutes} min."
        try:
            await sms.send(user.phone, msg)
        except Exception:
            pass

    async def verify_otp(self, db: AsyncSession, *, user, code: str, ip: Optional[str]) -> None:
        if not user.phone:
            raise HTTPException(status_code=400, detail="Aucun numéro de téléphone sur le profil")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Compte inactif")

        key = f"phoneotp_verify:{user.id}:{user.phone}:{ip}"
        if not rate_limiter.allow(key, settings.phone_otp_verify_rate_max_per_key, settings.phone_otp_rate_window_seconds):
            raise HTTPException(status_code=429, detail="Trop de tentatives, réessayez plus tard")

        hashed = _sha256_hex(code)
        entity = await code_repo.get_by_hashed_code(db, hashed)
        if not entity or entity.user_id != user.id or entity.type != PHONE_TYPE:
            raise HTTPException(status_code=400, detail="Code invalide")
        if entity.used_at is not None:
            raise HTTPException(status_code=400, detail="Code déjà utilisé")
        if datetime.utcnow() > entity.expires_at:
            raise HTTPException(status_code=400, detail="Code expiré")

        await code_repo.mark_used(db, entity)
        await user_repo.update_admin(db, user, phone_verified=True) 
        try:
            await code_repo.delete_expired(db)
        except Exception:
            pass
