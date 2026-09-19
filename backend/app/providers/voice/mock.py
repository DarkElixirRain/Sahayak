from .base import SpeechToTextProvider, TextToSpeechProvider


class MockSpeechToTextProvider(SpeechToTextProvider):
    async def transcribe(self, audio_bytes: bytes, mime_type: str) -> str:
        # For testing, simply return a placeholder string.
        # In integration tests, this can be monkey‑patched to return specific text.
        return "mock transcription"


class MockTextToSpeechProvider(TextToSpeechProvider):
    async def synthesize(self, text: str, language: str) -> bytes:
        # Return a tiny MP3 header as dummy audio data.
        # Real tests will not validate audio content, only that a value is returned.
        return b"ID3\x03\x00\x00\x00\x00\x00\x00"
