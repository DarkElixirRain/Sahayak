"""Core configuration for the Sahayak backend."""

import os

from dotenv import load_dotenv

APP_NAME = "Sahayak"
APP_VERSION = "0.1.0"

load_dotenv()


def _parse_cors_origins(raw: str) -> tuple[str, ...]:
    return tuple(origin.strip() for origin in raw.split(",") if origin.strip())


def _env_float(name: str, default: float) -> float:
    """Read a float setting, falling back to ``default`` on bad input."""
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


class Settings:
    """Application settings loaded from environment variables.

    Secret values (DATABASE_URL, LLM_API_KEY, GROQ_API_KEY) are never logged or
    exposed in API responses.
    """

    app_env: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    database_url: str = os.getenv("DATABASE_URL", "")
    cors_origins: tuple[str, ...] = _parse_cors_origins(
        os.getenv("CORS_ORIGINS", "http://localhost:3000")
    )

    # --- Authentication ----------------------------------------------------
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "insecure_default_secret_for_development_only")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))


    # --- LLM provider (Phase 5) -------------------------------------------
    # The project already used GROQ_API_KEY before the provider abstraction
    # existed, so LLM_API_KEY takes precedence and GROQ_API_KEY remains a
    # supported fallback (and the default provider stays "groq").
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq").strip().lower() or "groq"
    llm_api_key: str = os.getenv("LLM_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    # NOTE: the model id must be one the account can actually access.
    # Default: llama-3.1-8b-instant (fast, available on all Groq tiers as of
    # 2025). Override with LLM_MODEL env var. A bad model id surfaces as a
    # controlled ``provider_error`` (never a crash).
    llm_model: str = os.getenv("LLM_MODEL", "llama-3.1-8b-instant").strip()
    llm_base_url: str = os.getenv("LLM_BASE_URL", "").strip()
    llm_timeout_seconds: float = _env_float("LLM_TIMEOUT_SECONDS", 30.0)
    # --- NyayaLM / Ollama (local) -----------------------------------------
    # Set LLM_PROVIDER=ollama or LLM_PROVIDER=nyayalm to use a local Ollama
    # instance. No API key is required. Default model is NyayaLM 1.7B Q4_K_M.
    nyayalm_model: str = os.getenv("NYAYALM_MODEL", "hf.co/chhatramani/nyayalm1.7B_civil9law:Q4_K_M").strip()
    nyayalm_base_url: str = os.getenv("NYAYALM_URL", "http://localhost:11434").strip()
    # --- Voice integration -------------------------------------------------
    voice_provider: str = os.getenv("VOICE_PROVIDER", "mock").strip().lower() or "mock"
    max_audio_size_mb: int = int(os.getenv("MAX_AUDIO_SIZE_MB", "5"))
    max_audio_duration_sec: int = int(os.getenv("MAX_AUDIO_DURATION_SEC", "30"))
    

    @property
    def llm_configured(self) -> bool:
        """True when an API key is present. The key is never returned."""
        return bool(self.llm_api_key.strip())

    @property
    def is_database_configured(self) -> bool:
        """Return True if DATABASE_URL is set and non‑empty.
        Used by tests to safely skip real‑corpus tests when no live DB is available.
        """
        return bool(self.database_url.strip())


settings = Settings()