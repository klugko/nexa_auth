from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.services.microsoft_oauth_service import MicrosoftOAuthService
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.repositories.auth_provider_repository_impl import AuthProviderRepositoryImpl
from app.domain.entities.user import User
from app.domain.entities.auth_provider import AuthProvider

jwt_service = JWTService()
ms_service = MicrosoftOAuthService()
user_repo = UserRepositoryImpl()
authp_repo = AuthProviderRepositoryImpl()

PROVIDER_NAME = "microsoft"
STATE_PURPOSE = "oauth_microsoft"

class MicrosoftOAuthUseCases:
    def get_login_url(self) -> str:
        # CSRF protection via short-lived signed state
        state = jwt_service.create_state_token(STATE_PURPOSE, ttl_seconds=180)
        return ms_service.build_authorization_url(state)

    async def handle_callback(self, db: AsyncSession, code: str, state: str):
        # 1) Validate state
        try:
            jwt_service.verify_state_token(state, STATE_PURPOSE)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="State invalide")

        # 2) Exchange code for tokens
        try:
            tokens = await ms_service.exchange_code_for_tokens(code)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Code invalide: {e}")

        id_token = tokens.get("id_token")
        access_token = tokens.get("access_token")
        if not id_token or not access_token:
            raise HTTPException(status_code=400, detail="Tokens Microsoft manquants")

        # 3) Verify id_token signature/claims against Microsoft JWKS
        try:
            idp = await ms_service.verify_id_token(id_token)
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"ID token invalide: {e}")

        # 4) Verify access_token by calling Microsoft Graph /me (also fetch profile)
        try:
            me = await ms_service.get_graph_me(access_token)
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Access token invalide (Graph): {e}")

        # 5) Extract profile info
        sub = idp.get("sub") or idp.get("oid")  # 'sub' is stable; 'oid' is object id
        # try email from id_token first
        email = idp.get("email") or idp.get("preferred_username")
        # fallback from Graph
        email = email or me.get("mail") or me.get("userPrincipalName")

        display_name = me.get("displayName")
        picture = None  # Graph photo endpoint nécessite un appel binaire séparé

        if not sub:
            raise HTTPException(status_code=400, detail="Profil Microsoft incomplet (sub manquant)")
        if not email:
            # As a last resort, construct a synthetic unique email
            email = f"{sub}@login.microsoftonline.com"

        # 6) Find or create User
        user = await user_repo.get_by_email(db, email)
        if not user:
            user = User(email=email, hashed_password=None, is_active=True)
            user = await user_repo.create(db, user)

        # 7) Link AuthProvider
        link = await authp_repo.get_by_provider_and_user_id(db, PROVIDER_NAME, sub)
        if not link:
            link = AuthProvider(
                provider_name=PROVIDER_NAME,
                provider_user_id=sub,
                user_id=user.id,
            )
            await authp_repo.create(db, link)

        # 8) Issue our local RS256 JWTs
        access_jwt = jwt_service.create_access_token(str(user.id))
        refresh_jwt = jwt_service.create_refresh_token(str(user.id))

        return {
            "access_token": access_jwt,
            "refresh_token": refresh_jwt,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": display_name,
                "picture": picture,
            },
            "token_type": "bearer",
        }
