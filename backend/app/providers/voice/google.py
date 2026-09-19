from __future__ import annotations

import os
from typing import Optional

from google.cloud import speech
from google.cloud import texttospeech

from .base import SpeechToTextProvider, TextToSpeechProvider


class GoogleSpeechToTextProvider(SpeechToTextProvider):
    def __init__(self) -> None:
        # The client will automatically use GOOGLE_APPLICATION_CREDENTIALS env var
        self.client = speech.SpeechClient()

    async def transcribe(self, audio_bytes: bytes, mime_type: str) -> str:
        audio = speech.RecognitionAudio(content=audio_bytes)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code="ne-NP",  # default Nepali; can be overridden later
            alternative_language_codes=["en-US"],
        )
        response = self.client.recognize(config=config, audio=audio)
        # Concatenate alternatives
        transcripts = [result.alternatives[0].transcript for result in response.results]
        return " ".join(transcripts)


class GoogleTextToSpeechProvider(TextToSpeechProvider):
    def __init__(self) -> None:
        self.client = texttospeech.TextToSpeechClient()
        self.voice_name = os.getenv("TTS_VOICE_NAME", "ne-NP-Standard-A")

    async def synthesize(self, text: str, language: str) -> bytes:
        # language codes like "ne" or "en"
        input_ = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="ne-NP" if language == "ne" else "en-US",
            name=self.voice_name,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        response = self.client.synthesize_speech(
            input=input_, voice=voice, audio_config=audio_config
        )
        return response.audio_content
