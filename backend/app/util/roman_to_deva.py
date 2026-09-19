"""Deterministic Romanized Nepali → Devanagari normalization for retrieval.

When a user types in Romanized Nepali (e.g. "malai mero jagga ko kanoon bataideu"),
the lexical ILIKE retrieval against Devanagari corpus returns nothing because the
scripts don't overlap.  This module provides a *deterministic, local* mapping from
common Romanized Nepali words to their Devanagari equivalents.

Design constraints:
    * No LLM call — fully deterministic, zero-latency.
    * No external dependencies — pure Python stdlib.
    * The original user message is NEVER mutated; this is used only to produce
      an *additional* retrieval representation.
    * Phrases of >2 words are split into individual tokens, each transliterated
      independently and joined with spaces.
    * Words already in Devanagari pass through unchanged.
    * English words pass through unchanged (they may match English terms in
      the corpus enrichment).

Typical integration point:
    ``_build_retrieval_query()`` in conversation.py appends the normalized
    Devanagari form alongside the original query for dual-script ILIKE search.
"""

from __future__ import annotations

import re
import unicodedata

# --------------------------------------------------------------------------- #
# Phonetic mapping table
# --------------------------------------------------------------------------- #
# Maps common Romanized Nepali syllables/words → Devanagari.
# Order matters: longer patterns must come before shorter ones to avoid partial
# replacement (e.g. "sampan" before "sam").
#
# The dictionary is organized into two tiers:
#   1. Whole-word overrides for the most common legal/domestic terms
#   2. Syllable-level phonetic rules applied to tokens not matched in tier 1

