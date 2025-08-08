from app.application.use_cases.user_use_case import UserUseCases
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.infrastructure.db.session import get_db
from app.infrastructure.security.jwt_service import JWTService

bearer_scheme = HTTPBearer(auto_error=True)
jwt_service = JWTService()
user_uc = UserUseCases()

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Extract and validate Bearer token (RS256). Then fetch user by UUID `sub`.
    """
    token = creds.credentials
    try:
        payload = jwt_service.decode_token(token)  # verifies signature + exp
        sub = payload.get("sub")
        if not sub:
            raise ValueError("Missing sub in token")
        user_id = UUID(sub)  # ensure it's a valid UUID
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")

    user = await user_uc.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur inactif ou introuvable")
    return user
