from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://kasirpro:kasirpro@db:5432/kasirpro"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "changeme-use-strong-secret-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "kasirpro"
    MINIO_SECRET_KEY: str = "kasirpro123"
    MINIO_BUCKET: str = "kasirpro"

    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "https://kasirpro.yourdomain.com"]
    RATE_LIMIT_PER_MINUTE: int = 60

    SENTRY_DSN: str = ""
    ENVIRONMENT: str = "development"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Fonnte WhatsApp
    FONNTE_TOKEN: str = ""
    FONNTE_API_URL: str = "https://api.fonnte.com/send"

    class Config:
        env_file = ".env"


settings = Settings()