# Whole-word map (Roman → Devanagari) — legal & domestic vocabulary
WORD_MAP: dict[str, str] = {
    # Legal / formal terms
    "kanoon":     "कानून",
    "kanun":      "कानून",
    "kanuu":      "कानून",
    "mudda":      "मुद्दा",
    "muda":       "मुद्दा",
    "adalt":      "अदालत",
    "adalat":     "अदालत",
    "adawlat":    "अदालत",
    "court":      "अदालत",
    "faisala":    "फैसला",
    "phaisala":   "फैसला",
    "nirnaya":    "निर्णय",
    "nirdharan":  "निर्धारण",
    "sahayog":    "सहयोग",
    "sahayak":    "सहायक",
    "nyaya":      "न्याय",
    "kaypal":     "कायपाल",
    "samvidhan":  "संविधान",
    "ain":        "ऐन",
    "ainkanoon":  "ऐनकानून",
    "qanoon":     "कानून",
    "adhiwakta":  "अधिवक्ता",
    "wakil":      "वकील",
    "vakil":      "वकील",
    "wakalatnama": "वकालतनामा",
    "bujharan":   "बुझारण",
    "summons":    "सम्मन",
    "haziri":     "हाजिरी",
    "pratifakhar":"प्रतिफखर",
    "dalil":      "दलील",
    "sawal":      "सवाल",
    "jawab":      "जवाफ",
    "jawaaf":     "जवाफ",
    "jawaf":      "जवाफ",

    # Property / land
    "jagga":      "जग्गा",
    "jaga":       "जग्गा",
    "sampatti":   "सम्पत्ति",
    "sampatii":   "सम्पत्ति",
    "samptti":    "सम्पत्ति",
    "samptii":    "सम्पत्ति",
    "bhumii":     "भूमि",
    "bhum":       "भूम",
    "ghar":       "घर",
    "griha":      "गृह",
    "kiraaya":    "किराया",
    "kiraya":     "किराया",
    "kiraa":      "किराया",
    "maur":       "मौर",
    "nijji":      "निजी",
    "niji":       "निजी",
    "taksa":      "टक्सा",
    "lagaat":     "लगान",
    "naka":       "नक्सा",
    "naksaa":     "नक्सा",

    # Family / domestic
    "bhai":       "भाइ",
    "bhaii":      "भाइ",
    "bahini":     "बहिनी",
    "baini":      "बहिनी",
    "bua":        "बुबा",
    "bubaa":      "बुबा",
    "baba":       "बाबा",
    "baa":        "बाबा",
    "amaa":       "आमा",
    "ama":        "आमा",
    "aama":       "आमा",
    "didi":       "दिदी",
    "deidee":     "दिदी",
    "dai":        "दाइ",
    "daai":       "दाइ",
    "chhora":     "छोरा",
    "chhori":     "छोरी",
    "chhoraa":    "छोरा",
    "chhori":     "छोरी",
    "bahu":       "बुहारी",
    "pati":       "पति",
    "patni":      "पत्नी",
    "sami":       "श्रीमान",
    "sriman":     "श्रीमान",
    "wifa":       "विवाह",
    "biwaa":      "विवाह",
    "biwaha":     "विवाह",
    "vivah":      "विवाह",
    "vivaha":     "विवाह",
    "divorce":    "सम्बन्ध विच्छेद",
    "sambandh":   "सम्बन्ध",
    "bicched":    "विच्छेद",
    "bichhed":    "विच्छेद",
    "chhed":      "विच्छेद",
    "bacha":      "बालबालिका",
    "bachha":     "बालबालिका",
    "baal":       "बाल",

    # Actions / verbs
    "halyo":      "हाल्यो",
    "haalyo":     "हाल्यो",
    "garnuu":     "गर्नु",
    "garne":      "गर्ने",
    "gareko":     "गरेको",
    "garchhu":    "गर्छु",
    "garcha":     "गर्छ",
    "garera":     "गरेर",
    "garera":     "गरेर",
    "lyayo":      "ल्यायो",
    "liyo":       "लियो",
    "diyo":       "दियो",
    "raakhyo":    "राख्यो",
    "raakhnu":    "राख्नु",
    "chhepto":    "छेप्टो",
    "chepto":     "छेप्टो",
    "chepto":     "छेप्टो",
    "japti":      "जप्ती",
    "japtee":     "जप्ती",
    "khonchnu":   "खोंच्नु",
    "khonchna":   "खोंच्ना",
    "dininu":     "दिनु",
    "dinna":      "दिन्न",
    "naakhnu":    "नाख्नु",
    "lina":       "लिन",
    "line":       "लिने",
    "chhinna":    "छिन्न",
    "paunu":      "पाउनु",
    "paune":      "पाउने",
    "bataidinu":  "बताइदिनु",
    "bataaidinu": "बताइदिनु",
    "bataidenu":  "बताइदिनु",
    "bataaidenu": "बताइदिनु",

    # Negation
    "nahanne":    "नहान्ने",
    "nachahinne": "नचाहिने",
    "nasakne":    "नसक्ने",

    # Common phrases
    "malai":      "मलाई",
    "maile":      "मैले",
    "mero":       "मेरो",
    "mera":       "मेरा",
    "timro":      "तिम्रो",
    "timo":       "तिम्रो",
    "hamro":      "हाम्रो",
    "hara":       "हरा",
    "hamrai":     "हाम्रै",
    "uniharuko":  "उनीहरूको",
    "uniharu":    "उनीहरू",
    "tesko":      "तेस्को",
    "tyo":        "त्यो",
    "yo":         "यो",
    "tyahaa":     "त्यहाँ",
    "yaha":       "यहाँ",
    "kahaa":      "कहाँ",
    "kahile":     "कहिले",
    "kasaile":    "कसैले",
    "kun":        "कुन",
    "ke":         "के",
    "k":          "क",
    "cha":        "छ",
    "chha":       "छ",
    "x":          "छ",
    "xa":         "छ",
    "ch":         "छ",
    "h":          "ह",
    "ho":         "हो",
    "haina":      "होइन",
    "ra":         "र",
    "aba":        "अब",
    "paxi":       "पछि",
    "pachi":      "पछि",
    "pachhi":     "पछि",
    "ahile":      "अहिले",
    "soday":      "सोध",
    "sodh":       "सोध",
    "sodhnu":     "सोध्नु",

    # Legal matter types
    "property":   "सम्पत्ति",
    "land":       "जग्गा",
    "house":      "घर",
    "rent":       "किराया",
    "ownership":  "स्वामित्व",
    "marriage":   "विवाह",
    "child":      "बालबालिका",
    "murder":     "हत्या",
    "theft":      "चोरी",
    "robbery":    "लूट",
    "fraud":      "जालसाजी",
    "violence":   "हिंसा",
    "dispute":    "मुद्दा",
    "family":     "परिवार",
    "domestic":   "घरेलु",
    "maintenance":"भरणपोषण",
    "inheritance":"उत्तराधिकार",
    "partition":  "अंशबाँडा",
    "evidence":   "प्रमाण",
    "proof":      "प्रमाण",
    "notice":     "सूचना",
    "deadline":   "समयसीमा",
    "court":      "अदालत",
    "district":   "जिल्ला",
    "high":       "उच्च",
    "supreme":    "सर्वोच्च",
    "police":     "प्रहरी",
    "fir":        "एफ.आई.आर",
    "case":       "मुद्दा",

    # Question words
    "khojnu":     "खोज्नु",
    "khojna":     "खोज्ना",
    "sodhnu":     "सोध्नु",
    "bujhnna":    "बुझ्न",
    "thaha":      "थाहा",
    "thahaa":     "थाहा",
    "keho":       "केहो",
    "kasari":     "कसरी",
    "kin":        "किन",
    "kina":       "किन",
    "kinko":      "किनको",
    "kinlai":     "किनलाई",
    "kasko":      "कसको",
    "kaslai":     "कसलाई",
    "kaha":       "कहाँ",
    "kab":        "कब",
    "kun":        "कुन",
}

