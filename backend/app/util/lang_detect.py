# app/util/lang_detect.py
"""Simple language detection utilities used by the voice endpoint.

The detection is lightweight and based solely on the presence of Devanagari
Unicode characters. It is *not* authoritative and is only used for metadata
purposes (e.g., to hint the TTS language).
"""

import re
from typing import Literal

# Regular expression matching any Devanagari character.
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def detect_language(text: str) -> Literal["ne", "en", "mixed"]:
    """Detect whether a string is Nepali, English or mixed.

    Args:
        text: Input text to analyse.

    Returns:
        "ne" if the text contains Devanagari characters and no Latin letters,
        "en" if it contains Latin letters and no Devanagari, otherwise "mixed".
    """
    has_deva = bool(_DEVANAGARI_RE.search(text))
    has_latin = bool(re.search(r"[A-Za-z]", text))
    if has_deva and not has_latin:
        return "ne"
    if has_latin and not has_deva:
        return "en"
    return "mixed"
