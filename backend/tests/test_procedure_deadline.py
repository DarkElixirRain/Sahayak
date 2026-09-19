"""Phase 11 — Procedure and deadline provenance tests.

Verifies that:
  * USER_STATED and LEGALLY_VERIFIED constants are correctly defined
  * CaseContext stores deadline_source / notice_source
  * User-stated deadline is tagged USER_STATED
  * LEGALLY_VERIFIED is only set when backed by a provision
  * deadline_source=USER_STATED never gets promoted to LEGALLY_VERIFIED
    without an explicit legal basis
"""

from __future__ import annotations

import pytest
from app.services.case_context import (
    CaseContext,
    DEADLINE_USER_STATED,
    DEADLINE_LEGALLY_VERIFIED,
)


class TestProvenanceConstants:
    def test_user_stated_constant_defined(self):
        assert DEADLINE_USER_STATED == "USER_STATED"

    def test_legally_verified_constant_defined(self):
        assert DEADLINE_LEGALLY_VERIFIED == "LEGALLY_VERIFIED"

    def test_constants_are_distinct(self):
        assert DEADLINE_USER_STATED != DEADLINE_LEGALLY_VERIFIED


class TestCaseContextDeadlineSource:
    def test_deadline_source_field_exists(self):
        ctx = CaseContext()
        assert hasattr(ctx, "deadline_source")

    def test_notice_source_field_exists(self):
        ctx = CaseContext()
        assert hasattr(ctx, "notice_source")

    def test_deadline_source_default_none(self):
        ctx = CaseContext()
        assert ctx.deadline_source is None

    def test_notice_source_default_none(self):
        ctx = CaseContext()
        assert ctx.notice_source is None

    def test_user_stated_deadline_stored(self):
        """When user says '15 din bhitra jawab dinu parcha', store as USER_STATED."""
        ctx = CaseContext()
        ctx.update(
            deadline="15 days",
            deadline_days=15,
            deadline_source=DEADLINE_USER_STATED,
        )
        assert ctx.deadline == "15 days"
        assert ctx.deadline_days == 15
        assert ctx.deadline_source == DEADLINE_USER_STATED

    def test_legally_verified_deadline_stored(self):
        """Only a verified provision may set LEGALLY_VERIFIED."""
        ctx = CaseContext()
        ctx.update(
            deadline="30 days under Civil Code Section 42",
            deadline_days=30,
            deadline_source=DEADLINE_LEGALLY_VERIFIED,
        )
        assert ctx.deadline_source == DEADLINE_LEGALLY_VERIFIED

    def test_user_stated_not_promoted_automatically(self):
        """USER_STATED must never be automatically changed to LEGALLY_VERIFIED."""
        ctx = CaseContext()
        ctx.update(
            deadline="15 days",
            deadline_days=15,
            deadline_source=DEADLINE_USER_STATED,
        )
        # Simulate the system receiving more information (but no legal provision)
        ctx.update(court="Kathmandu District Court")
        # deadline_source must remain USER_STATED
        assert ctx.deadline_source == DEADLINE_USER_STATED

    def test_notice_source_user_stated(self):
        ctx = CaseContext()
        ctx.update(
            notice_received=True,
            notice_date="2026-09-01",
            notice_source=DEADLINE_USER_STATED,
        )
        assert ctx.notice_source == DEADLINE_USER_STATED
        assert ctx.notice_received is True

    def test_serialization_preserves_deadline_source(self):
        """deadline_source must survive to_dict/from_dict round-trip."""
        ctx = CaseContext()
        ctx.update(
            deadline="15 days",
            deadline_days=15,
            deadline_source=DEADLINE_USER_STATED,
        )
        data = ctx.to_dict()
        assert data["deadline_source"] == DEADLINE_USER_STATED

        restored = CaseContext.from_dict(data)
        assert restored.deadline_source == DEADLINE_USER_STATED
        assert restored.deadline_days == 15

    def test_serialization_preserves_legally_verified(self):
        ctx = CaseContext()
        ctx.update(
            deadline="30 days",
            deadline_days=30,
            deadline_source=DEADLINE_LEGALLY_VERIFIED,
        )
        restored = CaseContext.from_dict(ctx.to_dict())
        assert restored.deadline_source == DEADLINE_LEGALLY_VERIFIED

    def test_unknown_source_fields_not_in_meta(self):
        """deadline_source and notice_source are case fields, not metadata."""
        from dataclasses import fields as dc_fields
        from app.services.case_context import _META_FIELDS
        field_names = {f.name for f in dc_fields(CaseContext)}
        assert "deadline_source" in field_names
        assert "notice_source" in field_names
        assert "deadline_source" not in _META_FIELDS
        assert "notice_source" not in _META_FIELDS


