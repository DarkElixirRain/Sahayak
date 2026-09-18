"""Core configuration for the Sahayak backend."""

import os

from dotenv import load_dotenv

APP_NAME = "Sahayak"
APP_VERSION = "0.1.0"

load_dotenv()


def _parse_cors_origins(raw: str) -> tuple[str, ...]:
    return tuple(origin.strip() for origin in raw.split(",") if origin.strip())


class Settings:
    """Application settings loaded from environment variables.

    Secret values (DATABASE_URL, GROQ_API_KEY) are never logged or exposed
    in API responses.
    """

    app_env: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    database_url: str = os.getenv("DATABASE_URL", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    cors_origins: tuple[str, ...] = _parse_cors_origins(
        os.getenv("CORS_ORIGINS", "http://localhost:3000")
    )


settings = Settings()