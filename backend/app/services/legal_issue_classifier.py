"""Legal issue classifier and query reformulation for Sahayak.

This module takes the persistent CaseContext, conversation history,
and current user message to produce a structured legal understanding
and a clean retrieval query. It does NOT generate legal answers,
cite laws, or invent facts.

It reuses the existing CaseContext, ConversationService analysis,
and legal taxonomy without creating duplicate models.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.case_context import CaseContext, get_case_context_manager
from app.services.conversation import ConversationService, _build_follow_up_questions
from app.services.legal_grounding import detect_language


# ---------------------------------------------------------------------------
# Structured legal issue representation
# ---------------------------------------------------------------------------

class LegalIssue:
    """Structured legal issue extracted from conversation.

    All values are Optional. When a value is not known, it remains None
    rather than being guessed or invented.

    Uses ``__init__`` with keyword arguments so it can be constructed
    from a dict (e.g. ``LegalIssue(**some_dict)``).
    """

    # Core identification
    user_role: Optional[str] = None  # e.g. "self", "possessor", "third_party"
    opposing_party: Optional[str] = None  # e.g. "brother", "sister", "father"

    # Matter classification
    matter_type: Optional[str] = None  # e.g. "property", "family", "criminal"
    matter_subtype: Optional[str] = None  # more specific subtype

    # Jurisdiction
    court: Optional[str] = None  # e.g. "district court", "high court"
    court_level: Optional[str] = None  # e.g. "district", "high", "supreme"
    authority: Optional[str] = None  # e.g. "land office", "tax office"

    # Procedural stage
    notice_received: Optional[bool] = None
    notice_date: Optional[str] = None
    deadline_days: Optional[int] = None
    deadline: Optional[str] = None
    case_number: Optional[str] = None

    # User goal & urgency
    user_goal: Optional[str] = None
    urgency: Optional[str] = None

    # Facts
    incident_description: Optional[str] = None
    incident_date: Optional[str] = None
    incident_location: Optional[str] = None
    district: Optional[str] = None
    province: Optional[str] = None

    # Additional flags
    documents_available: Optional[List[str]] = None
    document_types: Optional[List[str]] = None
    previous_actions: Optional[List[str]] = None
    additional_facts: Optional[str] = None

    def __init__(self, **kwargs: Any) -> None:
        """Initialize LegalIssue with keyword arguments.

        Allows construction via ``LegalIssue(**some_dict)``.
        Only sets attributes that are provided; unspecified ones remain ``None``.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def is_complete_for_retrieval(self) -> bool:
        """Return True when enough essential fields are known to proceed with retrieval.

        Essential fields for property-related retrieval are:
        - matter_type
        - opposing_party (helps narrow search)
        - notice_received (if notice is involved)
        - court/level (filters jurisdiction)
        """
        essential = ["matter_type", "opposing_party", "notice_received", "court", "court_level"]
        known = sum(1 for f in essential if getattr(self, f) is not None)
        return known >= 3  # At least 3 of 5 essential fields

    def missing_critical(self) -> List[str]:
        """Return list of essential field names that are still None."""
        critical = ["matter_type", "opposing_party", "notice_received", "court", "court_level"]
        return [f for f in critical if getattr(self, f) is None]


# ---------------------------------------------------------------------------
# Structured legal issue representation
# ---------------------------------------------------------------------------


class ClassificationResult:
    """Result of legal issue classification.

    Contains the structured issue and a reformulated retrieval query,
    plus metadata about what was found vs. what's still missing.
    """

    issue: LegalIssue
    retrieval_query: str  # clean search query for the existing retrieval system
    language: str  # detected language
    fields_covered: List[str]  # which issue fields have values
    fields_missing: List[str]  # which essential fields are still None
    needs_clarification: bool  # whether follow-up questions are needed
    confidence: str  # "high", "medium", "low" based on how many essential fields are known

    # Essential fields for quick lookup
    _essential = ["matter_type", "opposing_party", "notice_received", "court", "court_level"]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize ClassificationResult with keyword arguments.

        Allows construction via ``ClassificationResult(**some_dict)``.
        Sets all provided attributes; unknown keys are stored as instance
        attributes for future extensibility.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def fields_missing_essential(self) -> List[str]:
        """Return list of essential field names that are still None."""
        return [f for f in self._essential if getattr(self, f, None) is None]


# ---------------------------------------------------------------------------
# Helper: map CaseContext fields to LegalIssue
# ---------------------------------------------------------------------------


