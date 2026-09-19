"""Conversation service - Phase 5: grounded legal assistant with legal intake.

Pipeline for every user turn:

    question -> greeting short-circuit (small talk only, never legal content)
             -> analysis -> case context extraction -> missing information identification
             -> targeted follow-up questions (if needed) -> context accumulation
             -> retrieval (verified_only) -> grounding context
             -> LLM generation -> citations -> safe response

Guarantees:

* legal answers are generated only from **verified** retrieved provisions
* citations are built from database rows, never from model output
* if no verified context exists, or the LLM is unavailable, the user gets a
  clear, honest fallback instead of a fabricated answer
* every outcome is labelled with a ``status`` so clients can tell "no match",
  "matches exist but are unverified", "generation unavailable", "retrieval
  error" and "pure greeting" apart
* conversation context is remembered across turns to avoid repetitive questions
* clarification questions are targeted and prioritized based on missing critical information
* case context is maintained throughout the conversation to avoid asking the same questions
* distinguishes between explicitly provided information, inferred information, and unknowns
* pure greetings/small talk never enter the legal retrieval pipeline and
  never trigger the legal "no verified provision" fallback text

Follows the project conventions: raw SQL via psycopg (no ORM), repository
pattern, structured exception handling, no secret exposure, Unicode-safe text.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.core.exceptions import ApiError
from app.db.session import get_connection
from app.repositories.conversation import ConversationRepository
from app.services.case_context import CaseContext, CaseContextManager, get_case_context_manager
from app.services.knowledge_retrieval import (
    STATUS_UNVERIFIED_ONLY,
    retrieve_legal_context,
)
from app.services.legal_grounding import (
    build_citations,
    build_context_block,
    build_system_prompt,
    build_user_message,
    citation_validation_failed_answer,
    context_entry_count,
    default_follow_up_questions,
    detect_language,
    disclaimer_for,
    extract_cited_sections,
    generation_unavailable_answer,
    insufficient_context_answer,
    normalize_section_number,
    retrieval_error_answer,
    strip_urls_from_answer,
)
from app.services.llm import LLMError, LLMProvider, get_llm_provider

logger = logging.getLogger("app.services.conversation")

# Outcome labels returned to clients (also mirrored in the response schema).
STATUS_ANSWERED = "answered"
STATUS_NO_VERIFIED_CONTEXT = "no_verified_context"
STATUS_NO_MATCH = "no_match"
STATUS_LLM_UNAVAILABLE = "llm_unavailable"
STATUS_RETRIEVAL_ERROR = "retrieval_error"
# New: pure greetings/small talk. Distinct from every legal outcome above so
# clients can tell "the user just said hi" apart from "we searched and found
# nothing" - they are not the same situation and should not share copy.
STATUS_GREETING = "greeting"

MAX_HISTORY_MESSAGES = 6

# Maximum follow-up questions returned per turn.
MAX_FOLLOW_UP = 2

# ---------------------------------------------------------------------------
# Greeting / small-talk detection
# ---------------------------------------------------------------------------
# Greetings ("hi", "namaste", ...) are not legal questions. Routing them
# through case-context extraction and retrieval either (a) pollutes nothing
# useful into the accumulated case context, or (b) - as reported - produces
# the exact same "no verified legal provision" fallback text as a genuine
# legal question that failed extraction, which reads as a bug to the user
# even when the retrieval/grounding logic itself is working correctly.
#
# Detection here uses the same explicit, auditable keyword/pattern matching
# already used everywhere else in this file (see _extract_case_context) -
# never an LLM guess, and never a shortcut for legal content. A message that
# mixes a greeting with real legal content ("hi mero bhai le mudda halyo")
# is deliberately NOT treated as a greeting: the legal content must still
# reach the grounded retrieval pipeline below.
# ---------------------------------------------------------------------------
_GREETING_WORDS = {
    "hi", "hii", "hiii", "hello", "hey", "yo",
    "namaste", "namaskar", "namaskaar",
    "नमस्ते", "नमस्कार",
}

_GREETING_MESSAGES = _GREETING_WORDS | {
    "hi there", "hello there", "hey there",
    "good morning", "good afternoon", "good evening",
    "k cha", "k xa", "kasto cha", "kasto xa",
    "sanchai cha", "sanchai hunuhuncha",
    "namaste ji", "namaskar ji",
}


def _is_greeting(query: str) -> bool:
    """True only when the *entire* message is a greeting/pleasantry.

    Deliberately conservative:
    - the whole normalized message matches a known greeting phrase, OR
    - the message starts with a greeting word and stays short (<=20 chars)

    Anything longer, or anything that pairs a greeting with a real sentence,
    falls through to the normal analysis/retrieval pipeline unchanged.
    """
    if not query or not query.strip():
        return False
    normalized = query.strip().lower().strip(" .!?।,-")
    if normalized in _GREETING_MESSAGES:
        return True
    first_word = normalized.split(" ", 1)[0] if normalized else ""
    return bool(first_word) and first_word in _GREETING_WORDS and len(normalized) <= 20


def _greeting_answer(language: str) -> str:
    """Friendly, non-legal reply for pure greetings. Never cites law."""
    if language == "english":
        return (
            "Hello! How can I help you today? "
            "Describe your legal situation and I'll look up verified "
            "information for you from our legal knowledge base."
        )
    return (
        "नमस्ते! Hello, ma kasari sahayog garna sakchhu? "
        "तपाईंको कानूनी समस्या बताउनुहोस्, म हाम्रो प्रमाणित कानूनी डाटाबेसबाट "
        "जानकारी खोजेर सहयोग गर्ने कोसिस गर्छु।"
    )


# ---------------------------------------------------------------------------
# Follow-up question catalogue
# ---------------------------------------------------------------------------
# Each entry: (field_name, condition_fn, english_q, nepali_q, reason_tag)
#
# condition_fn(ctx) returns True when the field is still unknown — some fields
# are logically covered by others (e.g. district covers incident_location, so
# we skip incident_location once district is known).
# ---------------------------------------------------------------------------
def _field_missing(field: str):
    """Return a predicate that checks a single field."""
    from app.services.case_context import CaseContext  # local import avoids circularity
    def _check(ctx: "CaseContext") -> bool:
        return not ctx.is_known(field)
    return _check


def _location_missing():
    """True only when neither incident_location nor district is known."""
    def _check(ctx: "CaseContext") -> bool:
        return not ctx.is_known("incident_location") and not ctx.is_known("district")
    return _check


def _court_missing():
    """True when neither court nor court_level is known."""
    def _check(ctx: "CaseContext") -> bool:
        return not ctx.is_known("court") and not ctx.is_known("court_level")
    return _check


def _deadline_missing():
    """True when notice was received but no deadline is known."""
    def _check(ctx: "CaseContext") -> bool:
        # Only ask about deadline if we know a notice was received
        if not ctx.is_known("notice_received"):
            return False
        return not ctx.is_known("deadline_days") and not ctx.is_known("deadline")
    return _check


# Priority-ordered catalogue.  The first entries are the most legally important.
_FOLLOW_UP_CATALOGUE: list[tuple] = [
    # (field_key_for_dedup, condition_fn, english_q, nepali_q, reason)
    (
        "matter_type",
        _field_missing("matter_type"),
        "What type of legal matter is this - property, family, criminal, or something else?",
        "यो के प्रकारको मुद्दा हो — सम्पत्ति, पारिवारिक, फौजदारी, वा अन्य?",
        "missing_matter_type",
    ),
    (
        "opposing_party",
        _field_missing("opposing_party"),
        "Who is the other party involved in this case?",
        "यस मुद्दामा अर्को पक्ष को हो?",
        "missing_opposing_party",
    ),
    (
        "incident_description",
        _field_missing("incident_description"),
        "Can you briefly describe what happened?",
        "के भयो भनेर संक्षेपमा बताउनुहोस्।",
        "missing_incident_description",
    ),
    (
        "location",
        _location_missing(),
        "Which district or city is this related to?",
        "यो मुद्दा कुन जिल्ला वा शहरसँग सम्बन्धित छ?",
        "missing_location",
    ),
    (
        "court",
        _court_missing(),
        "Which court or authority is handling this matter?",
        "यो मुद्दा कुन अदालत वा निकायमा दर्ता छ?",
        "missing_court",
    ),
    (
        "notice_received",
        _field_missing("notice_received"),
        "Have you received any official notice or document?",
        "कुनै आधिकारिक सूचना वा कागजात प्राप्त भएको छ?",
        "missing_notice",
    ),
    (
        "deadline",
        _deadline_missing(),
        "How many days do you have to respond to the notice?",
        "सूचनामा जवाफ दिन कति दिनको म्याद तोकिएको छ?",
        "missing_deadline",
    ),
    (
        "notice_date",
        _field_missing("notice_date"),
        "When exactly did you receive the notice?",
        "सूचना ठ्याक्कै कुन मितिमा प्राप्त भयो?",
        "missing_notice_date",
    ),
    (
        "case_number",
        _field_missing("case_number"),
        "Do you have an official case number or file number?",
        "मुद्दा नम्बर वा दर्ता नम्बर छ भने बताउनुहोस्।",
        "missing_case_number",
    ),
    (
        "documents_available",
        _field_missing("documents_available"),
        "What documents do you have that relate to this matter?",
        "यस विषयसँग सम्बन्धित तपाईंसँग कुनै कागजात छन्?",
        "missing_documents",
    ),
    (
        "user_goal",
        _field_missing("user_goal"),
        "What outcome are you hoping to achieve?",
        "तपाईं के हासिल गर्न चाहनुहुन्छ?",
        "missing_goal",
    ),
]

# High-priority fields: when ALL of these are known we have enough to
# stop asking intake questions and focus entirely on legal information.
_HIGH_PRIORITY_FIELDS = frozenset(
    {"matter_type", "opposing_party", "notice_received", "location", "court"}
)


def _build_follow_up_questions(
    *,
    case_context: Optional["CaseContext"],
    language: str,
    has_verified_context: bool,
) -> list[dict[str, str]]:
    """Return the highest-priority questions whose answers are still unknown.

    Guarantees:
    - Never asks about a field already captured in case_context.
    - Returns at most MAX_FOLLOW_UP questions.
    - Returns zero questions when all high-priority fields are known.
    - Never pads with generic questions when specific ones are already known.
    - Returns one generic question only when absolutely no context exists yet.
    """
    from app.services.case_context import CaseContext  # local import

    # No context object at all → first turn, ask a single open question
    if case_context is None:
        return _one_generic(language)

    # Check whether we already have sufficient intake information
    all_high_priority_known = all(
        _high_priority_satisfied(field, case_context)
        for field in _HIGH_PRIORITY_FIELDS
    )
    if all_high_priority_known and has_verified_context:
        # Enough context + legal material found → no intake questions needed
        return []

    questions: list[dict[str, str]] = []
    seen_keys: set[str] = set()

    for field_key, condition_fn, en_q, ne_q, reason in _FOLLOW_UP_CATALOGUE:
        if field_key in seen_keys:
            continue
        if not condition_fn(case_context):
            # This field (or its logical equivalent) is already known — skip.
            continue
        q_text = en_q if language == "english" else ne_q
        questions.append({"question": q_text, "reason": reason})
        seen_keys.add(field_key)
        if len(questions) >= MAX_FOLLOW_UP:
            break

    # If after filtering every specific question the list is empty, return
    # at most one generic question rather than three.
    if not questions:
        return _one_generic(language) if not all_high_priority_known else []

    return questions


def _high_priority_satisfied(field: str, ctx: "CaseContext") -> bool:
    """Return True when the high-priority field (or its logical proxy) is known."""
    if field == "location":
        return ctx.is_known("incident_location") or ctx.is_known("district")
    if field == "court":
        return ctx.is_known("court") or ctx.is_known("court_level")
    return ctx.is_known(field)


def _one_generic(language: str) -> list[dict[str, str]]:
    """Single neutral opening question when we know nothing yet."""
    if language == "english":
        return [{"question": "Can you describe your legal situation briefly?",
                 "reason": "initial_intake"}]
    return [{"question": "तपाईंको कानूनी समस्या संक्षेपमा बताउनुहोस्।",
             "reason": "initial_intake"}]


class ConversationService:
    """Service managing conversation state and grounded legal retrieval."""

    def __init__(self, provider: Optional[LLMProvider] = None) -> None:
        """Create the service.

        Args:
            provider: Optional LLM provider override (tests, or a caller that
                manages its own provider). When ``None`` the configured
                provider is used, and ``None`` from the configuration means
                generation is disabled but the endpoint still works.
        """
        self.repository = ConversationRepository
        self._provider = provider
        # Use the module-level singleton so case context persists across all
        # requests within the same worker process, backed by the database.
        self._case_context_manager = get_case_context_manager()

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def start_conversation(self, session_id: str, language: str = "nepali") -> dict[str, Any]:
        """Start a new conversation session.

        Args:
            session_id: Unique session identifier.
            language: User's preferred language ("nepali", "english", or None).

        Returns:
            Created session dict.
        """
        with get_connection() as conn:
            repo = self.repository(conn)
            session = repo.create_session(
                session_id=session_id,
                status="active",
                language=language,
            )
            return session

    def end_conversation(self, session_id: str) -> None:
        """End a conversation session."""
        with get_connection() as conn:
            repo = self.repository(conn)
            repo.update_session_status(session_id, "ended")

    def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a conversation session by session_id."""
        with get_connection() as conn:
            repo = self.repository(conn)
            return repo.get_session(session_id)

    # ------------------------------------------------------------------
    # Message persistence
    # ------------------------------------------------------------------

    def add_user_message(self, session_id: str, content: str, input_mode: str = "text") -> dict[str, Any]:
        """Add a user message to the conversation."""
        with get_connection() as conn:
            repo = self.repository(conn)
            return repo.add_message(
                session_id=session_id,
                role="user",
                input_mode=input_mode,
                content=content,
            )

    def add_assistant_message(self, session_id: str, content: str, input_mode: str = "text") -> dict[str, Any]:
        """Add an assistant message to the conversation."""
        with get_connection() as conn:
            repo = self.repository(conn)
            return repo.add_message(
                session_id=session_id,
                role="assistant",
                input_mode=input_mode,
                content=content,
            )

    def list_messages(self, session_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        """List conversation messages (most recent first)."""
        with get_connection() as conn:
            repo = self.repository(conn)
            return repo.list_session_messages(session_id=session_id, limit=limit)

    # ------------------------------------------------------------------
    # Multi-turn context assembly
    # ------------------------------------------------------------------

    def get_conversation_context(
        self,
        session_id: str,
        max_messages: int = 10,
        conn: Any = None,
    ) -> list[dict[str, Any]]:
        """Get recent conversation context for multi-turn questions.

        Returns list of dicts with 'role' and 'content' keys,
        ordered from oldest to newest.

        The window defaults to the last 10 messages but can be
        configured. This prevents context from growing unbounded
        while preserving relevant conversational history.

        ``conn`` lets a caller inside an open transaction reuse its own
        connection: rows written there are invisible to a fresh connection.
        """
        if conn is not None:
            return self.repository(conn).get_recent_context(
                session_id=session_id, max_messages=max_messages
            )
        with get_connection() as own_conn:
            repo = self.repository(own_conn)
            return repo.get_recent_context(session_id=session_id, max_messages=max_messages)

    # ------------------------------------------------------------------
    # Question analysis and case context extraction
    # ------------------------------------------------------------------

    def analyze_question(
        self, query: str, context: list[dict[str, Any]] | None = None, conn: Any = None
    ) -> dict[str, Any]:
        """Analyze a user question to extract intent, domain, entities, and case context.

        Combines keyword-based analysis with case context extraction to understand
        the user's legal situation. Updates internal case context for the session.

        Args:
            query: The user's question text.
            context: Recent conversation history (unused for analysis, kept for API compat).
            conn: Optional database connection. When provided, used internally instead
                of calling ``get_connection()``, ensuring the same connection is used
                throughout the conversation pipeline.

        Returns a dict with:
        - intent: one of the recognized intent categories
        - domain: legal domain key if identifiable, else None
        - entities: list of extracted entity strings
        - query: the normalized query
        - requires_clarification: whether the question needs more info
        - case_context_updates: dictionary of case context fields that were extracted
        """
        if not query or not query.strip():
            return {
                "intent": "unknown",
                "domain": None,
                "entities": [],
                "query": "",
                "requires_clarification": True,
                "case_context_updates": {},
            }

        normalized = query.strip().lower()

        # Simple intent classification via keyword matching
        intent = self._classify_intent(normalized)

        # Extract domain from intent or query
        domain = self._extract_domain(normalized, intent, conn=conn)

        # Extract simple entities (capitalized phrases, legal terms)
        entities = self._extract_entities(normalized, context)

        # Extract case context information from the query
        case_context_updates = self._extract_case_context(normalized, context or [], conn=conn)

        # Determine if clarification is needed
        requires_clarification = self._check_clarification_needed(
            normalized, intent, entities
        ) or len(case_context_updates) == 0  # Need clarification if no context extracted

        return {
            "intent": intent,
            "domain": domain,
            "entities": entities,
            "query": query,
            "requires_clarification": requires_clarification,
            "case_context_updates": case_context_updates,
        }

    def _classify_intent(self, normalized: str) -> str:
        """Classify the user's intent via keyword matching.

        Possible intents:
        - legal_information
        - procedure
        - document_requirement
        - rights
        - obligation
        - dispute
        - complaint
        - criminal_issue
        - family_issue
        - property_issue
        - unknown
        """
        # Nepali keywords
        nepali_keywords = {
            "धारा": "legal_information",
            "अनुच्छेद": "legal_information",
            "अधिकार": "rights",
            "दावा": "complaint",
            "सम्पत्ति": "property_issue",
            "जग्गा": "property_issue",
            "लडाई": "dispute",
            "शिकायत": "complaint",
            "दंड": "criminal_issue",
            " प्रक्रिया": "procedure",
            "समय": "document_requirement",
            "मुद्दा": "dispute",
        }

        # English / Romanized keywords
        english_keywords = {
            "section": "legal_information",
            "article": "legal_information",
            "right": "rights",
            "law": "legal_information",
            "complaint": "complaint",
            "property": "property_issue",
            "dispute": "dispute",
            "lawsuit": "dispute",
            "criminal": "criminal_issue",
            "procedure": "procedure",
            "requirement": "document_requirement",
            "obligation": "obligation",
            "mudda": "dispute",
        }

        # Check Nepali keywords first, then English
        for ne_key, ne_intent in nepali_keywords.items():
            if ne_key in normalized:
                return ne_intent

        for en_key, en_intent in english_keywords.items():
            if en_key in normalized:
                return en_intent

        # Check mixed/contextual patterns
        if any(word in normalized for word in ["विवाद", "dispute", "लडाई"]):
            return "dispute"
        if any(word in normalized for word in ["अधिकार", "rights", "right"]):
            return "rights"
        if any(word in normalized for word in ["शिकायत", "complaint"]):
            return "complaint"

        return "unknown"

    def _extract_domain(self, normalized: str, intent: str, conn: Any = None) -> Optional[str]:
        """Extract a legal domain key from the normalized query and intent.

        Returns a domain key (e.g. 'family', 'property', 'consumer') or None.
        """
        # Map intents to likely domains
        intent_domain_map = {
            "family": "family",
            "property_issue": "property",
            "dispute": "property",
            "criminal_issue": "criminal",
            "complaint": "consumer",
            "rights": "consumer",
            "unknown": None,
        }

        domain = intent_domain_map.get(intent)
        if domain:
            # Verify the domain exists in the database when a connection is available
            if conn is not None:
                from app.repositories.legal_domains import LegalDomainRepository

                dom_repo = LegalDomainRepository(conn)
                if dom_repo.get_by_key(domain) is not None:
                    return domain
            # When no connection is available, use the intent-mapped domain directly
            # (keyword-pattern fallback handles domain extraction from queries)

        # Try to extract domain from the query itself using keyword patterns
        domain_patterns = {
            "family": ["विवाह", "ब्याह", "पत्नी", "पति", "बच्चा", "child"],
            "property": ["सम्पत्ति", "जग्गा", "भूमि", "land", "घर", "house"],
            "consumer": ["माल", "खरीद", "खर्च", "पैसा", "money", "व्यवसाय", "business"],
        }

        for d_key, patterns in domain_patterns.items():
            if any(p in normalized for p in patterns):
                return d_key

        return None

    def _extract_entities(
        self, normalized: str, context: list[dict[str, Any]] | None = None
    ) -> list[str]:
        """Extract simple entities from the query and conversation context.

        Entities are legal terms, parties, or objects that may be relevant
        for retrieval. This is a simple keyword-based extractor.
        """
        entities: list[str] = []

        # Common legal entity patterns
        entity_patterns = [
            # Nepali
            "पैतृक", " ancestral",
            "स्वामित्व", " ownership",
            "नामसारी", " title deed",
            "अंशबाँडा", " partition",
            # English
            "ancestral",
            "ownership",
            "title",
            "partition",
            "property",
        ]

        # Add entities from conversation context if available
        if context:
            for msg in context:
                if msg.get("content"):
                    # Extract potentially relevant nouns/phrases
                    words = msg["content"].split()
                    for w in words:
                        w_clean = w.strip(".,;:!?")
                        if w_clean and len(w_clean) > 1:
                            # Check if not a stop word
                            stop_words = {"को", "का", "के", "in", "the", "a", "an", "कि", "that"}
                            if w_clean.lower() not in stop_words:
                                entities.append(w_clean)

        # Add entities from the current query
        words = normalized.split()
        for w in words:
            w_clean = w.strip(".,;:!?")
            if w_clean and len(w_clean) > 1:
                stop_words = {"को", "का", "के", "in", "the", "a", "an", "कि", "that"}
                if w_clean.lower() not in stop_words and w_clean not in entities:
                    entities.append(w_clean)

        return entities[:8]  # Cap at 8 entities

    def _extract_case_context(
        self, normalized: str, context: list[dict[str, Any]], conn: Any = None
    ) -> dict[str, Any]:
        """Extract case context information from the query.

        Returns a dictionary of case context fields that were identified
        in the input, with their extracted values.
        """
        updates: dict[str, Any] = {}

        # Extract user role information
        role_patterns = {
            "user_role": [
                ("म", "I"),
                ("मै", "I"),
                ("मेरो", "my"),
                (" मेरो ", " my "),
                ("मलाई", "to me"),
                ("मलाई ", " to me "),
            ]
        }

        # Extract opposing party information. Kept for explicit English
        # phrasing ("my brother") - the primary Romanized/Devanagari
        # detection now happens via _relation_tokens below.
        opposing_patterns = [
            ("मेरो भाई", "brother"),
            ("मेरा भाई", "brother"),
            ("भाइले", "brother"),
            ("भाईने", "brother"),
            ("mero bhai", "brother"),
            ("mero bhaijaan", "brother"),
            ("my brother", "brother"),
            ("my sis", "sister"),
            ("my father", "father"),
            ("my mother", "mother"),
            ("पिता", "father"),
            ("मातृ", "mother"),
            ("सासु", "mother-in-law"),
            ("ससुर", "father-in-law"),
        ]

        # Extract matter type information
        matter_patterns = {
            "matter_type": [
                ("सम्पत्ति", "property"),
                ("जग्गा", "land"),
                ("घर", "house"),
                ("किराया", "rent"),
                ("स्वामित्व", "ownership"),
                ("विवाह", "marriage"),
                ("टalak", "divorce"),
                ("ब्याह", "marriage"),
                ("बाल", "child"),
                ("बालक", "boy"),
                ("बालिका", "girl"),
                ("आत्महत्या", "suicide"),
                ("हत्या", "murder"),
                ("चोरी", "theft"),
                ("लूट", "robbery"),
                ("जालसाजी", "fraud"),
                ("धोखा", "deception"),
                ("दुर्व्यवहार", "abuse"),
                ("हिंसा", "violence"),
                ("डर", "threat"),
                ("धमकी", "threat"),
                ("अपघात", "accident"),
                ("घातक", "fatal"),
                ("छोटो", "minor"),
                ("गंभीर", "serious"),
                ("मुद्दा", "dispute"),
                ("mudda", "dispute"),
            ]
        }

        # Extract location information
        location_indicators = [
            "काठमाण्डौ", "काठमांडौ", "काठमाडौं", "kathmandu",
            "पोखरा", "pokhara",
            "ललितपुर", "lalitpur",
            "भक्तपुर", "bhaktapur",
            "बीरगंज", "birgunj",
            "विराटनगर", "biratnagar",
            "धारान", "dharan",
            "इटहरी", "itahari",
            "जनकपुर", "janakpur",
            "नेपालगंज", "nepalgunj",
            "महेंद्रनगर", "mahendranagar",
            "दिपायल", "dipayal",
            "अमरगढी", "amarghadi",
        ]

        # Check for location
        location_map = {
            "काठमाण्डौ": "Kathmandu",
            "काठमांडौ": "Kathmandu",
            "काठमाडौं": "Kathmandu",  # Chandrabindu variant
            "kathmandu": "Kathmandu",
            "पोखरा": "Pokhara",
            "pokhara": "Pokhara",
            "ललितपुर": "Lalitpur",
            "lalitpur": "Lalitpur",
            "भक्तपुर": "Bhaktapur",
            "bhaktapur": "Bhaktapur",
            "वीरगंज": "Birgunj",
            "birgunj": "Birgunj",
            "विराटनगर": "Biratnagar",
            "biratnagar": "Biratnagar",
            "धारान": "Dharan",
            "dharan": "Dharan",
            "इटहरी": "Itahari",
            "itahari": "Itahari",
            "जनकपुर": "Janakpur",
            "janakpur": "Janakpur",
            "नेपालगंज": "Nepalgunj",
            "nepalgunj": "Nepalgunj",
            "महेंद्रनगर": "Mahendranagar",
            "mahendranagar": "Mahendranagar",
            "दिपायल": "Dipayal",
            "dipayal": "Dipayal",
            "अमरगढी": "Amarghadi",
            "amarghadi": "Amarghadi",
        }
        for location, english_name in location_map.items():
            if location in normalized:
                updates["incident_location"] = english_name
                # Infer district/province from city name
                if location.lower() in ["काठमाण्डौ", "काठमांडौ", "काठमाडौं", "kathmandu"]:
                    updates["district"] = "Kathmandu"
                    updates["province"] = "Bagmati"
                elif location.lower() in ["पोखरा", "pokhara"]:
                    updates["district"] = "Kaski"
                    updates["province"] = "Gandaki"
                break

        # Extract court/authority information
        authority_patterns = [
            ("अदालत", "court"),
            ("दलाल", "court"),
            ("जिल्ला अदालत", "district court"),
            ("जिल्ला अदालत", "district court"),
            ("उच्च अदालत", "high court"),
            ("सुप्रीम कोर्ट", "supreme court"),
            ("अधिकारी", "authority"),
            ("प्रधान्य", "authority"),
            ("सशस्त्र प्रहरी", "armed police"),
            ("प्रहरी", "police"),
            ("वन विभाग", "forest department"),
            ("भूमि कार्यालय", "land office"),
            ("कर कार्यालय", "tax office"),
        ]

        # Extract notice information
        notice_patterns = [
            ("सूचना", "notice"),
            ("सूचना प्राप्त", "notice received"),
            ("सूचना आयो", "notice received"),
            ("सूचना आएको", "notice received"),
            ("दर्ता", "registration"),
            ("दर्ता प्राप्त", "registration received"),
        ]

        # Extract deadline information
        deadline_patterns = [
            ("दिनभित्र", "days within"),
            ("दिनमा", "days in"),
            ("हफ्ताबाट", "weeks from"),
            ("महिनाबाट", "months from"),
            ("आजबाट", "from today"),
            ("कलदेखि", "from tomorrow"),
            ("दिन", "day"),
            ("हफ्ता", "week"),
            ("महिना", "month"),
        ]

        # Check for user role
        for nepali_pattern, english_pattern in role_patterns["user_role"]:
            if nepali_pattern in normalized or english_pattern.lower() in normalized:
                if "म" in normalized or "mai" in normalized.lower():
                    updates["user_role"] = "self"
                elif "मेरो" in normalized or "mero" in normalized.lower():
                    updates["user_role"] = "possessor"
                break

        # --- FIX: opposing-party extraction --------------------------------
        # Relation words are now matched at the token level, not as fixed
        # two-word phrases. Nepali possessives inflect ("mero bhai",
        # "mera bhai", "merai bhai", "hamro bhai", ...); matching only the
        # single literal phrase "mero bhai" silently dropped opposing_party
        # (and the partition/inheritance retrieval-query enrichment in
        # _build_retrieval_query that depends on it) for any other equally
        # common possessive form - e.g. "malai merai bhai le mudda halyo"
        # was never recognized as a brother/sibling dispute, so the
        # retrieval query never picked up the Devanagari enrichment terms
        # needed to match the (Devanagari-indexed) verified knowledge base.
        _relation_tokens = [
            (("भाइ", "भाई", "bhai", "bhaijaan"), "brother"),
            (("बहिनी", "बहिन", "bahini"), "sister"),
            (("बुबा", "बाबा", "buwa", "baba", "पिता"), "father"),
            (("आमा", "aama", "मातृ"), "mother"),
            (("सासु", "sasu"), "mother-in-law"),
            (("ससुर", "sasural"), "father-in-law"),
        ]
        tokens = normalized.replace(",", " ").split()
        for variants, relation in _relation_tokens:
            if any(v in tok or tok in v for tok in tokens for v in variants):
                updates["opposing_party"] = relation
                break
        # Fall back to the original phrase list (covers explicit English
        # phrasing such as "my brother") for anything not already matched.
        if "opposing_party" not in updates:
            for nepali_term, english_term in opposing_patterns:
                if nepali_term in normalized or english_term.lower() in normalized:
                    updates["opposing_party"] = english_term
                    break
        # ---------------------------------------------------------------

        # Check for matter type
        for nepali_term, english_term in matter_patterns["matter_type"]:
            if nepali_term in normalized or english_term.lower() in normalized:
                updates["matter_type"] = english_term
                break

        # Check for court/authority
        for nepali_term, english_term in authority_patterns:
            if nepali_term in normalized or english_term.lower() in normalized:
                if "अदालत" in nepali_term or "court" in english_term.lower():
                    updates["court"] = english_term
                    # Check input text for court level indicators
                    if "जिल्ला" in normalized or "district" in normalized.lower():
                        updates["court_level"] = "district"
                    elif "उच्च" in normalized or "high" in normalized.lower():
                        updates["court_level"] = "high"
                    elif "सुप्रीम" in normalized or "supreme" in normalized.lower():
                        updates["court_level"] = "supreme"
                else:
                    updates["authority"] = english_term
                break

        # Check for notice
        for nepali_term, english_term in notice_patterns:
            if nepali_term in normalized or english_term.lower() in normalized:
                updates["notice_received"] = True
                break

        # Check for deadline/day information
        for nepali_term, english_term in deadline_patterns:
            if nepali_term in normalized or english_term.lower() in normalized:
                # Try to extract number of days
                import re
                # Translate Devanagari digits to ASCII before matching
                devanagari_to_ascii = str.maketrans("०१२३४५६७८९", "0123456789")
                normalized_digits = normalized.translate(devanagari_to_ascii)
                # Look for patterns like "15 दिन" or "15 days" or "१५ दिनभित्र"
                day_patterns = [r'(\d+)\s*दिन', r'(\d+)\s*days?', r'दिन\s*(\d+)']
                for pattern in day_patterns:
                    match = re.search(pattern, normalized_digits)
                    if match:
                        try:
                            days = int(match.group(1))
                            updates["deadline_days"] = days
                            updates["deadline"] = f"{days} days"
                        except ValueError:
                            pass
                break

        # Check for urgency indicators
        urgency_indicators = [
            "तात्कालिक", "urgent", "जल्द", "quick", "शीघ्र", "immediate",
            "एमर्जेन्सी", "emergency", "गम्भीर", "serious", "गंभीर"
        ]
        for indicator in urgency_indicators:
            if indicator in normalized:
                updates["urgency"] = "high"
                break

        # Extract incident description from action verbs
        action_verbs = [
            ("gareko", "did"), ("gareko", "did"), ("garekchu", "doing"),
            ("haryo", "happened"), ("halyo", "filed"), ("bhayeko", "was"),
            ("hunu", "to happen"),
            ("garnu", "to do"), ("garcha", "does"), ("garchu", "doing"),
            ("hunchha", "happens"), ("huncha", "happens")
        ]
        for nepali_verb, english_verb in action_verbs:
            if nepali_verb in normalized or english_verb in normalized:
                # Try to extract a simple description around the verb
                words = normalized.split()
                for i, word in enumerate(words):
                    if nepali_verb in word or english_verb in word:
                        # Get context around the verb
                        start = max(0, i - 3)
                        end = min(len(words), i + 4)
                        phrase = " ".join(words[start:end])
                        if len(phrase) > 10:  # Only use if it's substantial
                            updates["incident_description"] = phrase
                        break
                break

        return updates

    def _check_clarification_needed(
        self, normalized: str, intent: str, entities: list[str]
    ) -> bool:
        """Determine if the question requires clarification.

        Returns True when the query lacks sufficient information
        for reliable retrieval.
        """
        # Unknown intent without clear keywords
        if intent == "unknown" and not entities:
            return True

        # Very short queries without legal terminology
        if len(normalized) < 5:
            return True

        # Questions that are purely general without legal grounding
        general_starters = ["कस्तो", "कसरी", "कहाँ", "कुन", "what", "how", "where"]
        if any(normalized.startswith(s) for s in general_starters):
            # Still may be ok if there are legal entities
            if not any(e for e in entities if len(e) > 3):
                return True

        return False

    # ------------------------------------------------------------------
    # Legal retrieval integration
    # ------------------------------------------------------------------

    def retrieve_for_context(
        self,
        query: str,
        top_k: int = 5,
        minimum_score: float = 0.3,
        domain_filter: Optional[str] = None,
        verified_only: bool = True,
        conn: Any = None,
    ) -> dict[str, Any]:
        """Retrieve legal provisions relevant to the user's question.

        Uses Member 2's retrieve_legal_context service.

        Args:
            conn: Optional connection to reuse for the domain lookup. Pass the
                caller's connection when this runs inside an open transaction,
                otherwise a connection from the pool is used.

        Returns the structured retrieval response with source metadata.
        """
        if conn is not None:
            return self._retrieve(query, top_k, minimum_score, domain_filter,
                                  verified_only, conn)
        with get_connection() as own_conn:
            return self._retrieve(query, top_k, minimum_score, domain_filter,
                                  verified_only, own_conn)

    def _retrieve(
        self,
        query: str,
        top_k: int,
        minimum_score: float,
        domain_filter: Optional[str],
        verified_only: bool,
        conn: Any,
    ) -> dict[str, Any]:
        """Resolve the domain filter and delegate to the retrieval service."""
        domain_id = None
        if domain_filter:
            from app.repositories.legal_domains import LegalDomainRepository

            if LegalDomainRepository(conn).get_by_key(domain_filter) is not None:
                domain_id = domain_filter

        return retrieve_legal_context(
            query=query,
            top_k=top_k,
            minimum_score=minimum_score,
            domain_id=domain_id,
            verified_only=verified_only,
        )

    def _build_retrieval_query(
        self, query: str, case_context: Optional["CaseContext"]
    ) -> str:
        """Enrich the raw user query with accumulated case context.

        Appends key facts already known from prior turns so the retrieval
        engine has more signal. Appended terms only come from explicitly
        stored case context — never from inference or invention.

        Example:
            query = "notice आएको छ"
            case_context.matter_type = "property"
            case_context.court_level = "district"
            → "notice आएको छ property district court"
        """
        if not case_context:
            return query

        # Legal terms worth appending for better ILIKE matching
        enrichments: list[str] = []

        # Map matter types to useful Nepali/English retrieval terms
        matter_terms: dict[str, list[str]] = {
            "property":  ["सम्पत्ति", "जग्गा", "property"],
            "land":      ["जग्गा", "भूमि", "land"],
            "house":     ["घर", "house", "building"],
            "rent":      ["किराया", "rent", "tenancy"],
            "ownership": ["स्वामित्व", "ownership"],
            "marriage":  ["विवाह", "marriage"],
            "divorce":   ["सम्बन्ध विच्छेद", "divorce"],
            "child":     ["बालबालिका", "child"],
            "murder":    ["हत्या", "murder"],
            "theft":     ["चोरी", "theft"],
            "robbery":   ["लूट", "robbery"],
            "fraud":     ["जालसाजी", "fraud"],
            "violence":  ["हिंसा", "violence"],
            "brother":   ["भाइ", "brother", "सहोदर"],
            "dispute":   ["मुद्दा", "विवाद", "dispute"],
        }
        if case_context.matter_type:
            mt = case_context.matter_type.lower()
            enrichments.extend(matter_terms.get(mt, [mt]))

        # Court level terms
        court_terms: dict[str, list[str]] = {
            "district": ["जिल्ला अदालत", "district court"],
            "high":     ["उच्च अदालत", "high court"],
            "supreme":  ["सर्वोच्च अदालत", "supreme court"],
        }
        if case_context.court_level:
            enrichments.extend(court_terms.get(case_context.court_level.lower(), []))
        elif case_context.court:
            enrichments.append(case_context.court)

        # Notice/deadline terms
        if case_context.notice_received:
            enrichments.extend(["सूचना", "notice", "जवाफ"])
        if case_context.deadline_days:
            enrichments.append(f"{case_context.deadline_days} दिन")

        # Opposing party context
        if case_context.opposing_party in ("brother", "sister", "son", "daughter"):
            enrichments.extend(["अंशबाँडा", "उत्तराधिकार", "partition", "inheritance"])

        if not enrichments:
            return query

        # Deduplicate, filter out terms already in query, cap additions
        query_lower = query.lower()
        new_terms = []
        seen: set[str] = set()
        for term in enrichments:
            if term not in seen and term.lower() not in query_lower:
                seen.add(term)
                new_terms.append(term)
                if len(new_terms) >= 6:
                    break

        return f"{query} {' '.join(new_terms)}".strip() if new_terms else query

    # ------------------------------------------------------------------
    # Grounded response generation
    # ------------------------------------------------------------------

    def generate_grounded_response(
        self,
        query: str,
        session_id: str | None = None,
        top_k: int = 5,
        minimum_score: float = 0.3,
        conn: Any = None,
    ) -> dict[str, Any]:
        """Generate a grounded legal response to a user's question.

        The full pipeline:

        0. Short-circuit pure greetings/small talk with a friendly, non-legal
           reply - never touches case context or retrieval, never produces
           the legal "no verified provision" fallback text.
        1. Analyze the question (intent, domain, entities, clarification need)
        2. Extract and update case context from query and history
        3. Identify missing critical information and generate follow-up questions if needed
        4. Retrieve relevant legal provisions (verified_only)
        5. Assemble grounded context from retrieved provisions
        6. Format structured response with citations

        This embodies the RETRIEVE → GROUND → GENERATE principle with intelligent
        legal intake and case context management. Every real legal question still
        goes through steps 1-6 unchanged: nothing here bypasses grounding or
        invents an answer that isn't backed by a verified, retrieved provision.

        Args:
            conn: Optional connection shared with the caller's transaction. When
                omitted, the service opens its own connections from the pool.
                Callers that already hold an open transaction (the API route)
                must pass theirs, otherwise writes made in that uncommitted
                transaction are invisible here.
        """
        # Step 0: Small talk / greetings never enter the legal retrieval
        # pipeline (see _is_greeting for exactly what qualifies). This is a
        # UX fix, not a grounding shortcut: it only fires for messages with
        # zero legal content, and it never fabricates or cites law.
        if _is_greeting(query):
            language = detect_language(query)
            greeting_analysis: dict[str, Any] = {
                "intent": "greeting",
                "domain": None,
                "entities": [],
                "query": query,
                "requires_clarification": False,
                "case_context_updates": {},
            }
            response = self._response(
                answer=_greeting_answer(language),
                language=language,
                analysis=greeting_analysis,
                status=STATUS_GREETING,
                citations=[],
                confidence="low",
                retrieval=None,
                grounded=False,
                generation="canned",
                needs_clarification=False,
                session_id=session_id,
                conn=conn,
            )
            self._persist_assistant_turn(session_id, response, conn=conn)
            return response

        # Step 1: Analyze the question
        analysis = self.analyze_question(query, None, conn=conn)
        language = detect_language(query)

        # Step 2: Update case context with information from the query
        case_context_updates = analysis.get("case_context_updates", {})
        if session_id and case_context_updates:
            self._case_context_manager.update_context(session_id, conn=conn, **case_context_updates)

        # Get current case context for reference
        case_context = self._case_context_manager.get_context(session_id, conn=conn) if session_id else None

        # Step 3: Check if we need to ask for missing critical information
        # If we have a session and we're missing critical info, we might ask follow-ups
        # instead of proceeding to retrieval immediately
        needs_clarification_from_context = False
        if session_id and case_context:
            missing_fields = case_context.get_missing_fields()
            # Define critical fields that are essential for legal research
            critical_fields = ["user_role", "matter_type", "opposing_party", "incident_description"]
            missing_critical = [f for f in missing_fields if f in critical_fields]
            # If we're missing critical information and haven't gotten any useful info yet,
            # we should ask for clarification rather than searching
            if missing_critical and not case_context.is_known("matter_type"):
                needs_clarification_from_context = True

        # Step 4: Retrieve legal context. ``verified_only=True`` is the safe
        # default and is never relaxed to make an answer possible.
        # However, if we need clarification, we might skip retrieval or use a broader search
        try:
            # Determine domain filter - use extracted domain or infer from case context
            domain_filter = analysis.get("domain")
            if not domain_filter and case_context and case_context.matter_type:
                # Map matter type to domain if possible
                matter_to_domain = {
                    "property": "property",
                    "land": "property",
                    "house": "property",
                    "rent": "property",
                    "ownership": "property",
                    "marriage": "family",
                    "divorce": "family",
                    "child": "family",
                    "murder": "criminal",
                    "theft": "criminal",
                    "robbery": "criminal",
                    "fraud": "cyber",
                    "deception": "cyber",
                    "abuse": "safety",
                    "violence": "safety",
                    "threat": "safety",
                    "accident": "safety",
                }
                domain_filter = matter_to_domain.get(case_context.matter_type.lower() if case_context.matter_type else "")

            retrieval = self.retrieve_for_context(
                query=self._build_retrieval_query(query, case_context),
                top_k=top_k,
                minimum_score=minimum_score,
                domain_filter=domain_filter,
                verified_only=True,
                conn=conn,
            )
        except ApiError as exc:
            # Retrieval failure (e.g. database unavailable): never fabricate.
            logger.warning("Legal retrieval failed: %s", exc)
            response = self._retrieval_error_response(language, analysis, session_id=session_id, conn=conn)
            self._persist_assistant_turn(session_id, response, conn=conn)
            return response

        # Step 5: Handle case where we need clarification but got some results
        if needs_clarification_from_context and retrieval.get("total_found", 0) > 0:
            # We found some legal provisions but still need critical context
            # We'll proceed with the answer but emphasize the need for more information
            pass  # Continue with normal flow

        # Step 6: No verified context -> honest fallback, no guessing.
        if retrieval.get("total_found", 0) == 0:
            response = self._no_verified_context_response(
                language=language, analysis=analysis, retrieval=retrieval,
                session_id=session_id, conn=conn,
            )
            self._persist_assistant_turn(session_id, response, conn=conn)
            return response

        results = retrieval["results"]

        # Step 7: Citations are built from the database rows, never from model
        # output, so an answer can only ever cite real records. They are also
        # deduplicated on stable provision/chunk identity so a single provision
        # is never presented as several duplicate citation records.
        citations = build_citations(results)

        # Step 8: Generate strictly from the retrieved, verified context.
        provider = self._provider or get_llm_provider()
        if provider is None:
            response = self._generation_unavailable_response(
                language=language,
                analysis=analysis,
                retrieval=retrieval,
                citations=citations,
                reason="not_configured",
                provider=None,
                session_id=session_id,
                conn=conn,
            )
            self._persist_assistant_turn(session_id, response, conn=conn)
            return response

        system_prompt = build_system_prompt(
            language=language,
            context_block=build_context_block(results),
            verified_count=sum(1 for r in results if r.get("is_verified")),
            total_count=context_entry_count(results),
        )
        messages = [
            *self._history_messages(session_id, query, conn=conn),
            {"role": "user", "content": build_user_message(query)},
        ]

        try:
            completion = provider.generate(
                system_prompt=system_prompt, messages=messages
            )
        except LLMError as exc:
            logger.warning("LLM generation failed (%s): %s", exc.kind, exc)
            response = self._generation_unavailable_response(
                language=language,
                analysis=analysis,
                retrieval=retrieval,
                citations=citations,
                reason=exc.kind,
                provider=provider.info(),
                session_id=session_id,
                conn=conn,
            )
            self._persist_assistant_turn(session_id, response, conn=conn)
            return response

        # Phase 10: the answer text may only reference retrieved sections.
        # URLs are stripped first (answers are prose; only the structured,
        # database-backed citations carry links), then the answer is rejected
        # entirely if it cites a section that was not in the verified evidence.
        answer_text = strip_urls_from_answer(completion.text)
        unsupported_refs = self._unsupported_citation_references(
            answer_text, retrieval
        )
        if unsupported_refs:
            logger.warning(
                "Rejecting answer with unsupported citation references: %s",
                sorted(unsupported_refs),
            )
            response = self._citation_validation_failed_response(
                language=language,
                analysis=analysis,
                retrieval=retrieval,
                citations=citations,
                provider={"provider": completion.provider, "model": completion.model},
                session_id=session_id,
                conn=conn,
            )
            self._persist_assistant_turn(session_id, response, conn=conn)
            return response

        # Step 9: Structured response with a grounded answer + real citations.
        response = self._answered_response(
            answer=answer_text,
            language=language,
            analysis=analysis,
            retrieval=retrieval,
            citations=citations,
            provider={"provider": completion.provider, "model": completion.model},
            session_id=session_id,
            conn=conn,
        )

        # Step 10: Persist the assistant turn
        self._persist_assistant_turn(session_id, response, conn=conn)

        return response

    def _persist_assistant_turn(
        self,
        session_id: str | None,
        response: dict[str, Any],
        conn: Any = None,
    ) -> None:
        """Persist the assistant's turn so the stored history stays complete.

        The caller (API route) persists the user's own message before invoking
        this service, so it is not written here - only the reply. Called for
        both the grounded and the no-retrieval paths, otherwise a fallback reply
        would leave an unanswered user turn in the history.

        When ``conn`` is given the write joins the caller's transaction; the
        session row created there is not visible to a fresh connection.
        """
        if not session_id:
            return

        def _write(active_conn: Any) -> None:
            self.repository(active_conn).add_message(
                session_id=session_id,
                role="assistant",
                input_mode="text",
                # Persist the answer text (not the whole response dict) so the
                # stored history stays usable as LLM conversation history.
                content=str(response.get("answer") or response),
            )

        if conn is not None:
            _write(conn)
            return
        with get_connection() as own_conn:
            _write(own_conn)

    # ------------------------------------------------------------------
    # Conversation history (multi-turn memory)
    # ------------------------------------------------------------------

    def _history_messages(
        self,
        session_id: str | None,
        query: str,
        conn: Any = None,
        max_messages: int = MAX_HISTORY_MESSAGES,
    ) -> list[dict[str, str]]:
        """Recent turns rendered as provider-neutral chat messages.

        The API route persists the current user message *before* calling this
        service, so the last stored user turn is the question being answered
        right now; it is dropped here and re-added as the final message, which
        keeps the history free of duplicates.
        """
        if not session_id:
            return []
        try:
            history = self.get_conversation_context(
                session_id, max_messages=max_messages, conn=conn
            )
        except Exception:  # pragma: no cover - history is best-effort
            logger.exception(
                "Could not load conversation history; continuing without it"
            )
            return []

        if history:
            last = history[-1]
            if last.get("role") == "user" and (
                (last.get("content") or "").strip() == (query or "").strip()
            ):
                history = history[:-1]

        return [
            {"role": m["role"], "content": m.get("content") or ""}
            for m in history
            if m.get("role") in {"user", "assistant"}
            and (m.get("content") or "").strip()
        ]

    # ------------------------------------------------------------------
    # Response construction
    # ------------------------------------------------------------------

    def _confidence_from(self, results: list[dict[str, Any]]) -> str:
        """Coarse confidence label derived from the retrieval scores."""
        if not results:
            return "low"
        average = sum(r.get("score", 0.0) for r in results) / len(results)
        if average >= 0.7:
            return "high"
        if average >= 0.4:
            return "medium"
        return "low"

    def _unsupported_citation_references(
        self, answer: str, retrieval: dict[str, Any]
    ) -> list[str]:
        """Sections the answer cites that were NOT in the retrieval results.

        The generated answer may only reference sections that come from the
        retrieved, verified evidence. Any other explicit reference means the
        model strayed outside the evidence, so the answer must not be presented
        as a grounded response.
        """
        if not answer or not retrieval or not retrieval.get("results"):
            return []
        allowed = {
            normalize_section_number(r.get("section_number"))
            for r in retrieval["results"]
            if r.get("section_number")
        }
        unsupported: list[str] = []
        for ref in extract_cited_sections(answer):
            normalized = normalize_section_number(ref)
            if normalized and normalized not in allowed and normalized not in unsupported:
                unsupported.append(normalized)
        return unsupported

    def _citation_validation_failed_response(
        self,
        *,
        language: str,
        analysis: dict[str, Any],
        retrieval: dict[str, Any],
        citations: list[dict[str, Any]],
        provider: dict[str, str] | None,
        session_id: str | None = None,
        conn: Any = None,
    ) -> dict[str, Any]:
        """Safe "answered but rejected" outcome.

        Keeps the real, database-backed citations while refusing to ship an
        answer that cannot be traced to the verified evidence.
        """
        return self._response(
            answer=citation_validation_failed_answer(language),
            language=language,
            analysis=analysis,
            status=STATUS_LLM_UNAVAILABLE,
            citations=citations,
            confidence=self._confidence_from(retrieval.get("results", [])),
            retrieval=retrieval,
            provider=provider,
            grounded=False,
            generation="unavailable",
            needs_clarification=not citations,
            llm_error="citation_validation_failed",
            session_id=session_id,
            conn=conn,
        )

    def _needs_clarification(
        self, analysis: dict[str, Any], total_found: int
    ) -> bool:
        return bool(analysis.get("requires_clarification", False)) or total_found < 3

    def _response(
        self,
        *,
        answer: str,
        language: str,
        analysis: dict[str, Any],
        status: str,
        citations: list[dict[str, Any]] | None = None,
        confidence: str = "low",
        retrieval: dict[str, Any] | None = None,
        provider: dict[str, str] | None = None,
        grounded: bool = False,
        generation: str = "none",
        needs_clarification: bool | None = None,
        llm_error: str | None = None,
        session_id: str | None = None,
        conn: Any = None,
    ) -> dict[str, Any]:
        """Assemble the response contract shared by every outcome.

        ``status``/``grounded``/``generation`` make the outcomes distinguishable:
        an empty answer no longer conflates "nothing matched" with "matches
        exist but are unverified", "the generator is down", or "just a greeting".
        """
        retrieval = retrieval or {}
        return {
            "answer": answer,
            "citations": citations or [],
            "follow_up_questions": self._generate_follow_up_questions(
                analysis, language, has_verified_context=bool(citations),
                session_id=session_id, conn=conn,
            ),
            "needs_clarification": (
                self._needs_clarification(analysis, retrieval.get("total_found", 0))
                if needs_clarification is None
                else needs_clarification
            ),
            "confidence": confidence,
            "disclaimer": disclaimer_for(language),
            # Additive outcome + evidence labels (existing fields unchanged).
            "status": status,
            "grounded": grounded,
            "generation": generation,
            "llm_provider": (provider or {}).get("provider"),
            "llm_model": (provider or {}).get("model"),
            "llm_error": llm_error,
            "retrieval_status": retrieval.get("status"),
            "retrieval_total_found": retrieval.get("total_found", 0),
            "unverified_match_count": retrieval.get("unverified_match_count", 0),
            "search_terms": retrieval.get("tokens", []),
        }

    def _answered_response(
        self,
        *,
        answer: str,
        language: str,
        analysis: dict[str, Any],
        retrieval: dict[str, Any],
        citations: list[dict[str, Any]],
        provider: dict[str, str] | None,
        session_id: str | None = None,
        conn: Any = None,
    ) -> dict[str, Any]:
        """A real, LLM-generated answer grounded in verified provisions."""
        return self._response(
            answer=answer,
            language=language,
            analysis=analysis,
            status=STATUS_ANSWERED,
            citations=citations,
            confidence=self._confidence_from(retrieval.get("results", [])),
            retrieval=retrieval,
            provider=provider,
            grounded=True,
            generation="llm",
            session_id=session_id,
            conn=conn,
        )

    def _no_verified_context_response(
        self,
        *,
        language: str,
        analysis: dict[str, Any],
        retrieval: dict[str, Any],
        session_id: str | None = None,
        conn: Any = None,
    ) -> dict[str, Any]:
        """Safe fallback when no verified provision grounds the question."""
        unverified_only = retrieval.get("status") == STATUS_UNVERIFIED_ONLY
        return self._response(
            answer=insufficient_context_answer(
                language, unverified_only=unverified_only
            ),
            language=language,
            analysis=analysis,
            status=(
                STATUS_NO_VERIFIED_CONTEXT if unverified_only else STATUS_NO_MATCH
            ),
            citations=[],
            confidence="low",
            retrieval=retrieval,
            grounded=False,
            generation="none",
            needs_clarification=True,
            session_id=session_id,
            conn=conn,
        )

    def _generation_unavailable_response(
        self,
        *,
        language: str,
        analysis: dict[str, Any],
        retrieval: dict[str, Any],
        citations: list[dict[str, Any]],
        reason: str,
        provider: dict[str, str] | None,
        session_id: str | None = None,
        conn: Any = None,
    ) -> dict[str, Any]:
        """Verified provisions found, but no answer could be generated."""
        return self._response(
            answer=generation_unavailable_answer(language),
            language=language,
            analysis=analysis,
            status=STATUS_LLM_UNAVAILABLE,
            citations=citations,
            confidence=self._confidence_from(retrieval.get("results", [])),
            retrieval=retrieval,
            provider=provider,
            grounded=False,
            generation="unavailable",
            needs_clarification=not citations,
            llm_error=reason,
            session_id=session_id,
            conn=conn,
        )

    def _retrieval_error_response(
        self, language: str, analysis: dict[str, Any],
        session_id: str | None = None, conn: Any = None
    ) -> dict[str, Any]:
        """The legal knowledge base could not be queried at all."""
        return self._response(
            answer=retrieval_error_answer(language),
            language=language,
            analysis=analysis,
            status=STATUS_RETRIEVAL_ERROR,
            citations=[],
            confidence="low",
            retrieval=None,
            grounded=False,
            generation="none",
            needs_clarification=True,
            llm_error=None,
            session_id=session_id,
            conn=conn,
        )

    def _generate_follow_up_questions(
        self,
        analysis: dict[str, Any],
        language: str = "nepali",
        has_verified_context: bool = False,
        session_id: str | None = None,
        conn: Any = None,
    ) -> list[dict[str, str]]:
        """Generate targeted follow-up questions based on what is still unknown.

        Rules enforced here:
        1. Load the current persisted case context so we know exactly what
           facts have already been captured.
        2. Never ask for a field that is already known (is_known returns True).
        3. Never ask more than MAX_FOLLOW_UP questions.
        4. Stop generating when sufficient information already exists
           (all HIGH-priority fields are known).
        5. Prefer the highest-priority missing fields over lower-priority ones.
        6. Fall back to one generic question only when truly nothing is known —
           never pad with three generic questions.
        """
        case_context: Optional[CaseContext] = None
        if session_id:
            try:
                case_context = self._case_context_manager.get_context(
                    session_id, conn=conn
                )
            except Exception:
                logger.warning("Could not load case context for follow-ups")

        return _build_follow_up_questions(
            case_context=case_context,
            language=language,
            has_verified_context=has_verified_context,
        )

    # _generate_context_aware_follow_ups is retained for backward compatibility
    # with existing unit tests that call it directly.
    def _generate_context_aware_follow_ups(
        self,
        case_context: Optional[CaseContext],
        language: str,
        has_verified_context: bool,
    ) -> list[dict[str, str]]:
        """Delegate to the module-level implementation."""
        return _build_follow_up_questions(
            case_context=case_context,
            language=language,
            has_verified_context=has_verified_context,
        )