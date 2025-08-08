import urllib.parse
from typing import Dict, Any
import httpx
from anyio import to_thread
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.config import settings

GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

class GoogleOAuthClient:
    """
    Minimal Google OAuth2 client:
    - Build authorization URL
    - Exchange code for tokens
    - Verify ID token (server-side)
    """
    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        self.scopes = settings.google_oauth_scopes.split()

    def build_authorization_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",  # force refresh_token for dev phase
            "state": state,
        }
        return f"{GOOGLE_AUTH_BASE}?{urllib.parse.urlencode(params)}"

    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=15) as client:
            data = {
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code",
            }
            resp = await client.post(GOOGLE_TOKEN_URL, data=data)
            resp.raise_for_status()
            return resp.json()

    async def verify_id_token(self, id_token_str: str) -> Dict[str, Any]:
        """
        Verifies Google ID Token signature and audience (server-side).
        Uses google-auth library (sync) executed in thread to avoid blocking.
        """
        def _verify():
            request = google_requests.Request()
            return id_token.verify_oauth2_token(
                id_token_str, request, self.client_id
            )
        return await to_thread.run_sync(_verify)
