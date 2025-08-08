import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    app_name: str = os.getenv("APP_NAME", "Nexa Auth API")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")

    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "postgres")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", 5432))
    db_name: str = os.getenv("DB_NAME", "nexa_auth_db")

    jwt_private_key_path: str = os.getenv("JWT_PRIVATE_KEY_PATH")
    jwt_public_key_path: str = os.getenv("JWT_PUBLIC_KEY_PATH")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "RS256")
    jwt_access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 15))
    jwt_refresh_token_expire_days: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7))
    jwt_key_id: str = os.getenv("JWT_KEY_ID", "")  
    jwks_cache_seconds: int = int(os.getenv("JWKS_CACHE_SECONDS", 3600))
    
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_callback_url: str = os.getenv("GOOGLE_CALLBACK_URL", "")
    
    apple_client_id: str = os.getenv("APPLE_CLIENT_ID", "")
    apple_team_id: str = os.getenv("APPLE_TEAM_ID", "")
    apple_key_id: str = os.getenv("APPLE_KEY_ID", "")
    apple_private_key_path: str = os.getenv("APPLE_PRIVATE_KEY_PATH", "")
    apple_private_key: str = os.getenv("APPLE_PRIVATE_KEY", "")
    apple_callback_url: str = os.getenv("APPLE_CALLBACK_URL", "")
    
    microsoft_client_id: str = os.getenv("MICROSOFT_CLIENT_ID", "")
    microsoft_client_secret: str = os.getenv("MICROSOFT_CLIENT_SECRET", "")
    microsoft_tenant_id: str = os.getenv("MICROSOFT_TENANT_ID", "common")
    microsoft_callback_url: str = os.getenv("MICROSOFT_CALLBACK_URL", "")
    
    # SMTP
    smtp_host: str = os.getenv("SMTP_HOST", "localhost")
    smtp_port: int = int(os.getenv("SMTP_PORT", 1025))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from: str = os.getenv("SMTP_FROM", "[email protected]")
    smtp_use_tls: int = int(os.getenv("SMTP_USE_TLS", 0))
    smtp_use_ssl: int = int(os.getenv("SMTP_USE_SSL", 0))

    # Password reset
    password_reset_token_expire_minutes: int = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", 30))
    password_reset_rate_window_seconds: int = int(os.getenv("PASSWORD_RESET_RATE_WINDOW_SECONDS", 900))
    password_reset_rate_max_per_key: int = int(os.getenv("PASSWORD_RESET_RATE_MAX_PER_KEY", 5))
    frontend_reset_password_url: str = os.getenv("FRONTEND_RESET_PASSWORD_URL", "http://localhost:3000/reset-password")

    @property
    def database_url(self):
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

settings = Settings()
