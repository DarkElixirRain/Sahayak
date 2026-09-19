from .base import SpeechToTextProvider, TextToSpeechProvider
from .mock import MockSpeechToTextProvider, MockTextToSpeechProvider
from .google import GoogleSpeechToTextProvider, GoogleTextToSpeechProvider
from app.core.config import settings


def get_speech_to_text_provider() -> SpeechToTextProvider:
    """Factory returning the configured Speech‑to‑Text provider.

    Returns:
        An instance of ``SpeechToTextProvider`` – either the Google implementation
        or the mock implementation depending on ``settings.voice_provider``.
    """
    if settings.voice_provider == "google":
        return GoogleSpeechToTextProvider()
    return MockSpeechToTextProvider()


def get_text_to_speech_provider() -> TextToSpeechProvider:
    """Factory returning the configured Text‑to‑Speech provider.

    Returns:
        An instance of ``TextToSpeechProvider`` – either the Google implementation
        or the mock implementation depending on ``settings.voice_provider``.
    """
    if settings.voice_provider == "google":
        return GoogleTextToSpeechProvider()
    return MockTextToSpeechProvider()
