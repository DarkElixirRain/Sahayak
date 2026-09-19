# app/api/schemas/voice.py
"""Voice API schemas extending conversation contracts.

The voice endpoint accepts an audio payload and returns the original
ConversationResponse plus the transcribed text and generated audio.
"""

from __future__ import annotations

from typing import Optional, Literal

from pydantic import BaseModel, Field

from app.schemas.conversation import ConversationResponse


class AudioPayload(BaseModel):
    """Binary audio data returned to the client.

    The content is base64‑encoded bytes so that JSON can transport it.
    ``format`` follows standard MIME types (e.g., ``audio/mpeg`` or
    ``audio/wav``)."""

    format: str = Field(..., description="MIME type of the audio payload, e.g. 'audio/mpeg'")
    content: str = Field(..., description="Base64‑encoded audio data")


class VoiceConversationResponse(ConversationResponse):
    """Response model for the voice endpoint.

    It includes the original ``ConversationResponse`` fields together with
    the transcript from Speech‑to‑Text and the synthesized audio (or an error).
    """

    transcript: str = Field(..., description="Transcribed user speech")
    audio: Optional[AudioPayload] = Field(None, description="Synthesized speech for the assistant's answer")
    tts_error: Optional[str] = Field(None, description="Error message if TTS generation failed")
    input_mode: Literal["voice"] = Field("voice", description="Indicates the request originated from voice input")
