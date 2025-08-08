from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.services.apple_oauth_service import AppleOAuthService
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.repositories.auth_provider_repository_impl import AuthProviderRepositoryImpl
from app.domain.entities.user import User
from app.domain.entities.auth_provider import AuthProvider

jwt_service = JWTService()
apple_service = AppleOAuthService()
user_repo = UserRepositoryImpl()
authp_repo = AuthProviderRepositoryImpl()

PROVIDER_NAME = "apple"
STATE_PURPOSE = "oauth_apple"

class AppleOAuthUseCases:
    def get_login_url(self) -> str:
        # State anti-CSRF signé et très court
        state = jwt_service.create_state_token(STATE_PURPOSE, ttl_seconds=120)
        return apple_service.build_authorization_url(state)

    async def handle_callback(self, db: AsyncSession, code: str, state: str):
        # 1) Vérifier le state
        try:
            jwt_service.verify_state_token(state, STATE_PURPOSE)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="State invalide")

        # 2) Échanger le code
        try:
            tokens = await apple_service.exchange_code_for_tokens(code)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Code invalide: {e}")

        id_token = tokens.get("id_token")
        if not id_token:
            raise HTTPException(status_code=400, detail="ID token manquant")

        # 3) Vérifier le id_token (signature + aud + iss)
        try:
            idp = await apple_service.verify_id_token(id_token)
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"ID token invalide: {e}")

        # 4) Extraire infos
        sub = idp.get("sub")        # identifiant Apple
        email = idp.get("email")    # peut être absent selon les cas
        name = None                 # Apple ne renvoie pas toujours le nom dans id_token
        picture = None

        if not sub:
            raise HTTPException(status_code=400, detail="Profil Apple incomplet")

        # fallback email (unique) si absent
        if not email:
            email = f"{sub}@privaterelay.appleid.com"

        # 5) Trouver/Créer User
        user = await user_repo.get_by_email(db, email)
        if not user:
            user = User(email=email, hashed_password=None, is_active=True)
            user = await user_repo.create(db, user)

        # 6) Lier AuthProvider
        link = await authp_repo.get_by_provider_and_user_id(db, PROVIDER_NAME, sub)
        if not link:
            link = AuthProvider(
                provider_name=PROVIDER_NAME,
                provider_user_id=sub,
                user_id=user.id,
            )
            await authp_repo.create(db, link)

        # 7) Émettre nos JWT (RS256)
        access_token = jwt_service.create_access_token(str(user.id))
        refresh_token = jwt_service.create_refresh_token(str(user.id))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": name,
                "picture": picture,
            },
            "token_type": "bearer",
        }
