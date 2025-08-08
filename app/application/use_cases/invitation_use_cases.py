import hashlib
import secrets
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infrastructure.services.rate_limiter import rate_limiter
from app.infrastructure.email.smtp_email_sender import SmtpEmailSender
from app.domain.entities.invitation import Invitation
from app.infrastructure.repositories.invitation_repository_impl import InvitationRepositoryImpl
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.repositories.role_repository_impl import RoleRepositoryImpl
from app.infrastructure.security.password_hash import hash_password
from app.infrastructure.security.jwt_service import JWTService

inv_repo = InvitationRepositoryImpl()
user_repo = UserRepositoryImpl()
role_repo = RoleRepositoryImpl()
email_sender = SmtpEmailSender()
jwt_service = JWTService()

def _sha256_hex(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

class InvitationUseCases:
    async def create_invitation(
        self,
        db: AsyncSession,
        *,
        inviter_id,
        inviter_email: str,
        target_type: Optional[str],
        target_id: Optional[str],
        invitee_email: str,
        ip: Optional[str],
        ua: Optional[str],
    ) -> None:
        key = f"invite:{inviter_id}:{invitee_email}:{ip}"
        if not rate_limiter.allow(key, settings.invitation_rate_max_per_key, settings.invitation_rate_window_seconds):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Trop de requêtes, réessayez plus tard")

        raw_token = secrets.token_urlsafe(48)
        hashed = _sha256_hex(raw_token)

        entity = Invitation(
            email=invitee_email,
            inviter_id=inviter_id,
            hashed_token=hashed,
            status="pending",
            target_type=target_type,
            target_id=target_id,
            expires_at=Invitation.default_expiry(settings.invitation_expire_minutes),
            ip_address=ip,
            user_agent=ua[:255] if ua else None,
        )
        await inv_repo.create(db, entity)

        accept_link = f"{settings.frontend_accept_invite_url}?token={raw_token}"

        html = (
            f"<p>Hello,</p>"
            f"<p><b>{inviter_email}</b> invited you to join the platform.</p>"
            f"<p><a href='{accept_link}'>Accept Invitation</a></p>"
            f"<p>This link expires in {settings.invitation_expire_minutes} minutes.</p>"
        )

        try:
            await email_sender.send_html(to=invitee_email, subject="You're invited", html=html)
        except Exception:
            pass

    async def accept_invitation(
        self,
        db: AsyncSession,
        *,
        raw_token: str,
        first_name: Optional[str],
        last_name: Optional[str],
        password: Optional[str],
    ):
        hashed = _sha256_hex(raw_token)
        inv = await inv_repo.get_by_hashed_token(db, hashed)
        if not inv or inv.status != "pending":
            raise HTTPException(status_code=400, detail="Invitation invalide")

        if datetime.utcnow() > inv.expires_at:
            raise HTTPException(status_code=400, detail="Invitation expirée")

        user = await user_repo.get_by_email(db, inv.email)
        if not user:
            from app.domain.entities.user import User
            hashed_pwd = hash_password(password) if password else None
            user = User(
                email=inv.email,
                hashed_password=hashed_pwd,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                email_verified=True,  
            )
            user = await user_repo.create(db, user)
        else:
            if not user.is_active:
                raise HTTPException(status_code=403, detail="Compte désactivé")
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if password:
                user.hashed_password = hash_password(password)
            await db.commit()

        role_user = await role_repo.get_by_name(db, "user")
        if role_user:
            await role_repo.add_role_to_user(db, user.id, role_user)

        await inv_repo.mark_used(db, inv)

        access_token = jwt_service.create_access_token(str(user.id))
        refresh_token = jwt_service.create_refresh_token(str(user.id))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "token_type": "bearer",
        }
