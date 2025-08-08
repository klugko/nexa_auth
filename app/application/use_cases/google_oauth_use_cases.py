from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.services.google_oauth_service import GoogleOAuthService
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.repositories.auth_provider_repository_impl import AuthProviderRepositoryImpl
from app.domain.entities.user import User
from app.domain.entities.auth_provider import AuthProvider

jwt_service = JWTService()
google_service = GoogleOAuthService()
user_repo = UserRepositoryImpl()
authp_repo = AuthProviderRepositoryImpl()

PROVIDER_NAME = "google"
STATE_PURPOSE = "oauth_google"

class GoogleOAuthUseCases:
    def get_login_url(self) -> str:
        # Génère un state signé (60s)
        state = jwt_service.create_state_token(STATE_PURPOSE, ttl_seconds=120)
        return google_service.build_authorization_url(state)

    async def handle_callback(self, db: AsyncSession, code: str, state: str):
        # Vérifier le state (anti-CSRF)
        try:
            jwt_service.verify_state_token(state, STATE_PURPOSE)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="State invalide")

        # 1) Échanger le code contre tokens
        try:
            tokens = await google_service.exchange_code_for_tokens(code)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code invalide")

        id_token = tokens.get("id_token")
        if not id_token:
            raise HTTPException(status_code=400, detail="ID token manquant")

        # 2) Vérifier id_token côté Google
        try:
            id_payload = await google_service.verify_id_token(id_token)
        except Exception:
            raise HTTPException(status_code=401, detail="ID token invalide")

        # 3) Extraire infos clefs
        sub = id_payload.get("sub")                  # Google user id
        email = id_payload.get("email")
        name = id_payload.get("name")
        picture = id_payload.get("picture")

        if not sub or not email:
            raise HTTPException(status_code=400, detail="Profil Google incomplet")

        # 4) Trouver ou créer User
        user = await user_repo.get_by_email(db, email)
        if not user:
            # Crée un compte "passwordless" (hashed_password = None)
            user = User(email=email, hashed_password=None, is_active=True)
            user = await user_repo.create(db, user)

        # 5) Lier AuthProvider si non existant
        link = await authp_repo.get_by_provider_and_user_id(db, PROVIDER_NAME, sub)
        if not link:
            link = AuthProvider(
                provider_name=PROVIDER_NAME,
                provider_user_id=sub,
                user_id=user.id
            )
            await authp_repo.create(db, link)

        # 6) Émettre nos JWT locaux (access + refresh)
        access_token = jwt_service.create_access_token(str(user.id))
        refresh_token = jwt_service.create_refresh_token(str(user.id))

        # Tu peux renvoyer aussi quelques infos profil si utile
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": name,
                "picture": picture,
            },
            "token_type": "bearer"
        }
