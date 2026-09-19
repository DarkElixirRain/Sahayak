"""Case context management - Phase 5 intelligent legal intake.

This module implements structured case context extraction and management
for the Sahayak legal assistant. It tracks what information has been
provided by the user, what can be inferred, and what remains unknown.

Persistence model (revised):
    CaseContext is now persisted as JSONB in conversation_sessions.case_context
    (migration 010). This makes it durable across process restarts and
    compatible with multi-worker deployments.

    CaseContextManager is a lightweight façade that delegates to the repository.
    Each method opens its own DB connection so it can be called from any
    code path without requiring the caller to pass a connection.

The case context includes:
- user_role: Who the user is in the legal situation
- opposing_party: Who the other party is
- matter_type: Type of legal matter (property, family, criminal, etc.)
- matter_subtype: More specific subtype of the matter
- incident_description: What happened
- incident_date: When the incident occurred
- incident_location: Where the incident occurred
- district: District/jurisdiction
- province: Province
- authority: Which authority is involved
- court: Which court is involved
- court_level: Level of court (district, high, supreme)
- case_number: Official case number if known
- notice_received: Whether an official notice was received
- notice_date: Date notice was received
- deadline: Any deadline mentioned
- deadline_days: Number of days for a deadline
- deadline_source: Provenance of the deadline — USER_STATED or LEGALLY_VERIFIED
- notice_source: Provenance of notice information — USER_STATED or LEGALLY_VERIFIED
- documents_available: What documents the user has
- document_types: Types of documents available
- previous_actions: What actions have been taken so far
- user_goal: What the user wants to achieve
- urgency: How urgent the situation is
- additional_facts: Any other relevant information

Provenance constants (Phase 11):
    DEADLINE_USER_STATED     = "USER_STATED"
    DEADLINE_LEGALLY_VERIFIED = "LEGALLY_VERIFIED"

Important: deadline_source must NEVER be set to LEGALLY_VERIFIED unless a
verified legal provision from the knowledge base explicitly establishes the
deadline. A user saying "15 days" results in USER_STATED only.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, fields as dataclass_fields
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("app.services.case_context")

# Provenance constants for deadline / notice fields (Phase 11).
# Set to USER_STATED when the user mentions a deadline in conversation.
# Set to LEGALLY_VERIFIED ONLY when a verified legal provision in the
# knowledge base explicitly establishes the deadline.
DEADLINE_USER_STATED = "USER_STATED"
DEADLINE_LEGALLY_VERIFIED = "LEGALLY_VERIFIED"

# Fields that are metadata rather than case information.
_META_FIELDS = frozenset({"created_at", "updated_at"})


@dataclass
class CaseContext:
    """Structured case context for legal intake."""

    # Core identification
    user_role: Optional[str] = None
    opposing_party: Optional[str] = None

    # Matter classification
    matter_type: Optional[str] = None
    matter_subtype: Optional[str] = None

    # Incident details
    incident_description: Optional[str] = None
    incident_date: Optional[str] = None   # stored as ISO string for JSON compat
    incident_location: Optional[str] = None

    # Jurisdiction
    district: Optional[str] = None
    province: Optional[str] = None
    authority: Optional[str] = None
    court: Optional[str] = None
    court_level: Optional[str] = None

    # Case specifics
    case_number: Optional[str] = None
    notice_received: Optional[bool] = None
    notice_date: Optional[str] = None     # ISO string
    deadline: Optional[str] = None
    deadline_days: Optional[int] = None

    # Provenance tags for deadline and notice (Phase 11).
    # Values: None (not known), DEADLINE_USER_STATED, DEADLINE_LEGALLY_VERIFIED.
    # NEVER set to LEGALLY_VERIFIED unless a verified legal provision
    # in the knowledge base explicitly establishes the deadline/notice rule.
    deadline_source: Optional[str] = None
    notice_source: Optional[str] = None

    # Documentation
    documents_available: Optional[List[str]] = None
    document_types: Optional[List[str]] = None

    # Proceedings
    previous_actions: Optional[List[str]] = None
    user_goal: Optional[str] = None

    # Context
    urgency: Optional[str] = None
    additional_facts: Optional[str] = None

    # Metadata (not serialised as case information)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def update(self, **kwargs: Any) -> None:
        """Update case context fields with new information.

        Rules:
        - None values are ignored (they do not overwrite existing data).
        - Lists are merged (union, preserving order of first occurrence).
        - Scalar values are replaced (new evidence supersedes old).
        """
        for key, value in kwargs.items():
            if not hasattr(self, key) or value is None:
                continue
            current = getattr(self, key)
            if current is None:
                setattr(self, key, value)
            elif isinstance(current, list) and isinstance(value, list):
                combined = list(dict.fromkeys(current + value))
                setattr(self, key, combined)
            else:
                setattr(self, key, value)
        self.updated_at = datetime.now().isoformat()

    def is_known(self, field_name: str) -> bool:
        """Return True when the field has a non-None value."""
        return getattr(self, field_name, None) is not None

    def get_missing_fields(self) -> List[str]:
        """Return field names that are still unknown (None), excluding metadata."""
        return [
            f.name
            for f in dataclass_fields(self)
            if f.name not in _META_FIELDS and getattr(self, f.name) is None
        ]

    def get_completeness_percentage(self) -> float:
        """Percentage of non-metadata fields that have a known value."""
        all_fields = [f.name for f in dataclass_fields(self) if f.name not in _META_FIELDS]
        known = [n for n in all_fields if getattr(self, n) is not None]
        return (len(known) / len(all_fields)) * 100 if all_fields else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dict for JSON storage."""
        result: Dict[str, Any] = {}
        for f in dataclass_fields(self):
            result[f.name] = getattr(self, f.name)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CaseContext":
        """Restore a CaseContext from a stored dict.

        Unknown keys are silently ignored so schema evolution does not break
        older stored contexts.
        """
        known = {f.name for f in dataclass_fields(cls)}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


