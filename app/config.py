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
    
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_callback_url: str = os.getenv("GOOGLE_CALLBACK_URL", "")

    @property
    def database_url(self):
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

settings = Settings()
