# app/util/audio_validator.py
"""Utility functions for validating uploaded audio files.

The voice endpoint must enforce both size (max 5 MB) and duration (max 30 s)
constraints. WAV files are validated using the standard library ``wave``
module. MP3 files are validated with ``mutagen`` if it is available; otherwise
the validator raises an informative error.
"""

import io
import wave
from typing import Tuple

from fastapi import HTTPException

# Configuration – mirrors settings in ``app.core.config`` but kept local to avoid
# a hard import cycle for this utility module.
MAX_AUDIO_SIZE_MB = 5
MAX_AUDIO_DURATION_SEC = 30


def _get_mime_type(filename: str) -> str:
    """Return a simple MIME type based on the file extension.

    Only ``.wav`` and ``.mp3`` are supported. The function is deliberately
    lightweight – the endpoint already receives the ``content_type`` from the
    client, but having a fallback helps when the client omits it.
    """
    lc = filename.lower()
    if lc.endswith(".wav"):
        return "audio/wav"
    if lc.endswith(".mp3"):
        return "audio/mpeg"
    raise HTTPException(status_code=422, detail="Unsupported audio format. Only WAV and MP3 are allowed.")


def _validate_size(audio_bytes: bytes) -> None:
    """Validate that the payload does not exceed ``MAX_AUDIO_SIZE_MB``.

    ``audio_bytes`` is the raw content read from the ``UploadFile`` stream.
    """
    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > MAX_AUDIO_SIZE_MB:
        raise HTTPException(
            status_code=422,
            detail=f"Audio file too large: {size_mb:.2f} MiB > {MAX_AUDIO_SIZE_MB} MiB",
        )


def _wav_duration(audio_bytes: bytes) -> float:
    """Calculate duration of a WAV file using the ``wave`` module.

    Returns duration in seconds.
    """
    with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
        frames = wav.getnframes()
        rate = wav.getframerate()
        return frames / float(rate)


def _mp3_duration(audio_bytes: bytes) -> float:
    """Calculate duration of an MP3 file using ``mutagen`` if available.

    The function imports ``mutagen`` lazily; if the library is missing a clear
    ``HTTPException`` is raised so the caller can fallback to size‑only
    validation or report an unsupported format.
    """
    try:
        from mutagen.mp3 import MP3
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="MP3 duration validation requires the optional 'mutagen' package. Install it or use WAV.",
        ) from exc
    audio = MP3(io.BytesIO(audio_bytes))
    return audio.info.length


def validate_audio(audio_bytes: bytes, filename: str) -> Tuple[str, bytes]:
    """Validate size and duration of an uploaded audio payload.

    Args:
        audio_bytes: Raw bytes from the uploaded file.
        filename: Original filename – used to infer MIME type.

    Returns:
        A tuple ``(mime_type, audio_bytes)`` that can be passed directly to the
        provider implementations.
    """
    # Size check first – cheap and prevents unnecessarily parsing large files.
    _validate_size(audio_bytes)

    mime_type = _get_mime_type(filename)
    # Duration check depending on format.
    if mime_type == "audio/wav":
        duration = _wav_duration(audio_bytes)
    else:  # audio/mpeg (MP3)
        duration = _mp3_duration(audio_bytes)

    if duration > MAX_AUDIO_DURATION_SEC:
        raise HTTPException(
            status_code=422,
            detail=f"Audio duration too long: {duration:.1f}s > {MAX_AUDIO_DURATION_SEC}s",
        )
    return mime_type, audio_bytes
