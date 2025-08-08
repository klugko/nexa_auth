import hashlib
import secrets
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.repositories.password_reset_token_repository_impl import PasswordResetTokenRepositoryImpl
from app.infrastructure.email.smtp_email_sender import SmtpEmailSender
from app.infrastructure.services.rate_limiter import rate_limiter
from app.domain.entities.password_reset_token import PasswordResetToken
from app.infrastructure.security.password_hash import hash_password

user_repo = UserRepositoryImpl()
token_repo = PasswordResetTokenRepositoryImpl()
email_sender = SmtpEmailSender()

def _sha256_hex(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

class PasswordResetUseCases:
    async def request_reset(self, db: AsyncSession, email: str, ip: Optional[str], ua: Optional[str]) -> None:
        # Rate limit per (email+ip)
        key = f"pwdreset:{email}:{ip}"
        if not rate_limiter.allow(key, settings.password_reset_rate_max_per_key, settings.password_reset_rate_window_seconds):
            # Message générique pour éviter l'énumération d'emails
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Trop de requêtes, réessayez plus tard")

        user = await user_repo.get_by_email(db, email)
        # Toujours répondre de manière générique pour ne pas divulguer l'existence
        if user:
            # generate secure token (not stored in clear)
            raw_token = secrets.token_urlsafe(48)  # ~ 64 chars
            hashed = _sha256_hex(raw_token)
            entity = PasswordResetToken(
                user_id=user.id,
                hashed_token=hashed,
                expires_at=PasswordResetToken.default_expiry(settings.password_reset_token_expire_minutes),
                ip_address=ip,
                user_agent=ua[:255] if ua else None,
            )
            await token_repo.create(db, entity)

            # Build link for frontend
            reset_link = f"{settings.frontend_reset_password_url}?token={raw_token}"
            # Render simple HTML inline (template file also available)
            html = (
                f"<p>Hi,</p>"
                f"<p>Click the link below to reset your password (valid {settings.password_reset_token_expire_minutes} minutes):</p>"
                f"<p><a href='{reset_link}'>Reset Password</a></p>"
                f"<p>If you didn't request this, ignore this email.</p>"
            )
            try:
                await email_sender.send_html(to=email, subject="Reset your password", html=html)
            except Exception:
                # In dev, failing email should not leak; log in real app
                pass

        # reply generic
        return

    async def confirm_reset(self, db: AsyncSession, raw_token: str, new_password: str, ip: Optional[str], ua: Optional[str]) -> None:
        hashed = _sha256_hex(raw_token)
        entity = await token_repo.get_by_hashed_token(db, hashed)
        if not entity:
            raise HTTPException(status_code=400, detail="Token invalide")
        if entity.used_at is not None:
            raise HTTPException(status_code=400, detail="Token déjà utilisé")
        if datetime.utcnow() > entity.expires_at:
            raise HTTPException(status_code=400, detail="Token expiré")

        # get user and update password
        from app.domain.entities.user import User  # to avoid circulars at import-time
        res = await db.execute(
            # lightweight select to fetch user (we could use repo, but we already import it elsewhere)
            # still, we keep consistency with repo:
            # using user_repo.get_by_id for clarity
            )
        user = await user_repo.get_by_id(db, entity.user_id)
        if not user:
            raise HTTPException(status_code=400, detail="Utilisateur introuvable")

        user.hashed_password = hash_password(new_password)
        await db.commit()

        # mark token as used
        await token_repo.mark_used(db, entity)
        # Option: purge other expired tokens
        try:
            await token_repo.delete_expired(db)
        except Exception:
            pass

        # Note: For stronger security, you can also force logout by blacklisting refresh tokens
        # or bumping a token_version on the user and checking it in JWT; not implemented here to keep scope focused.
