import base64
import hashlib
import json
from typing import Dict, Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from app.config import settings

def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

class JWKSService:
    """
    Build JWKS from the configured RSA public key.
    Also computes a deterministic kid when not provided (RFC 7638 thumbprint).
    """

    def __init__(self):
        with open(settings.jwt_public_key_path, "rb") as f:
            self._pub_pem = f.read()
        self._pub = serialization.load_pem_public_key(self._pub_pem, backend=default_backend())
        if not isinstance(self._pub, rsa.RSAPublicKey):
            raise RuntimeError("Public key is not RSA")

        numbers = self._pub.public_numbers()
        self.n_b64 = _b64url(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big"))
        self.e_b64 = _b64url(numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big"))

        # kid from settings or RFC 7638 thumbprint
        self.kid = settings.jwt_key_id or self._compute_thumbprint()

    def _compute_thumbprint(self) -> str:
        jwk_for_thumb = {"e": self.e_b64, "kty": "RSA", "n": self.n_b64}
        data = json.dumps(jwk_for_thumb, separators=(",", ":"), sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(data).digest()
        return _b64url(digest)

    def get_jwk(self) -> Dict[str, Any]:
        return {
            "kty": "RSA",
            "alg": "RS256",
            "use": "sig",
            "kid": self.kid,
            "n": self.n_b64,
            "e": self.e_b64,
        }

    def get_jwks(self) -> Dict[str, Any]:
        return {"keys": [self.get_jwk()]}