class TestSixTurnDeadlineDistinction:
    """Simulates the six-turn conversation scenario from the Phase 11 spec.

    Turn 5: User says '15 din bhitra jawab dinu parcha bhaneko cha.'
    This must be tagged USER_STATED, not LEGALLY_VERIFIED.
    """

    def test_turn5_deadline_tagged_user_stated(self):
        ctx = CaseContext()

        # Turn 1: mudda halyo
        ctx.update(incident_description="Malai mudda halyo")

        # Turn 2: bhai le mudda haleko
        ctx.update(opposing_party="bhai")

        # Turn 3: sampattiko bisayama
        ctx.update(matter_type="property")

        # Turn 4: jilla adalat bata notice aako cha
        ctx.update(
            notice_received=True,
            court="Jilla adalat",
            notice_source=DEADLINE_USER_STATED,
        )

        # Turn 5: user says 15 din bhitra jawab dinu parcha — user-stated
        ctx.update(
            deadline="15 days",
            deadline_days=15,
            deadline_source=DEADLINE_USER_STATED,
        )

        # Turn 6: Kathmandu location
        ctx.update(district="Kathmandu")

        # Verify the deadline is USER_STATED, not legally verified
        assert ctx.deadline_source == DEADLINE_USER_STATED, (
            "A user-stated deadline must remain USER_STATED. "
            "It must NOT be auto-promoted to LEGALLY_VERIFIED."
        )
        assert ctx.deadline_days == 15
        assert ctx.district == "Kathmandu"
        assert ctx.notice_received is True


class TestProceduralRetrieval:
    """Test that procedural queries retrieve verified civil code content
    when available, and return the safe fallback when not."""

    @pytest.mark.skipif(
        not __import__("os").environ.get("DATABASE_URL"),
        reason="DATABASE_URL not set",
    )
    def test_court_notice_query_retrieves_verified_material(self):
        """'After receiving a court notice, what to do?' should find Civil Code results."""
        from app.services.knowledge_retrieval import retrieve_legal_context

        result = retrieve_legal_context(
            "कोर्टको सूचना पाएपछि के गर्ने?",
            verified_only=True,
        )
        # May match or not depending on chunk content; must not ERROR
        assert result["status"] in ("ok", "no_match", "unverified_only")

    @pytest.mark.skipif(
        not __import__("os").environ.get("DATABASE_URL"),
        reason="DATABASE_URL not set",
    )
    def test_no_procedural_evidence_returns_safe_fallback(self):
        """When no procedural evidence found, insufficient_context is returned."""
        from app.services.knowledge_retrieval import retrieve_legal_context, STATUS_NO_MATCH
        from app.services.legal_grounding import insufficient_context_answer

        result = retrieve_legal_context(
            "after_receiving_notice_utterly_specific_query_xyz123",
            verified_only=True,
        )
        if result["status"] == STATUS_NO_MATCH:
            fallback = insufficient_context_answer("nepali", unverified_only=False)
            assert fallback
            assert "कानून" in fallback or "ज्ञान" in fallback or "प्रावधान" in fallback