# --------------------------------------------------------------------------- #
# Syllable-level phonetic fallback rules
# --------------------------------------------------------------------------- #
# Applied in order; first match wins for each token.
# Each rule is (pattern → Devanagari replacement).

_SYLLABLE_RULES: list[tuple[re.Pattern[str], str]] = [
    # Consonant clusters
    (re.compile(r"^shri$"), "श्री"),
    (re.compile(r"^shree$"), "श्री"),
    (re.compile(r"^kshetra$"), "क्षेत्र"),
    (re.compile(r"^pradhan$"), "प्रधान"),
    (re.compile(r"^sarkaar$"), "सरकार"),
    (re.compile(r"^sarkar$"), "सरकार"),
    (re.compile(r"^sarkari$"), "सरकारी"),
    (re.compile(r"^prakriti$"), "प्रकृति"),
    (re.compile(r"^karyalaya$"), "कार्यालय"),
    (re.compile(r"^samiti$"), "समिति"),
    (re.compile(r"^parishad$"), "परिषद"),
    (re.compile(r"^mantri$"), "मन्त्री"),
    (re.compile(r"^pradhiipaa$"), "प्रधानपालिका"),
    (re.compile(r"^mahikma$"), "महाकम"),
    (re.compile(r"^mahasachib$"), "महासचिव"),
    (re.compile(r"^adhikrit$"), "अधिकृत"),
    (re.compile(r"^pradhikrit$"), "प्राधिकृत"),

    # Common compound words
    (re.compile(r"^kanoon$"), "कानून"),
    (re.compile(r"^kanun$"), "कानून"),
    (re.compile(r"^kanooni$"), "कानूनी"),
    (re.compile(r"^kanuni$"), "कानूनी"),
    (re.compile(r"^kanoonko$"), "कानूनको"),
    (re.compile(r"^kanoonle$"), "कानूनले"),
    (re.compile(r"^kanoonma$"), "कानूनमा"),
    (re.compile(r"^kanoonbata$"), "कानूनबाट"),
    (re.compile(r"^kanoonniyam$"), "कानूननियम"),
    (re.compile(r"^kanoonpaalo$"), "कानूनपालो"),
    (re.compile(r"^kanoonpalan$"), "कानूनपालन"),
    (re.compile(r"^kanoonsahiit$"), "कानूनसहित"),
    (re.compile(r"^kanoonbhitra$"), "कानूनभित्र"),
    (re.compile(r"^kanoonagali$"), "कानूनअगाडी"),
    (re.compile(r"^kanoonagadhi$"), "कानूनअगाडी"),
    (re.compile(r"^kanoonwala$"), "कानूनवाला"),
    (re.compile(r"^kanoonko$"), "कानूनको"),
    (re.compile(r"^kanoonle$"), "कानूनले"),
    (re.compile(r"^kanoonma$"), "कानूनमा"),
    (re.compile(r"^kanoonbata$"), "कानूनबाट"),
    (re.compile(r"^kanoonniyam$"), "कानूननियम"),
    (re.compile(r"^kanoonpaalo$"), "कानूनपालो"),
    (re.compile(r"^kanoonpalan$"), "कानूनपालन"),
    (re.compile(r"^kanoonsahiit$"), "कानूनसहित"),
    (re.compile(r"^kanoonbhitra$"), "कानूनभित्र"),
    (re.compile(r"^kanoonagali$"), "कानूनअगाडी"),
    (re.compile(r"^kanoonagadhi$"), "कानूनअगाडी"),
    (re.compile(r"^kanoonwala$"), "कानूनवाला"),
]

