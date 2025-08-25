import hashlib
import secrets
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.repositories.email_verification_token_repository_impl import EmailVerificationTokenRepositoryImpl
from app.infrastructure.email.smtp_email_sender import SmtpEmailSender
from app.infrastructure.services.rate_limiter import rate_limiter
from app.domain.entities.email_verification_token import EmailVerificationToken

user_repo = UserRepositoryImpl()
token_repo = EmailVerificationTokenRepositoryImpl()
email_sender = SmtpEmailSender()

def _sha256_hex(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

class EmailVerificationUseCases:
    async def send_verification(self, db: AsyncSession, email: str, ip: Optional[str], ua: Optional[str]) -> None:
        key = f"emailverify:{email}:{ip}"
        if not rate_limiter.allow(key, settings.email_verification_rate_max_per_key, settings.email_verification_rate_window_seconds):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Trop de requêtes, réessayez plus tard")

        user = await user_repo.get_by_email(db, email)
        if user:
            if getattr(user, "email_verified", False):
                return  

            raw_token = secrets.token_urlsafe(48)
            hashed = _sha256_hex(raw_token)
            entity = EmailVerificationToken(
                user_id=user.id,
                hashed_token=hashed,
                expires_at=EmailVerificationToken.default_expiry(settings.email_verification_token_expire_minutes),
                ip_address=ip,
                user_agent=ua[:255] if ua else None,
            )
            await token_repo.create(db, entity)

            verify_link = f"{settings.frontend_verify_email_url}?token={raw_token}"
            html = (
                f"<p>Hi,</p>"
                f"<p>Please verify your email by clicking the link below.</p>"
                f"<p><a href='{verify_link}'>Verify Email</a></p>"
                f"<p>This link expires in {settings.email_verification_token_expire_minutes} minutes.</p>"
            )
            try:
                await email_sender.send_html(to=email, subject="Verify your email", html=html)
            except Exception:
                pass
        return

    async def confirm_verification(self, db: AsyncSession, raw_token: str, ip: Optional[str], ua: Optional[str]) -> None:
        hashed = _sha256_hex(raw_token)
        entity = await token_repo.get_by_hashed_token(db, hashed)
        if not entity:
            raise HTTPException(status_code=400, detail="Token invalide")
        if entity.used_at is not None:
            raise HTTPException(status_code=400, detail="Token déjà utilisé")
        if datetime.utcnow() > entity.expires_at:
            raise HTTPException(status_code=400, detail="Token expiré")

        await user_repo.set_email_verified(db, entity.user_id, True)
        await token_repo.mark_used(db, entity)
