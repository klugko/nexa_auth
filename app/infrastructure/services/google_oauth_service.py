import httpx
import urllib.parse
import secrets
from typing import Dict, Any
from app.config import settings

GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_SCOPES = ["openid", "email", "profile"]

class GoogleOAuthService:
    """
    Handles building the Google OAuth2 URL, exchanging code for tokens,
    and verifying the ID token server-side via Google's tokeninfo endpoint.
    """

    def build_authorization_url(self, state: str) -> str:
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_callback_url,
            "response_type": "code",
            "scope": " ".join(GOOGLE_SCOPES),
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_AUTH_BASE}?{urllib.parse.urlencode(params)}"

    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_callback_url,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            return resp.json()

    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify id_token by calling Google's tokeninfo endpoint.
        Ensures 'aud' matches our client_id and token is valid.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(GOOGLE_TOKENINFO_URL, params={"id_token": id_token})
            resp.raise_for_status()
            payload = resp.json()

        # Basic validations
        if payload.get("aud") != settings.google_client_id:
            raise ValueError("Invalid audience on ID token")
        if payload.get("email_verified") not in ("true", True, "1", 1):
            # On tolère email non vérifié si besoin : ici on impose vérifié
            raise ValueError("Email not verified on Google account")

        return payload

    @staticmethod
    def generate_state_nonce() -> str:
        # Nonce supplémentaire si tu veux le renvoyer côté client (optionnel)
        return secrets.token_urlsafe(16)