def _ctx_to_issue(ctx: CaseContext) -> LegalIssue:
    """Map a CaseContext to a LegalIssue, preserving whatever is known."""
    return LegalIssue(
        # Core identification
        user_role=ctx.user_role,
        opposing_party=ctx.opposing_party,

        # Matter classification
        matter_type=ctx.matter_type,
        matter_subtype=ctx.matter_subtype,

        # Jurisdiction
        court=ctx.court,
        court_level=ctx.court_level,
        authority=ctx.authority,

        # Procedural stage
        notice_received=ctx.notice_received,
        notice_date=ctx.notice_date,
        deadline_days=ctx.deadline_days,
        deadline=ctx.deadline,
        case_number=ctx.case_number,

        # User goal & urgency
        user_goal=ctx.user_goal,
        urgency=ctx.urgency,

        # Facts
        incident_description=ctx.incident_description,
        incident_date=ctx.incident_date,
        incident_location=ctx.incident_location,
        district=ctx.district,
        province=ctx.province,

        # Additional flags
        documents_available=ctx.documents_available,
        document_types=ctx.document_types,
        previous_actions=ctx.previous_actions,
        additional_facts=ctx.additional_facts,
    )


# ---------------------------------------------------------------------------
# Language detection helper
# ---------------------------------------------------------------------------

def _detect_language(text: str) -> str:
    """Detect language using the existing legal_grounding detector."""
    return detect_language(text)


# ---------------------------------------------------------------------------
# Query reformulation
# ---------------------------------------------------------------------------

def _build_retrieval_query_from_issue(issue: LegalIssue, language: str) -> str:
    """Build a clean retrieval query from the LegalIssue.

    Rules:
    - Remove conversational noise ("malai", "mera", etc.)
    - Use existing legal terminology from the taxonomy
    - Append jurisdiction and procedural terms
    - Cap the query at a reasonable length
    - Never invent terms

    The query format adapts to what the existing retrieval system expects:
    term-based ILIKE patterns using the domain-specific Nepali/English terms.
    """

    terms: list[str] = []

    # Matter type — the most important filter
    if issue.matter_type:
        mt = issue.matter_type.lower()
        if mt == "property":
            terms.extend(["सम्पत्ति", "जग्गा", "property"])
        elif mt == "family":
            terms.extend(["विवाह", "ब्याह", "marriage"])
        elif mt == "criminal":
            terms.extend(["फौजदारी", "criminal"])

    # Opposing party — narrows the search
    if issue.opposing_party:
        terms.append(issue.opposing_party)

    # Court/authority — jurisdiction filter
    if issue.court:
        terms.append(issue.court)
    if issue.court_level:
        if issue.court_level == "district":
            terms.extend(["जिल्ला अदालत", "district court"])
        elif issue.court_level == "high":
            terms.extend(["उच्च अदालत", "high court"])
        elif issue.court_level == "supreme":
            terms.extend(["सर्वोच्च अदालत", "supreme court"])

    # Notice / deadline — procedural filter
    if issue.notice_received:
        terms.extend(["सूचना", "notice"])

    if issue.deadline_days:
        # Translate days to Devanagari for consistency
        devanagari_digits = str(issue.deadline_days).translate(
            str.maketrans("0123456789", "०१२३४५६७८९")
        )
        terms.append(f"{devanagari_digits} दिन")

    # Location/district — helps with venue-specific search
    if issue.district:
        terms.append(issue.district)
    if issue.province:
        terms.append(issue.province)

    # User goal — helps narrow intent
    if issue.user_goal:
        terms.append(issue.user_goal)

    # Urgency
    if issue.urgency == "high":
        terms.append(["tatkālik", "urgent", "ajal", "quick"][0])

    # Deduplicate while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for t in terms:
        if t not in seen:
            seen.add(t)
            deduped.append(t)

    # Build query string — join with space, cap at reasonable length
    query = " ".join(deduped)
    # Trim to prevent overly long queries (the retrieval system uses term-based ILIKE)
    if len(query) > 300:
        query = query[:300].rsplit(" ", 1)[0]  # cut at last space

    return query


# ---------------------------------------------------------------------------
# Core classification function
# ---------------------------------------------------------------------------

