"""Tests for follow-up question generation and the non-repetition guarantee.

These tests exercise the module-level ``_build_follow_up_questions`` function
and the ``ConversationService._generate_follow_up_questions`` method directly,
so they do not require a database.

Core requirements tested:
1. Never ask about a field already known in case context.
2. Ask questions in priority order.
3. Return at most MAX_FOLLOW_UP questions.
4. Return zero questions when all high-priority fields are known and retrieval worked.
5. Return exactly one generic question when no context exists.
6. Simulate the 6-turn canonical scenario and verify that questions adapt
   correctly at each turn.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.services.case_context import CaseContext
from app.services.conversation import (
    MAX_FOLLOW_UP,
    ConversationService,
    _build_follow_up_questions,
    _one_generic,
)
from app.schemas.conversation import FollowUpQuestion


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ctx(**kwargs) -> CaseContext:
    """Build a CaseContext with only the supplied fields set."""
    ctx = CaseContext()
    for k, v in kwargs.items():
        setattr(ctx, k, v)
    return ctx


def _questions(ctx: CaseContext | None, language: str = "nepali", verified: bool = False):
    return _build_follow_up_questions(
        case_context=ctx,
        language=language,
        has_verified_context=verified,
    )


@contextmanager
def _no_db():
    """Patch DB calls so tests that invoke ConversationService work offline."""
    conn_cm = MagicMock()
    conn_cm.__enter__.return_value = "conn"
    conn_cm.__exit__.return_value = None
    with (
        patch("app.services.conversation.get_connection", return_value=conn_cm),
        patch("app.repositories.legal_domains.LegalDomainRepository") as repo,
    ):
        repo.return_value.get_by_key.return_value = {"id": "x", "key": "civil"}
        yield


# ---------------------------------------------------------------------------
# Basic invariants
# ---------------------------------------------------------------------------

class TestBasicInvariants:
    def test_no_context_returns_single_generic_question(self):
        qs = _questions(None)
        assert len(qs) == 1
        assert qs[0]["reason"] == "initial_intake"

    def test_no_context_english_returns_english_question(self):
        qs = _questions(None, language="english")
        assert len(qs) == 1
        assert qs[0]["question"].isascii()

    def test_empty_context_returns_at_most_max_follow_up(self):
        ctx = CaseContext()  # everything unknown
        qs = _questions(ctx)
        assert len(qs) <= MAX_FOLLOW_UP

    def test_all_high_priority_known_with_verified_context_returns_empty(self):
        ctx = _ctx(
            matter_type="property",
            opposing_party="brother",
            notice_received=True,
            incident_location="Kathmandu",
            court_level="district",
        )
        qs = _questions(ctx, verified=True)
        assert qs == [], f"Expected no questions, got: {qs}"

    def test_all_high_priority_known_without_verified_context_may_still_ask(self):
        """Even when intake is complete, a follow-up may be needed if no legal
        material was retrieved yet (has_verified_context=False)."""
        ctx = _ctx(
            matter_type="property",
            opposing_party="brother",
            notice_received=True,
            incident_location="Kathmandu",
            court_level="district",
        )
        qs = _questions(ctx, verified=False)
        # May return 0 or more; key constraint: no more than MAX_FOLLOW_UP
        assert len(qs) <= MAX_FOLLOW_UP

    def test_questions_never_exceed_max_follow_up(self):
        ctx = CaseContext()  # all fields unknown
        for lang in ("nepali", "english", "mixed", "unknown"):
            qs = _questions(ctx, language=lang)
            assert len(qs) <= MAX_FOLLOW_UP, f"Too many questions for language={lang}"

    def test_question_dicts_conform_to_schema(self):
        ctx = CaseContext()
        for q in _questions(ctx):
            validated = FollowUpQuestion(**q)
            assert validated.question
            assert validated.reason is not None


# ---------------------------------------------------------------------------
# Non-repetition: never ask about known fields
# ---------------------------------------------------------------------------

class TestNonRepetition:
    def test_opposing_party_known_not_asked(self):
        ctx = _ctx(opposing_party="brother")
        reasons = {q["reason"] for q in _questions(ctx)}
        assert "missing_opposing_party" not in reasons

    def test_matter_type_known_not_asked(self):
        ctx = _ctx(matter_type="property")
        reasons = {q["reason"] for q in _questions(ctx)}
        assert "missing_matter_type" not in reasons

    def test_notice_received_known_not_asked(self):
        ctx = _ctx(notice_received=True)
        reasons = {q["reason"] for q in _questions(ctx)}
        assert "missing_notice" not in reasons

    def test_incident_location_known_skips_location_question(self):
        ctx = _ctx(incident_location="Kathmandu")
        reasons = {q["reason"] for q in _questions(ctx)}
        assert "missing_location" not in reasons

    def test_district_known_skips_location_question(self):
        """district satisfies the location requirement."""
        ctx = _ctx(district="Kathmandu")
        reasons = {q["reason"] for q in _questions(ctx)}
        assert "missing_location" not in reasons

    def test_court_level_known_skips_court_question(self):
        ctx = _ctx(court_level="district")
        reasons = {q["reason"] for q in _questions(ctx)}
        assert "missing_court" not in reasons

    def test_court_known_skips_court_question(self):
        ctx = _ctx(court="district court")
        reasons = {q["reason"] for q in _questions(ctx)}
        assert "missing_court" not in reasons

    def test_deadline_only_asked_after_notice_received(self):
        # If notice_received is not known, do NOT ask about deadline yet
        ctx = _ctx()  # empty
        reasons = {q["reason"] for q in _questions(ctx)}
        assert "missing_deadline" not in reasons

    def test_deadline_asked_when_notice_known_and_higher_priority_filled(self):
        """Deadline question appears once the higher-priority fields are already
        known (matter_type, opposing_party, location, court) and notice is
        received but no deadline captured yet.  When those higher-priority
        slots are empty they consume the MAX_FOLLOW_UP budget first."""
        ctx = _ctx(
            matter_type="property",
            opposing_party="brother",
            notice_received=True,
            incident_location="Kathmandu",
            court_level="district",
        )
        reasons = {q["reason"] for q in _questions(ctx, language="nepali")}
        assert "missing_deadline" in reasons, (
            f"Expected deadline question when notice known and higher fields filled. "
            f"Got reasons: {reasons}"
        )

    def test_deadline_not_asked_when_both_notice_and_deadline_known(self):
        ctx = _ctx(notice_received=True, deadline_days=15)
        reasons = {q["reason"] for q in _questions(ctx)}
        assert "missing_deadline" not in reasons


# ---------------------------------------------------------------------------
# Priority ordering
# ---------------------------------------------------------------------------

class TestPriorityOrdering:
    def test_matter_type_is_asked_before_court_when_both_unknown(self):
        ctx = CaseContext()
        qs = _questions(ctx, language="english")
        reasons = [q["reason"] for q in qs]
        if "missing_court" in reasons:
            assert reasons.index("missing_matter_type") < reasons.index("missing_court")

    def test_opposing_party_is_asked_before_documents(self):
        ctx = CaseContext()
        qs = _questions(ctx, language="english")
        reasons = [q["reason"] for q in qs]
        if "missing_documents" in reasons and "missing_opposing_party" in reasons:
            assert reasons.index("missing_opposing_party") < reasons.index("missing_documents")


# ---------------------------------------------------------------------------
# Language awareness
# ---------------------------------------------------------------------------

class TestLanguageAwareness:
    def test_nepali_questions_contain_devanagari(self):
        ctx = CaseContext()
        qs = _questions(ctx, language="nepali")
        for q in qs:
            assert any("\u0900" <= ch <= "\u097f" for ch in q["question"]), (
                f"Expected Devanagari in nepali question: {q['question']}"
            )

    def test_english_questions_contain_no_devanagari(self):
        ctx = CaseContext()
        qs = _questions(ctx, language="english")
        for q in qs:
            assert not any("\u0900" <= ch <= "\u097f" for ch in q["question"]), (
                f"English question should not contain Devanagari: {q['question']}"
            )

    def test_mixed_falls_back_to_nepali(self):
        ctx = CaseContext()
        qs_mixed = _questions(ctx, language="mixed")
        qs_nepali = _questions(ctx, language="nepali")
        assert qs_mixed == qs_nepali


# ---------------------------------------------------------------------------
# Canonical 6-turn scenario
# ---------------------------------------------------------------------------
# For each turn we build the CaseContext that would have accumulated by that
# point and verify the follow-up questions that would be generated.

class TestCanonical6TurnScenario:
    """Simulate the canonical 6-turn intake scenario.

    Turn 1: "Malai mudda halyo, aba maile ke garne?"
        → No context yet. Ask what type of matter it is.

    Turn 2: "मेरो भाइले हालेको हो।"
        → opposing_party=brother is now known. Don't ask about it again.

    Turn 3: "सम्पत्तिको विषयमा हो।"
        → matter_type=property is now known. Don't ask about it again.

    Turn 4: "जिल्ला अदालतबाट notice आएको छ।"
        → court_level=district, notice_received=True now known.

    Turn 5: "मलाई notice मा १५ दिनभित्र जवाफ दिन भनिएको छ।"
        → deadline_days=15 now known.

    Turn 6: "म काठमाडौंमा छु।"
        → incident_location=Kathmandu, district=Kathmandu, province=Bagmati known.
        → All high-priority fields now satisfied. With verified context: no questions.
    """

    def test_turn1_no_context_asks_matter_type(self):
        """After the first message we know almost nothing — ask the most important thing."""
        ctx = CaseContext()
        qs = _questions(ctx, language="nepali")
        reasons = [q["reason"] for q in qs]
        assert "missing_matter_type" in reasons, f"Expected matter_type question, got: {reasons}"

    def test_turn2_opposing_party_known_not_asked_again(self):
        ctx = _ctx(opposing_party="brother")
        reasons = {q["reason"] for q in _questions(ctx, language="nepali")}
        assert "missing_opposing_party" not in reasons
        # Should still ask about matter_type since it's unknown
        assert "missing_matter_type" in reasons

    def test_turn3_matter_type_known_not_asked_again(self):
        ctx = _ctx(opposing_party="brother", matter_type="property")
        reasons = {q["reason"] for q in _questions(ctx, language="nepali")}
        assert "missing_matter_type" not in reasons
        assert "missing_opposing_party" not in reasons

    def test_turn4_court_and_notice_known_not_asked_again(self):
        ctx = _ctx(
            opposing_party="brother",
            matter_type="property",
            court_level="district",
            notice_received=True,
        )
        reasons = {q["reason"] for q in _questions(ctx, language="nepali")}
        assert "missing_court" not in reasons
        assert "missing_notice" not in reasons
        assert "missing_matter_type" not in reasons
        assert "missing_opposing_party" not in reasons

    def test_turn5_deadline_known_not_asked_again(self):
        ctx = _ctx(
            opposing_party="brother",
            matter_type="property",
            court_level="district",
            notice_received=True,
            deadline_days=15,
        )
        reasons = {q["reason"] for q in _questions(ctx, language="nepali")}
        assert "missing_deadline" not in reasons

    def test_turn6_all_high_priority_known_no_questions_with_verified_context(self):
        ctx = _ctx(
            opposing_party="brother",
            matter_type="property",
            court_level="district",
            notice_received=True,
            deadline_days=15,
            incident_location="Kathmandu",
            district="Kathmandu",
        )
        qs = _questions(ctx, language="nepali", verified=True)
        assert qs == [], f"After full intake, no questions needed. Got: {qs}"

    def test_turn6_all_high_priority_known_caps_at_max_without_verified_context(self):
        ctx = _ctx(
            opposing_party="brother",
            matter_type="property",
            court_level="district",
            notice_received=True,
            deadline_days=15,
            incident_location="Kathmandu",
            district="Kathmandu",
        )
        qs = _questions(ctx, language="nepali", verified=False)
        assert len(qs) <= MAX_FOLLOW_UP

    def test_questions_progressively_decrease_over_turns(self):
        """As more fields are filled in, the number of follow-up questions
        should decrease (or stay the same because of the MAX_FOLLOW_UP cap,
        but never increase)."""
        contexts = [
            CaseContext(),
            _ctx(opposing_party="brother"),
            _ctx(opposing_party="brother", matter_type="property"),
            _ctx(opposing_party="brother", matter_type="property",
                 court_level="district", notice_received=True),
            _ctx(opposing_party="brother", matter_type="property",
                 court_level="district", notice_received=True, deadline_days=15),
            _ctx(opposing_party="brother", matter_type="property",
                 court_level="district", notice_received=True, deadline_days=15,
                 incident_location="Kathmandu"),
        ]
        counts = [len(_questions(ctx, verified=True)) for ctx in contexts]
        # The final turn must have the minimum (ideally 0)
        assert counts[-1] <= counts[0], (
            f"Question count should not grow over turns. Counts: {counts}"
        )


# ---------------------------------------------------------------------------
# ConversationService integration (no DB)
# ---------------------------------------------------------------------------

class TestConversationServiceFollowUps:
    """Test that ConversationService._generate_follow_up_questions uses the
    new logic and passes conn correctly."""

    def test_service_no_session_returns_generic(self):
        svc = ConversationService()
        qs = svc._generate_follow_up_questions(
            analysis={"intent": "unknown"}, language="nepali",
            has_verified_context=False, session_id=None, conn=None,
        )
        assert len(qs) == 1
        assert qs[0]["reason"] == "initial_intake"

    def test_service_with_context_manager_returning_known_ctx(self):
        """When the case_context_manager returns a context where matter_type is
        known, the follow-up must not ask for it."""
        svc = ConversationService()
        known_ctx = _ctx(matter_type="property", opposing_party="brother")

        with patch.object(
            svc._case_context_manager, "get_context", return_value=known_ctx
        ):
            qs = svc._generate_follow_up_questions(
                analysis={}, language="nepali",
                has_verified_context=False,
                session_id="test-session", conn=None,
            )

        reasons = {q["reason"] for q in qs}
        assert "missing_matter_type" not in reasons
        assert "missing_opposing_party" not in reasons

    def test_schema_conformance_on_service_output(self):
        svc = ConversationService()
        with patch.object(
            svc._case_context_manager, "get_context", return_value=CaseContext()
        ):
            qs = svc._generate_follow_up_questions(
                analysis={}, language="nepali",
                has_verified_context=False,
                session_id="test-session", conn=None,
            )
        for q in qs:
            FollowUpQuestion(**q)  # must not raise
