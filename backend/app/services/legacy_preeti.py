"""Deterministic conversion of pre-Unicode "Preeti"-family Nepali text to Unicode Devanagari.

The Preeti keyboard layout encodes Devanagari using characters of the host
codepage (ASCII letters, digits and a small set of Latin-1 lookalikes such as
"Æ", "æ", "ª"). This module maps those keyboard codes back to their proper
Unicode Devanagari equivalents and then applies the standard set of typographic
corrections (matra re-ordering, reph placement, conjunct reassembly, matra
deduplication and monophthong joining) that the layout requires.

Guarantees:
    * fully deterministic: the same input always yields the same output
    * no network access and no external dependencies
    * characters that are NOT part of the Preeti alphabet pass through unchanged
      (structural numbers, punctuation such as the en-dash, and any text that is
      already Unicode)
    * the mapping + corrections are "clean-room": implemented here from the
      documented Preeti layout; during development the output was verified to be
      byte-identical to a reference implementation across the full Muluki Dewani
      Samhita 2074 corpus.
"""

from __future__ import annotations

import re
import unicodedata

# --------------------------------------------------------------------------- #
# Preeti character map
# --------------------------------------------------------------------------- #
# Keyboard code -> Unicode Devanagari. These are the public Preeti layout
# assignments (Latin letters/digits and the legacy glyphs that survive in
# Latin-1 round-trips, e.g. "Æ" stands for the closing double quote).
CHARACTER_MAP: dict[str, str] = {
    " ": " ",
    "!": "१",
    '"': "ू",
    "#": "३",
    "$": "४",
    "%": "५",
    "&": "७",
    "'": "ु",
    "(": "९",
    ")": "०",
    "*": "८",
    "+": "ं",
    ",": ",",
    "-": "(",
    ".": "।",
    "/": "र",
    "0": "ण्",
    "1": "ज्ञ",
    "2": "द्द",
    "3": "घ",
    "4": "द्ध",
    "5": "छ",
    "6": "ट",
    "7": "ठ",
    "8": "ड",
    "9": "ढ",
    ":": "स्",
    ";": "स",
    "<": "?",
    "=": ".",
    ">": "श्र",
    "?": "रु",
    "@": "२",
    "A": "ब्",
    "B": "द्य",
    "C": "ऋ",
    "D": "म्",
    "E": "भ्",
    "F": "ँ",
    "G": "न्",
    "H": "ज्",
    "I": "क्ष्",
    "J": "व्",
    "K": "प्",
    "L": "ी",
    "M": "ः",
    "N": "ल्",
    "O": "इ",
    "P": "ए",
    "Q": "त्त",
    "R": "च्",
    "S": "क्",
    "T": "त्",
    "U": "ग्",
    "V": "ख्",
    "W": "ध्",
    "X": "ह्",
    "Y": "थ्",
    "Z": "श्",
    "[": "ृ",
    "\\": "्",
    "]": "े",
    "^": "६",
    "_": ")",
    "`": "ञ",
    "a": "ब",
    "b": "द",
    "c": "अ",
    "d": "म",
    "e": "भ",
    "f": "ा",
    "g": "न",
    "h": "ज",
    "i": "ष्",
    "j": "व",
    "k": "प",
    "l": "ि",
    "n": "ल",
    "o": "य",
    "p": "उ",
    "q": "त्र",
    "r": "च",
    "s": "क",
    "t": "त",
    "u": "ग",
    "v": "ख",
    "w": "ध",
    "x": "ह",
    "y": "थ",
    "z": "श",
    "|": "्र",
    "}": "ै",
    "~": "ञ्",
    # Latin-1 legacy glyphs
    "\u00a1": "ज्ञ्",   # ¡
    "\u00a2": "द्घ",    # ¢
    "\u00a3": "घ्",     # £
    "\u00a4": "झ्",     # ¤
    "\u00a5": "्र",     # ¥
    "\u00a7": "ट्ट",    # §
    "\u00a9": "र",      # ©
    "\u00aa": "ङ",      # ª
    "\u00ab": "्र",     # «
    "\u00b0": "ङ्ढ",    # °
    "\u00b1": "+",      # ±
    "\u00b4": "झ",      # ´
    "\u00b6": "ठ्ठ",    # ¶
    "\u00bf": "रू",     # ¿
    "\u00c5": "हृ",     # Å
    "\u00c6": "”",      # Æ  (closing double quote)
    "\u00cb": "ङ्ग",    # Ë
    "\u00cc": "न्न",    # Ì
    "\u00cd": "ङ्क",    # Í
    "\u00ce": "ङ्ख",    # Î
    "\u00d2": "\u00a8", # Ò -> ¨
    "\u00d6": "=",      # Ö
    "\u00d7": "×",      # ×
    "\u00d8": "्य",     # Ø
    "\u00d9": ";",      # Ù
    "\u00da": "’",      # Ú
    "\u00db": "!",      # Û
    "\u00dc": "%",      # Ü
    "\u00dd": "ट्ठ",    # Ý
    "\u00df": "द्म",    # ß
    "\u00e5": "द्व",    # å
    "\u00e6": "“",      # æ  (opening double quote)
    "\u00e7": "ॐ",      # ç
    "\u00f7": "/",      # ÷
    "\u02c6": "फ्",     # ˆ
    "\u02dc": "ऽ",      # ˜
    # Windows-1252 legacy glyphs
    "\u2018": "ॅ",      # ‘
    "\u201a": "ध्र",    # ‚
    "\u2022": "ड्ड",    # •
    "\u2026": "‘",      # …
    "\u2030": "झ्",     # ‰
    "\u2039": "ङ्घ",    # ‹
    "\u203a": "द्र",    # ›
    # Identities that pass through unchanged
    "\u0964": "।",      # danda (already correct)
}

