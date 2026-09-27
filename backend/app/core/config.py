from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CareerPilot API"
    ENV: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://careerpilot:careerpilot@db:5432/careerpilot"

    # Auth
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Redis (rate limiting)
    REDIS_URL: str = "redis://redis:6379/0"

    # SMTP / email (verification + password reset). If SMTP_HOST is empty,
    # emails are logged to the console instead of sent — fine for local dev
    # and CI, set real values in production.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@careerpilot.local"
    FRONTEND_URL: str = "http://localhost:5173"
    EMAIL_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # File upload
    MAX_UPLOAD_SIZE_MB: int = 5
    ALLOWED_UPLOAD_EXTENSIONS: list[str] = [".pdf", ".docx"]
    UPLOAD_DIR: str = "/app/uploads"

    # Third-party
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""

    # AI analysis (Google Gemini — free tier via https://aistudio.google.com/apikey)
    GEMINI_API_KEY: str = ""

    # Rate limiting. 30/min was too aggressive — a single dashboard load
    # (list resumes + any follow-up calls) plus normal fast interaction can
    # exceed that quickly and lock a real user out. This is a generous
    # per-IP ceiling meant to catch abuse/brute force, not normal use.
    RATE_LIMIT_PER_MINUTE: int = 300

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
