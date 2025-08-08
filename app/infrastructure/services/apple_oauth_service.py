import base64
import httpx
import json
import time
import urllib.parse
from typing import Any, Dict, Optional

from jose import jwt
from app.config import settings

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

APPLE_AUTH_BASE = "https://appleid.apple.com/auth/authorize"
APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISS = "https://appleid.apple.com"

class AppleOAuthService:
    """
    Apple OAuth2 service:
    - Builds authorize URL with proper scopes and state.
    - Generates client_secret (ES256) with Apple private key (.p8).
    - Exchanges authorization code for tokens.
    - Verifies id_token signature using Apple's JWKS (RS256).
    """

    _jwks_cache: Optional[Dict[str, Any]] = None
    _jwks_fetched_at: float = 0
    _jwks_ttl_seconds: int = 60 * 60  # cache 1h

    def _load_private_key(self) -> str:
        """
        Load Apple .p8 private key from file or env.
        Apple requires ES256 client_secret signed with this key.
        """
        if settings.apple_private_key_path:
            with open(settings.apple_private_key_path, "r") as f:
                return f.read()
        if settings.apple_private_key:
            # Replace escaped newlines if provided as single-line env
            return settings.apple_private_key.replace("\\n", "\n")
        raise RuntimeError("Apple private key not configured")

    def build_authorization_url(self, state: str) -> str:
        params = {
            "client_id": settings.apple_client_id,
            "redirect_uri": settings.apple_callback_url,
            "response_type": "code",        # we exchange 'code' for tokens
            "response_mode": "query",       # callback via query params
            "scope": "name email",
            "state": state,
        }
        return f"{APPLE_AUTH_BASE}?{urllib.parse.urlencode(params)}"

    def _generate_client_secret(self) -> str:
        """
        Create the client_secret JWT (ES256) required by Apple /auth/token.
        Claims:
          iss: Team ID
          iat: now
          exp: now + 20 minutes (can be up to 6 months, but keep short)
          aud: https://appleid.apple.com
          sub: client_id (Service ID)
        Header:
          kid: Apple Key ID
          alg: ES256
        """
        private_key = self._load_private_key()
        now = int(time.time())
        claims = {
            "iss": settings.apple_team_id,
            "iat": now,
            "exp": now + 20 * 60,
            "aud": APPLE_ISS,
            "sub": settings.apple_client_id,
        }
        headers = {
            "kid": settings.apple_key_id,
            "alg": "ES256",
        }
        return jwt.encode(claims, private_key, algorithm="ES256", headers=headers)

    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        client_secret = self._generate_client_secret()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                APPLE_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.apple_callback_url,
                    "client_id": settings.apple_client_id,
                    "client_secret": client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            # Apple returns detailed JSON errors; propagate for debugging
            try:
                payload = resp.json()
            except json.JSONDecodeError:
                resp.raise_for_status()
                payload = {}
            if resp.status_code >= 400:
                raise ValueError(f"Apple token error: {payload}")
            return payload

    async def _fetch_apple_jwks(self) -> Dict[str, Any]:
        # Simple in-memory cache
        now = time.time()
        if self._jwks_cache and (now - self._jwks_fetched_at) < self._jwks_ttl_seconds:
            return self._jwks_cache
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(APPLE_JWKS_URL)
            resp.raise_for_status()
            jwks = resp.json()
        self._jwks_cache = jwks
        self._jwks_fetched_at = now
        return jwks

    @staticmethod
    def _b64url_to_int(val: str) -> int:
        padded = val + "==="  # handle missing padding
        return int.from_bytes(base64.urlsafe_b64decode(padded), "big")

    @staticmethod
    def _rsa_jwk_to_pem(jwk_obj: Dict[str, str]) -> bytes:
        """
        Convert Apple's RSA JWK to PEM to verify JWT signature.
        """
        n = AppleOAuthService._b64url_to_int(jwk_obj["n"])
        e = AppleOAuthService._b64url_to_int(jwk_obj["e"])
        pub = rsa.RSAPublicNumbers(e, n).public_key()
        return pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify id_token issued by Apple:
          - pick correct JWKS key by 'kid'
          - verify signature (RS256)
          - validate issuer and audience
        """
        header = jwt.get_unverified_header(id_token)
        kid = header.get("kid")
        if not kid:
            raise ValueError("Missing kid in id_token header")

        jwks = await self._fetch_apple_jwks()
        keys = jwks.get("keys", [])
        jwk_obj = next((k for k in keys if k.get("kid") == kid), None)
        if not jwk_obj:
            raise ValueError("Apple public key not found for kid")

        pem = self._rsa_jwk_to_pem(jwk_obj)

        payload = jwt.decode(
            id_token,
            pem,
            algorithms=["RS256"],
            audience=settings.apple_client_id,
            issuer=APPLE_ISS,
        )

        ev = payload.get("email_verified")
        if ev in ("false", False, "0", 0):
            raise ValueError("Apple email not verified")

        return payload
