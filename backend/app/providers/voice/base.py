import abc
from typing import Awaitable


class SpeechToTextProvider(abc.ABC):
    @abc.abstractmethod
    async def transcribe(self, audio_bytes: bytes, mime_type: str) -> str:
        """Transcribe audio bytes to text.

        Args:
            audio_bytes: Raw audio data.
            mime_type: MIME type of the audio (e.g., 'audio/wav').
        Returns:
            The transcribed text.
        """
        raise NotImplementedError


class TextToSpeechProvider(abc.ABC):
    @abc.abstractmethod
    async def synthesize(self, text: str, language: str) -> bytes:
        """Synthesize speech from text.

        Args:
            text: The text to speak.
            language: Language code (e.g., 'ne', 'en').
        Returns:
            Audio bytes (e.g., MP3).
        """
        raise NotImplementedError
