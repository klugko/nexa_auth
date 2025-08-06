from datetime import datetime, timedelta
from jose import jwt
from app.config import settings

class JWTService:
    def __init__(self):
        with open(settings.jwt_private_key_path, "rb") as f:
            self.private_key = f.read()
        with open(settings.jwt_public_key_path, "rb") as f:
            self.public_key = f.read()

    def create_token(self, subject: str, expires_delta: timedelta) -> str:
        to_encode = {
            "sub": subject,
            "exp": datetime.utcnow() + expires_delta,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(to_encode, self.private_key, algorithm=settings.jwt_algorithm)

    def create_access_token(self, subject: str) -> str:
        return self.create_token(subject, timedelta(minutes=settings.jwt_access_token_expire_minutes))

    def create_refresh_token(self, subject: str) -> str:
        return self.create_token(subject, timedelta(days=settings.jwt_refresh_token_expire_days))

    def decode_token(self, token: str):
        return jwt.decode(token, self.public_key, algorithms=[settings.jwt_algorithm])
