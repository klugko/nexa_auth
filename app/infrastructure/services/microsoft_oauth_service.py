import base64
import time
import urllib.parse
from typing import Any, Dict, Optional

import httpx
from jose import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from app.config import settings

# Endpoints (tenant-aware)
def _ms_base_auth() -> str:
    return f"https://login.microsoftonline.com/{settings.microsoft_tenant_id}/oauth2/v2.0/authorize"

def _ms_base_token() -> str:
    return f"https://login.microsoftonline.com/{settings.microsoft_tenant_id}/oauth2/v2.0/token"

def _ms_openid_config() -> str:
    # v2.0 OpenID configuration (expose jwks_uri, issuer, etc.)
    return f"https://login.microsoftonline.com/{settings.microsoft_tenant_id}/v2.0/.well-known/openid-configuration"

MS_SCOPES = [
    "openid",
    "profile",
    "email",
    "offline_access",
    "User.Read",  # required to call Microsoft Graph /me
]

GRAPH_ME = "https://graph.microsoft.com/v1.0/me"

class MicrosoftOAuthService:
    """
    Microsoft OAuth2 service:
    - Builds authorize URL with proper scopes and state
    - Exchanges authorization code for tokens
    - Verifies id_token signature via Microsoft JWKS (RS256) + aud/iss
    - Calls Microsoft Graph /me to validate access_token and fetch profile
    """

    _openid_cache: Optional[Dict[str, Any]] = None
    _openid_fetched_at: float = 0
    _openid_ttl_seconds: int = 60 * 60  # 1h

    @staticmethod
    def _b64url_to_int(val: str) -> int:
        padded = val + "==="
        return int.from_bytes(base64.urlsafe_b64decode(padded), "big")

    @staticmethod
    def _rsa_jwk_to_pem(jwk_obj: Dict[str, str]) -> bytes:
        n = MicrosoftOAuthService._b64url_to_int(jwk_obj["n"])
        e = MicrosoftOAuthService._b64url_to_int(jwk_obj["e"])
        pub = rsa.RSAPublicNumbers(e, n).public_key()
        return pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    async def _fetch_openid_config(self) -> Dict[str, Any]:
        now = time.time()
        if self._openid_cache and (now - self._openid_fetched_at) < self._openid_ttl_seconds:
            return self._openid_cache
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(_ms_openid_config())
            r.raise_for_status()
            data = r.json()
        self._openid_cache = data
        self._openid_fetched_at = now
        return data

    def build_authorization_url(self, state: str) -> str:
        params = {
            "client_id": settings.microsoft_client_id,
            "response_type": "code",
            "redirect_uri": settings.microsoft_callback_url,
            "response_mode": "query",
            "scope": " ".join(MS_SCOPES),
            "state": state,
            "prompt": "select_account",  # UX better
        }
        return f"{_ms_base_auth()}?{urllib.parse.urlencode(params)}"

    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                _ms_base_token(),
                data={
                    "client_id": settings.microsoft_client_id,
                    "scope": " ".join(MS_SCOPES),
                    "code": code,
                    "redirect_uri": settings.microsoft_callback_url,
                    "grant_type": "authorization_code",
                    "client_secret": settings.microsoft_client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            # Return JSON errors verbatim to help debugging
            payload = r.json()
            if r.status_code >= 400:
                raise ValueError(f"Microsoft token error: {payload}")
            return payload

    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify Microsoft id_token:
        - Get key by 'kid' from jwks_uri
        - Verify signature (RS256)
        - Validate audience (our client_id) and issuer (contains tenant tid)
        """
        # read header for kid
        header = jwt.get_unverified_header(id_token)
        kid = header.get("kid")
        if not kid:
            raise ValueError("Missing 'kid' in id_token header")

        # fetch OpenID config to get jwks_uri
        cfg = await self._fetch_openid_config()
        jwks_uri = cfg.get("jwks_uri")
        if not jwks_uri:
            raise ValueError("jwks_uri not found in OpenID configuration")

        # fetch JWKS
        async with httpx.AsyncClient(timeout=10.0) as client:
            jwks_resp = await client.get(jwks_uri)
            jwks_resp.raise_for_status()
            keys = jwks_resp.json().get("keys", [])

        jwk_obj = next((k for k in keys if k.get("kid") == kid), None)
        if not jwk_obj:
            raise ValueError("Microsoft public key not found for kid")

        # build PEM to verify
        pem = self._rsa_jwk_to_pem(jwk_obj)

        # issuer depends on actual tenant ID embedded in claims (tid)
        unverified = jwt.get_unverified_claims(id_token)
        tid = unverified.get("tid")
        if not tid:
            raise ValueError("Missing 'tid' in id_token claims")
        expected_iss = f"https://login.microsoftonline.com/{tid}/v2.0"

        payload = jwt.decode(
            id_token,
            pem,
            algorithms=["RS256"],
            audience=settings.microsoft_client_id,
            issuer=expected_iss,
        )
        return payload

    async def get_graph_me(self, access_token: str) -> Dict[str, Any]:
        """
        Call Microsoft Graph /me, proves access_token validity and fetches richer profile.
        Requires the 'User.Read' scope granted during authorization.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                GRAPH_ME,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            data = r.json()
            if r.status_code >= 400:
                raise ValueError(f"Graph /me error: {data}")
            return data
