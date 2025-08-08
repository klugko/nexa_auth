from fastapi import APIRouter
from app.infrastructure.security.jwks_service import JWKSService

router = APIRouter(prefix="/.well-known", tags=["Well-Known"])

@router.get("/jwks.json", summary="JWKS public keys", description="Exposes RSA public keys for JWT verification (RS256).")
async def jwks():
    """
    Public endpoint for other services to download our RSA public key(s).
    """
    svc = JWKSService()
    return svc.get_jwks()
