from itsdangerous import URLSafeSerializer
from app.config import settings

_signer = URLSafeSerializer(settings.oauth_state_secret, salt="oauth-state")

def make_state(payload: dict) -> str:
    return _signer.dumps(payload)

def verify_state(state: str) -> dict:
    return _signer.loads(state)