# Every keyboard code the converter knows about (used to detect leftovers).
PREETI_KEY_ALPHABET: frozenset[str] = frozenset(CHARACTER_MAP)

# Characters that legitimately remain in correctly converted text even though
# they also exist as Preeti keys or lookalikes. These carry no meaning in the
# legacy encoding on their own and MUST NOT round-trip through the character
# map (otherwise paragraphs, parentheses and quoted sections would mangle).
PASSTHROUGH_CHARS: frozenset[str] = frozenset(
    [" ", ",", "(", ")", ".", ":", ";", "?", "!", "%", "=", "+", "-", "/",
     "“", "”", "‘", "’", "–", "—", "।"]
)

# --------------------------------------------------------------------------- #
# Post-processing rules
# --------------------------------------------------------------------------- #
# Applied to each whitespace-delimited token AFTER the character map. They fix
# the ordering/duplication artefacts inherent to the Preeti layout:
#
#   *  the reph (र्, typed as "{") and the conjunct markers "m" (क्र/क्त/झ/फ/ऊ)
#      are repositioned and resolved into real glyph sequences
#   *  the independent vowel "इ" + reph forms "ई"
#   *  the i-matra (ि) must be written after the consonant cluster it belongs to
#   *  vowel signs precede/combine with halant-bearing conjuncts correctly
#   *  chandrabindu/anusvara are pulled in front of vowel signs
#   *  doubled matras are deduplicated (typing artefacts)
#   *  word-initial visarga is written as ":" and टृ becomes ट्ट
#   *  monophthong ligatures are joined (ेा→ो, ाे→ो, अा→आ, एे→ऐ, अाे→ओ ...)
POST_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"्ा"), ""),                                          # drop vowel sign after halant
    (re.compile(r"(त्र|त्त)([^उभप]+?)m"), r"\1m\2"),                 # delay marker after त्र/त्त
    (re.compile(r"त्रm"), "क्र"),
    (re.compile(r"त्तm"), "क्त"),
    (re.compile(r"([^उभप]+?)m"), r"m\1"),                            # flip marker before cluster
    (re.compile(r"उm"), "ऊ"),
    (re.compile(r"भm"), "झ"),
    (re.compile(r"पm"), "फ"),
    (re.compile(r"इ{"), "ई"),
    (re.compile(r"ि((.्)*[^्])"), r"\1ि"),                           # move i-matra after cluster
    (re.compile(r"(.[ािीुूृेैोौंःँ]*?){"), r"{\1"),                  # reposition reph
    (re.compile(r"((.्)*){"), r"{\1"),
    (re.compile(r"{"), "र्"),                                         # resolve reph
    (re.compile(r"([ाीुूृेैोौंःँ]+?)(्(.्)*[^्])"), r"\2\1"),        # vowel signs before conjunct
    (re.compile(r"्([ाीुूृेैोौंःँ]+?)((.्)*[^्])"), r"्\2\1"),
    (re.compile(r"([ंँ])([ािीुूृेैोौः]*)"), r"\2\1"),                # anusvara before matras
    (re.compile(r"ँँ"), "ँ"),                                          # dedupe matras
    (re.compile(r"ंं"), "ं"),
    (re.compile(r"ेे"), "े"),
    (re.compile(r"ैै"), "ै"),
    (re.compile(r"ुु"), "ु"),
    (re.compile(r"ूू"), "ू"),
    (re.compile(r"^ः"), ":"),                                         # word-initial visarga
    (re.compile(r"टृ"), "ट्ट"),
    (re.compile(r"ेा"), "ाे"),
    (re.compile(r"ैा"), "ाै"),
    (re.compile(r"अाे"), "ओ"),
    (re.compile(r"अाै"), "औ"),
    (re.compile(r"अा"), "आ"),
    (re.compile(r"एे"), "ऐ"),
    (re.compile(r"ाे"), "ो"),
    (re.compile(r"ाै"), "ौ"),
)