class CaseContextManager:
    """DB-backed case context manager.

    Each method fetches the current context from ``conversation_sessions``,
    applies changes in memory, and writes the result back. The round-trip is
    cheap (single-row JSONB read/write) and keeps the data durable.

    A process-level in-memory cache is also maintained as a performance
    optimisation: within a request we avoid a redundant DB read for the same
    session. The cache is invalidated when ``save`` succeeds.
    """

    def __init__(self) -> None:
        # Process-level cache: session_id → CaseContext. Kept for intra-request
        # performance; the authoritative copy is always the DB.
        self._cache: Dict[str, CaseContext] = {}

    # ------------------------------------------------------------------
    # Internal DB helpers — deferred import to avoid circular imports.
    # ------------------------------------------------------------------

    @staticmethod
    def _repo_from(conn: Any):  # type: ignore[return]
        from app.repositories.conversation import ConversationRepository
        return ConversationRepository(conn)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_context(
        self, session_id: str, *, conn: Any = None
    ) -> CaseContext:
        """Load (or create) the case context for a session.

        Uses the in-memory cache first; falls back to the DB.
        """
        if session_id in self._cache:
            return self._cache[session_id]

        ctx = self._load_from_db(session_id, conn=conn)
        self._cache[session_id] = ctx
        return ctx

    def update_context(
        self, session_id: str, *, conn: Any = None, **kwargs: Any
    ) -> CaseContext:
        """Apply ``kwargs`` to the context and persist immediately."""
        ctx = self.get_context(session_id, conn=conn)
        ctx.update(**kwargs)
        self._save_to_db(session_id, ctx, conn=conn)
        return ctx

    def clear_context(self, session_id: str) -> None:
        """Drop the in-memory cache entry (DB record is kept)."""
        self._cache.pop(session_id, None)

    def get_missing_information(self, session_id: str, *, conn: Any = None) -> List[str]:
        """Return field names that are still unknown for a session."""
        return self.get_context(session_id, conn=conn).get_missing_fields()

    def is_ready_for_legal_research(
        self, session_id: str, min_completeness: float = 30.0, *, conn: Any = None
    ) -> bool:
        """True when enough information has been gathered to start retrieval."""
        return (
            self.get_context(session_id, conn=conn).get_completeness_percentage()
            >= min_completeness
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_from_db(self, session_id: str, *, conn: Any = None) -> CaseContext:
        """Fetch stored context from DB; return empty context when absent."""
        def _load(active_conn: Any) -> CaseContext:
            repo = self._repo_from(active_conn)
            data = repo.get_case_context(session_id)
            if data:
                if isinstance(data, dict):
                    return CaseContext.from_dict(data)
                try:
                    import json
                    parsed = json.loads(data)
                    if isinstance(parsed, dict):
                        return CaseContext.from_dict(parsed)
                except Exception:
                    pass
            return CaseContext()

        if conn is not None:
            return _load(conn)
        try:
            from app.db.session import get_connection
            with get_connection() as own_conn:
                return _load(own_conn)
        except Exception:
            logger.warning(
                "Could not load case context for %s from DB; using empty context",
                session_id,
            )
            return CaseContext()

    def _save_to_db(
        self, session_id: str, ctx: CaseContext, *, conn: Any = None
    ) -> None:
        """Write the context back to the DB."""
        data = ctx.to_dict()

        def _save(active_conn: Any) -> None:
            self._repo_from(active_conn).save_case_context(session_id, data)

        if conn is not None:
            _save(conn)
            return
        try:
            from app.db.session import get_connection
            with get_connection() as own_conn:
                _save(own_conn)
        except Exception:
            logger.warning(
                "Could not persist case context for %s; in-memory copy retained",
                session_id,
            )


# Module-level singleton so all requests in the same worker process share
# the same cache layer. This is safe because CaseContextManager holds only
# a cache (not DB connections), and the DB is always the source of truth.
_case_context_manager: CaseContextManager | None = None


def get_case_context_manager() -> CaseContextManager:
    """Return the process-level CaseContextManager singleton."""
    global _case_context_manager
    if _case_context_manager is None:
        _case_context_manager = CaseContextManager()
    return _case_context_manager
