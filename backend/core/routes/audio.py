"""Audio routes for the Sahayak MVP voice flow.

For the MVP the app does NOT generate dynamic speech. Every successful AI
response references a single pre-recorded dummy audio file (the same recording
for every response). This module serves that one specific file through the
existing storage abstraction.

Security notes:
- Only a single hardcoded storage key is ever served. There is no
  {path}/{filename} parameter, so arbitrary backend files cannot be exposed.
- No storage credentials, absolute filesystem paths, or database details are
  returned to the client.
"""

import logging
from typing import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from core.services_init import document_service

router = APIRouter(prefix="/audio", tags=["audio"])
logger = logging.getLogger(__name__)

# URL path returned inside /query responses as the "audio_url" field. Clients
# resolve this relative to their configured API base URL.
DUMMY_RESPONSE_AUDIO_URL = "/audio/dummy-response"

# The stored dummy response file (the key inside the configured storage path).
# It was recorded once and is reused for every AI response in the MVP. Real
# dynamic TTS will replace this later.
DUMMY_RESPONSE_AUDIO_KEY = (
    "ElevenLabs_2026-09-20T01_29_55_Roger - Laid-Back, Casual, Resonant"
    "_pre_sp100_s50_sb75_se0_b_m2.mp3"
)
DUMMY_RESPONSE_AUDIO_MEDIA_TYPE = "audio/mpeg"


@router.get("/dummy-response", summary="Serve the dummy response audio")
async def get_dummy_response_audio():
    """Stream the single pre-recorded dummy response audio file."""
    try:
        content = await document_service.storage.download_file("", DUMMY_RESPONSE_AUDIO_KEY)
    except FileNotFoundError:
        logger.warning("Dummy response audio file not found in storage: %s", DUMMY_RESPONSE_AUDIO_KEY)
        raise HTTPException(status_code=404, detail="Dummy response audio not found.") from None
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to read dummy response audio: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to load dummy response audio.") from exc

    def _generate() -> Iterator[bytes]:
        yield content

    return StreamingResponse(
        _generate(),
        media_type=DUMMY_RESPONSE_AUDIO_MEDIA_TYPE,
        headers={
            "Content-Disposition": f'inline; filename="dummy-response.mp3"',
            "Content-Length": str(len(content)),
            "Cache-Control": "public, max-age=3600",
        },
    )