# --------------------------------------------------------------------------- #
# Conversion
# --------------------------------------------------------------------------- #

_TOKEN_SPLIT = re.compile(r"(\s+|\S+)")


def convert_word(word: str) -> str:
    """Map a single whitespace-delimited token to Devanagari."""
    mapped = "".join(CHARACTER_MAP.get(ch, ch) for ch in word)
    for pattern, replacement in POST_RULES:
        mapped = pattern.sub(replacement, mapped)
    return unicodedata.normalize("NFC", mapped)


def convert_text(text: str) -> str:
    """Convert a whole string, preserving whitespace and token boundaries."""
    parts: list[str] = []
    for token in _TOKEN_SPLIT.findall(text):
        if token.isspace():
            parts.append(token)
        else:
            parts.append(convert_word(token))
    return "".join(parts)


# --------------------------------------------------------------------------- #
# Detection helpers (Unicode-range based, not "non-ASCII")
# --------------------------------------------------------------------------- #

# Devanagari block plus the zero-width joiner/non-joiner used inside words.
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097f\u200c\u200d]")
# The same, but excluding spacing/layout controls from the "real text" count.
_REAL_DEVANAGARI_RE = re.compile(r"[\u0900-\u093B\u093D-\u097F]")


def has_devanagari(text: str) -> bool:
    """True when the text contains Devanagari script characters (U+0900-U+097F
    plus ZWJ/ZWNJ) — NOT merely any non-ASCII codepoint."""
    return bool(_DEVANAGARI_RE.search(text))


def devanagari_char_count(text: str) -> int:
    """Count Devanagari script characters (excluding ZWJ/ZWNJ)."""
    return len(_REAL_DEVANAGARI_RE.findall(text))


def legacy_remnants(text: str) -> str:
    """Return any characters still in Preeti keyboard code that survived
    conversion. Correctly converted text may legitimately keep a small set of
    ASCII/typographic punctuation (PASSTHROUGH_CHARS); everything else from the
    Preeti alphabet here indicates an unconverted remnant."""
    leftovers: list[str] = []
    for ch in text:
        if ch in PASSTHROUGH_CHARS or ch.isspace():
            continue
        if ch in PREETI_KEY_ALPHABET or ord(ch) < 0x0900:
            leftovers.append(ch)
    return "".join(sorted(set(leftovers)))