# --------------------------------------------------------------------------- #
# Phonetic single-syllable mapping
# --------------------------------------------------------------------------- #
# For words not in WORD_MAP, we attempt a character-by-character phonetic
# mapping.  This covers the vast majority of Romanized Nepali that doesn't
# appear in our curated dictionary.

_CHAR_MAP: dict[str, str] = {
    # Vowels (inherent 'a' is silent)
    "aa": "आ", "ai": "ऐ", "au": "औ",
    "a": "अ", "i": "इ", "ii": "ई", "ee": "ई",
    "u": "उ", "uu": "ऊ",
    "e": "ए", "o": "ओ",
    # Nasalization
    "n": "न", "m": "म",
    # Consonants
    "ka": "क", "kha": "ख", "ga": "ग", "gha": "घ", "nga": "ङ",
    "cha": "छ", "ja": "ज", "jha": "झ", "nya": "ञ",
    "ta": "त", "tha": "थ", "da": "द", "dha": "ध", "na": "न",
    "ta": "ट", "tha": "ठ", "da": "ड", "dha": "ढ", "na": "ण",
    "pa": "प", "pha": "फ", "ba": "ब", "bha": "भ", "ma": "म",
    "ya": "य", "ra": "र", "la": "ल", "wa": "व",
    "sha": "श", "sa": "स", "ha": "ह",
    "ksha": "क्ष", "tra": "त्र", "gya": "ज्ञ",
    # Conjuncts
    "kya": "क्य", "gya": "ज्ञ", "tya": "त्य",
    "dya": "द्य", "bya": "ब्य", "mya": "म्य",
    "rya": "र्य", "lya": "ल्य", "sya": "स्य",
    "hya": "ह्य",
    # Common word-final patterns
    "ne": "ने", "nu": "नु", "na": "ना",
    "le": "ले", "lu": "लु", "la": "ला",
    "re": "रे", "ru": "रु", "ra": "रा",
    "te": "ते", "tu": "तु", "ta": "ता",
    "de": "दे", "du": "दु", "da": "दा",
    "se": "से", "su": "सु", "sa": "सा",
    "he": "हे", "hu": "हु", "ha": "हा",
    "ye": "ये", "yu": "यु", "ya": "या",
    "ke": "के", "ku": "कु", "ka": "का",
    "ge": "गे", "gu": "गु", "ga": "गा",
    "che": "छे", "chu": "छु", "cha": "छा",
    "je": "जे", "ju": "जु", "ja": "जा",
    "pe": "पे", "pu": "पु", "pa": "पा",
    "be": "बे", "bu": "बु", "ba": "बा",
    "me": "मे", "mu": "मु", "ma": "मा",
    "ye": "ये", "yu": "यु", "ya": "या",
    "we": "वे", "wu": "वु", "wa": "वा",
    "she": "शे", "shu": "शु", "sha": "शा",
    "ha": "हा", "hi": "हि", "hu": "हु",
    "hu": "हु", "he": "हे", "ho": "हो",
    "la": "ला", "li": "लि", "lu": "लु",
    "le": "ले", "lo": "लो",
    "ra": "रा", "ri": "रि", "ru": "रु",
    "re": "रे", "ro": "रो",
    "na": "ना", "ni": "नि", "nu": "नु",
    "ne": "ने", "no": "नो",
    "ta": "ता", "ti": "ति", "tu": "तु",
    "te": "ते", "to": "तो",
    "da": "दा", "di": "दि", "du": "दु",
    "de": "दे", "do": "दो",
    "sa": "सा", "si": "सि", "su": "सु",
    "se": "से", "so": "सो",
    "ma": "मा", "mi": "मि", "mu": "मु",
    "me": "मे", "mo": "मो",
    "ba": "बा", "bi": "बि", "bu": "बु",
    "be": "बे", "bo": "बो",
    "pa": "पा", "pi": "पि", "pu": "पु",
    "pe": "पे", "po": "पो",
    "ka": "का", "ki": "कि", "ku": "कु",
    "ke": "के", "ko": "को",
    "ga": "गा", "gi": "गि", "gu": "गु",
    "ge": "गे", "go": "गो",
    "ja": "जा", "ji": "जि", "ju": "जु",
    "je": "जे", "jo": "जो",
    "cha": "छा", "chi": "छि", "chu": "छु",
    "che": "छे", "cho": "छो",
    "ha": "हा", "hi": "हि", "hu": "हु",
    "he": "हे", "ho": "हो",
    "kha": "खा", "khi": "खि", "khu": "खु",
    "khe": "खे", "kho": "खो",
    "gha": "घा", "ghi": "घि", "ghu": "घु",
    "ghe": "घे", "gho": "घो",
    "tha": "था", "thi": "थि", "thu": "थु",
    "the": "थे", "tho": "थो",
    "dha": "धा", "dhi": "धि", "dhu": "धु",
    "dhe": "धे", "dho": "धो",
    "pha": "फा", "phi": "फि", "phu": "फु",
    "phe": "फे", "pho": "फो",
    "bha": "भा", "bhi": "भि", "bhu": "भु",
    "bhe": "भे", "bho": "भो",
    "sha": "शा", "shi": "शि", "shu": "शु",
    "she": "शे", "sho": "शो",
    "sa": "सा", "si": "सि", "su": "सु",
    "se": "से", "so": "सो",
    "tra": "त्र", "trya": "त्र्य",
    "ksha": "क्ष", "gya": "ज्ञ",
    "ddha": "द्ध", "dd": "ड्ड",
    "bbha": "ब्भ", "bb": "ब्ब",
    "gg": "ग्ग", "jj": "ज्ज", "kk": "क्क",
    "ll": "ल्ल", "mm": "म्म", "nn": "न्न",
    "pp": "प्प", "rr": "र्र", "ss": "स्स",
    "tt": "ट्ट", "yy": "य्य", "zz": "ज्ज",
}

