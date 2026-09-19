from typing import Generator

from fastapi import Depends

from app.core.config import settings
from app.providers.voice import get_voice_provider, SpeechToTextProvider, TextToSpeechProvider


def get_stt_provider() -> Generator[SpeechToTextProvider, None, None]:
    """FastAPI dependency that yields the configured Speech‑to‑Text provider.
    The provider is instantiated via the factory in ``app.providers.voice``.
    """
    provider = get_voice_provider(settings.voice_provider)
    if not isinstance(provider, SpeechToTextProvider):
        raise RuntimeError("Configured voice provider does not implement SpeechToTextProvider")
    yield provider


def get_tts_provider() -> Generator[TextToSpeechProvider, None, None]:
    """FastAPI dependency that yields the configured Text‑to‑Speech provider."""
    provider = get_voice_provider(settings.voice_provider)
    if not isinstance(provider, TextToSpeechProvider):
        raise RuntimeError("Configured voice provider does not implement TextToSpeechProvider")
    yield provider