def classify_legal_issue(
    user_message: str,
    conversation_history: Optional[list[dict[str, str]]] = None,
    session_id: Optional[str] = None,
    service: Optional[ConversationService] = None,
) -> ClassificationResult:
    """Classify the legal issue from a user message and conversation context.

    This is the main entry point. It:

    1. Loads/persists CaseContext from the session (if session_id provided)
    2. Extracts case context updates from the user message via analysis
    3. Merges new facts with existing persisted context
    4. Builds a LegalIssue from the accumulated context
    5. Generates a clean retrieval query
    6. Returns ClassificationResult with metadata

    The CaseContext is the authoritative source — it persists across
    HTTP requests and process restarts.

    Args:
        user_message: The current user's message text.
        conversation_history: Recent conversation messages (role + content).
            Used as supplementary context when session_id is not available.
        session_id: If provided, the CaseContext is loaded from/saved to
            PostgreSQL for this session, surviving process restarts.
        service: Optional ConversationService instance. When None, a new one
            is created (each call gets a fresh service, but the DB-backed
            CaseContext Manager persists the context).

    Returns:
        ClassificationResult containing the structured issue and reformulated
        retrieval query.
    """

    # ------------------------------------------------------------------
    # 1. Initialize service and load case context
    # ------------------------------------------------------------------
    if service is None:
        service = ConversationService()

    # Load existing case context from the session (persisted in DB)
    ctx: CaseContext = CaseContext()
    if session_id:
        ctx = service._case_context_manager.get_context(session_id)

# ------------------------------------------------------------------
    # 2. Extract case context updates from the user message
    # ------------------------------------------------------------------
    analysis = service.analyze_question(user_message, conversation_history)

    # Update context with new extractions from this message
    case_context_updates = analysis.get("case_context_updates", {})
    if case_context_updates:
        ctx = service._case_context_manager.update_context(
            session_id or "temp-session", **case_context_updates
        )
        # Re-fetch the (possibly updated) context
        if session_id:
            ctx = service._case_context_manager.get_context(session_id)
        else:
            # For isolated calls, we got the updated context directly
            pass

    # ------------------------------------------------------------------
    # 3. Map CaseContext to LegalIssue
    # ------------------------------------------------------------------
    issue = _ctx_to_issue(ctx)

    # ------------------------------------------------------------------
    # 4. Detect language
    # ------------------------------------------------------------------
    language = _detect_language(user_message)

    # ------------------------------------------------------------------
    # 5. Build retrieval query from the accumulated issue
    # ------------------------------------------------------------------
    retrieval_query = _build_retrieval_query_from_issue(issue, language)

    # ------------------------------------------------------------------
    # 6. Determine completeness and missing fields
    # ------------------------------------------------------------------
    fields_covered: list[str] = []
    fields_missing: list[str] = []

    # Check which issue fields have values
    for field_name in [
        "matter_type", "opposing_party", "court", "court_level",
        "notice_received", "user_role", "urgency", "user_goal",
        "deadline_days", "deadline", "case_number",
        "incident_description", "incident_location", "district", "province"
    ]:
        val = getattr(issue, field_name)
        if val is not None:
            fields_covered.append(field_name)
        else:
            fields_missing.append(field_name)

    # Check essential fields for retrieval
    essential = ["matter_type", "opposing_party", "notice_received", "court", "court_level"]
    fields_missing_essential = [f for f in essential if getattr(issue, f) is None]
    needs_clarification = len(fields_missing_essential) > 0

    # Confidence based on how many essential fields are known
    essential_known = sum(1 for f in essential if getattr(issue, f) is not None)
    if essential_known >= 4:
        confidence = "high"
    elif essential_known >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    # ------------------------------------------------------------------
    # 7. Return ClassificationResult
    # ------------------------------------------------------------------
    return ClassificationResult(
        issue=issue,
        retrieval_query=retrieval_query,
        language=language,
        fields_covered=fields_covered,
        fields_missing=fields_missing,
        needs_clarification=needs_clarification,
        confidence=confidence,
    )


# ---------------------------------------------------------------------------
# Convenience: classify from just a message (no session, context lost)
# ---------------------------------------------------------------------------

def classify_message_isolated(user_message: str) -> ClassificationResult:
    """Classify a message without session persistence.

    Useful for one-off classification where the CaseContext is not
    preserved across calls. Each call starts with an empty context.

    Note: This does NOT persist context — the CaseContext is local only
    to this invocation and is lost between calls. Use
    classify_legal_issue() with a session_id for persistent conversations.
    """

    service = ConversationService()
    result = classify_legal_issue(user_message, session_id=None, service=service)

    return result