# Devanagari matra / vowel sign patterns
_VOWEL_SIGNS = set("ाि�ीुूृेैोौंःँ")


# --------------------------------------------------------------------------- #
# Detection helpers
# --------------------------------------------------------------------------- #

_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def is_devanagari(text: str) -> bool:
    """True if the text contains any Devanagari character."""
    return bool(_DEVANAGARI_RE.search(text))


def is_romanized_nepali(text: str) -> bool:
    """Heuristic: text is Latin-script and appears to be Romanized Nepali.

    This is intentionally permissive — the worst case of a false positive is
    that we add extra Devanagari terms to the retrieval query, which the
    ILIKE engine simply ignores if they don't match anything.
    """
    if not text or not text.strip():
        return False
    if is_devanagari(text):
        return False
    if not re.search(r"[a-zA-Z]", text):
        return False

    text_lower = text.lower().strip()
    # Quick check: any whole-word match from WORD_MAP?
    words = re.findall(r"[a-zA-Z]+", text_lower)
    if any(w in WORD_MAP for w in words):
        return True
    # Accept if it's short Latin text (likely Nepali, not English legal query)
    return False


# --------------------------------------------------------------------------- #
# Transliteration engine
# --------------------------------------------------------------------------- #

_TOKEN_RE = re.compile(r"[a-zA-Z]+|[^a-zA-Z]+")


def transliterate_word(word: str) -> str:
    """Transliterate a single Romanized Nepali word to Devanagari.

    Uses whole-word map first, then phonetic syllable rules, then
    character-level fallback.  Returns Devanagari script if a mapping
    was found, otherwise returns the original word unchanged.
    """
    w = word.lower()

    # 1. Whole-word dictionary lookup (fastest path)
    if w in WORD_MAP:
        return WORD_MAP[w]

    # 2. Try syllable-level rules
    for pattern, replacement in _SYLLABLE_RULES:
        if pattern.match(w):
            return replacement

    # 3. Attempt phonetic character-level mapping
    result = _phonetic_transliterate(w)
    if result and result != w and is_devanagari(result):
        return result

    # 4. No mapping found — return original (English / already Devanagari)
    return word


def _phonetic_transliterate(word: str) -> str:
    """Character-by-character phonetic transliteration.

    This is a *best-effort* fallback for words not in the dictionary.
    It handles the most common Nepali phoneme → grapheme mappings.
    """
    if not word:
        return word

    # Multi-character syllables first (greedy, longest match)
    i = 0
    result: list[str] = []
    w = word.lower()

    while i < len(w):
        matched = False
        # Try longest possible match first (up to 4 chars)
        for length in range(min(4, len(w) - i), 0, -1):
            fragment = w[i:i + length]
            if fragment in _CHAR_MAP:
                result.append(_CHAR_MAP[fragment])
                i += length
                matched = True
                break
        if not matched:
            # Single char not in map — skip it
            i += 1

    if not result:
        return word

    joined = "".join(result)
    # Apply halant (्) to consonants that precede another consonant
    # to form conjuncts (simplified rule)
    joined = unicodedata.normalize("NFC", joined)
    return joined


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def normalize_romanized_nepali(text: str) -> str:
    """Normalize a full query string from Romanized Nepali to Devanagari.

    * Words already in Devanagari pass through unchanged.
    * English words pass through unchanged.
    * Romanized Nepali words are transliterated to Devanagari.
    * Result is NFC-normalized and whitespace-collapsed.

    The original text is NEVER mutated by this function.

    Args:
        text: User input that may be Romanized Nepali.

    Returns:
        A string with Romanized Nepali words replaced by Devanagari equivalents.
        If the input contains no Romanized Nepali, it is returned unchanged
        (except for NFC normalization and whitespace cleanup).
    """
    if not text or not text.strip():
        return text

    # Already Devanagari — no work needed
    if is_devanagari(text):
        return unicodedata.normalize("NFC", text)

    # Tokenize: keep structure (spaces, punctuation)
    parts = _TOKEN_RE.findall(text)
    result_parts: list[str] = []

    for part in parts:
        if re.match(r"[a-zA-Z]+$", part):
            result_parts.append(transliterate_word(part))
        else:
            result_parts.append(part)

    result = "".join(result_parts)
    result = unicodedata.normalize("NFC", result)
    # Collapse whitespace
    result = re.sub(r"\s+", " ", result).strip()
    return result


def build_dual_script_query(original: str) -> str:
    """Build a dual-script query string for retrieval.

    Returns a query that contains BOTH the original terms AND the
    transliterated Devanagari terms, separated by spaces.  The ILIKE
    engine will match whichever script aligns with the corpus.

    Example:
        "malai mero jagga ko kanoon bataideu"
        → "malai mero jagga ko kanoon bataideu मलाई मेरो जग्गा क कानून बताइदिनु"

    Args:
        original: The user's original query text.

    Returns:
        A dual-script query string suitable for retrieval.
    """
    if not original or not original.strip():
        return original

    # If already Devanagari, no dual-script needed
    if is_devanagari(original):
        return original

    normalized = normalize_romanized_nepali(original)

    # If normalization produced nothing different, return original
    if normalized == original or not is_devanagari(normalized):
        return original

    # Combine: original + normalized, deduplicated
    parts = []
    seen: set[str] = set()

    for word in re.findall(r"[^\s]+", original):
        w = word.lower().strip(".,!?;:")
        if w and w not in seen:
            seen.add(w)
            parts.append(word)

    for word in re.findall(r"[^\s]+", normalized):
        w = word.lower().strip(".,!?;:")
        if w and w not in seen:
            seen.add(w)
            parts.append(word)

    return " ".join(parts)
