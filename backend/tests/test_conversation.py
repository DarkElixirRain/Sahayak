"""Unit tests for the Phase 5 conversation engine.

These tests never touch a database: anything that would reach PostgreSQL
(``get_connection``, the domain lookup) is patched, and the assertions focus on
the pure logic - question analysis, response shaping, schema conformance and
route registration. End-to-end behaviour against a real database is covered by
``tests/integration/test_phase5_conversation.py``.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.conversation import ConversationResponse, FollowUpQuestion
from app.services.conversation import ConversationService
from app.services.legal_grounding import (
    CONTEXT_CLOSE,
    MAX_CONTEXT_ENTRIES,
    build_citations,
    build_context_block,
    context_entry_count,
)

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def service():
    return ConversationService()


@contextmanager
def _fake_db(domain_exists=True):
    """Patch the connection + domain repository used by ``_extract_domain``.

    Lets intent/domain analysis run without a live database.
    """
    conn_cm = MagicMock()
    conn_cm.__enter__.return_value = "conn"
    conn_cm.__exit__.return_value = None

    with (
        patch("app.services.conversation.get_connection", return_value=conn_cm),
        patch("app.repositories.legal_domains.LegalDomainRepository") as repo,
    ):
        repo.return_value.get_by_key.return_value = (
            {"id": "x", "key": "property"} if domain_exists else None
        )
        yield repo


# --------------------------------------------------------------------------- #
# Question analysis
# --------------------------------------------------------------------------- #

def test_empty_query_is_unknown_and_needs_clarification(service):
    for query in ("", "   ", "\n\t "):
        analysis = service.analyze_question(query)
        assert analysis["intent"] == "unknown"
        assert analysis["requires_clarification"] is True
        assert analysis["domain"] is None
        assert analysis["query"] == ""


def test_nepali_keyword_intent(service):
    with _fake_db():
        assert service.analyze_question("धारा १४१ के हो?")["intent"] == "legal_information"
        assert service.analyze_question("मेरो अधिकार के हो?")["intent"] == "rights"


def test_english_keyword_intent(service):
    with _fake_db():
        assert (
            service.analyze_question("what does section 141 say")["intent"]
            == "legal_information"
        )
        assert service.analyze_question("criminal case procedure")["intent"] == "criminal_issue"


def test_mixed_nepali_english_query(service):
    with _fake_db():
        analysis = service.analyze_question("joint property सम्पत्ति को अधिकार")
    assert analysis["intent"] in {"property_issue", "rights"}
    assert analysis["query"] == "joint property सम्पत्ति को अधिकार"


def test_unrelated_text_is_unknown(service):
    assert service.analyze_question("hello there friend")["intent"] == "unknown"


def test_short_query_needs_clarification(service):
    assert service.analyze_question("हो")["requires_clarification"] is True


def test_domain_is_returned_when_it_exists_in_the_database(service):
    with _fake_db(domain_exists=True):
        assert service.analyze_question("मेरो जग्गा को विवाद छ")["domain"] == "property"


def test_domain_is_none_when_missing_from_the_database(service):
    # "criminal" comes from the intent map only: when the repository says the
    # domain row does not exist, no keyword fallback should invent one.
    with _fake_db(domain_exists=False):
        assert service.analyze_question("criminal case procedure")["domain"] is None


def test_entities_are_deduplicated_and_capped(service):
    entities = service.analyze_question(
        "ancestral ancestral ancestral ownership title partition"
    )["entities"]
    assert len(entities) == len(set(entities))
    assert len(entities) <= 8


# --------------------------------------------------------------------------- #
# Response shaping / schema conformance
# --------------------------------------------------------------------------- #

def test_no_retrieval_response_conforms_to_the_schema(service):
    """Regression: follow-up questions must be objects, not bare strings."""
    for query in ("धारा १ जान्न चाहन्छु", "I have a property dispute", "hello"):
        with _fake_db():
            analysis = service.analyze_question(query)
        payload = service._no_verified_context_response(
            language="nepali", analysis=analysis, retrieval={"total_found": 0}
        )
        assert payload["citations"] == []
        assert payload["needs_clarification"] is True
        assert payload["confidence"] == "low"
        assert payload["grounded"] is False
        assert payload["generation"] == "none"

        model = ConversationResponse(**payload)
        assert model.follow_up_questions
        for item in model.follow_up_questions:
            assert isinstance(item, FollowUpQuestion)
            assert item.question


def test_follow_up_questions_conform_to_the_schema(service):
    analysis = {"intent": "property_issue", "domain": "property"}
    for language in ("nepali", "english", "mixed", "unknown"):
        questions = service._generate_follow_up_questions(
            analysis, language, has_verified_context=True
        )
        assert questions, "a known domain must produce at least one suggestion"
        assert len(questions) <= 3
        for item in questions:
            FollowUpQuestion(**item)


def test_follow_up_questions_have_a_default(service):
    questions = service._generate_follow_up_questions(
        {"intent": "unknown", "domain": None}, "nepali"
    )
    assert questions and all(q.get("question") for q in questions)


def test_follow_up_questions_are_language_aware(service):
    analysis = {"intent": "legal_information", "domain": None}
    nepali = service._generate_follow_up_questions(analysis, "nepali")
    english = service._generate_follow_up_questions(analysis, "english")
    assert any("\u0900" <= ch <= "\u097f" for q in nepali for ch in q["question"])
    assert all(q["question"].isascii() for q in english)


def _results(*specs):
    out = []
    for number, title, content, score in specs:
        out.append(
            {
                "document_title": "Muluki Dewani Samhita 2074",
                "section_number": number,
                "section_title": title,
                "content": content,
                "domain": "family",
                "source": "Nepal Law Commission",
                "source_url": "https://example.invalid/law",
                "score": score,
            }
        )
    return out


def test_answered_response_citations_carry_source_traceability(service):
    results = _results(("141", "संरक्षक", "व्यक्ति", 1.0))
    retrieval = {"results": results, "total_found": 1, "status": "ok"}

    payload = service._answered_response(
        answer="\u0938\u0902\u0930\u0915\u094d\u0937\u0915 \u0938\u092e\u094d\u092c\u0928\u094d\u0927\u0940 \u0909\u0924\u094d\u0924\u0930\u0964",
        language="nepali",
        analysis={"intent": "legal_information", "domain": "family"},
        retrieval=retrieval,
        citations=build_citations(results),
        provider={"provider": "groq", "model": "test-model"},
    )

    model = ConversationResponse(**payload)
    assert model.status == "answered"
    assert model.grounded is True
    assert model.generation == "llm"
    assert model.llm_provider == "groq"
    assert model.llm_model == "test-model"
    assert len(model.citations) == 1
    citation = model.citations[0]
    assert citation.document == "Muluki Dewani Samhita 2074"
    assert citation.section == "141"
    assert citation.source == "Nepal Law Commission"
    assert citation.source_url == "https://example.invalid/law"
    assert citation.score == 1.0


def test_confidence_tracks_the_average_score(service):
    for score, expected in ((0.9, "high"), (0.5, "medium"), (0.1, "low")):
        assert service._confidence_from(_results(("1", "T", "C", score))) == expected


def test_confidence_is_low_without_results(service):
    assert service._confidence_from([]) == "low"


def test_answered_response_carries_the_generated_answer(service):
    """The answer is the model's text, not concatenated provision content."""
    results = _results(("1", "T", "क" * 900, 1.0))
    payload = service._answered_response(
        answer="Generated answer text.",
        language="english",
        analysis={"intent": "legal_information", "domain": None},
        retrieval={"results": results, "total_found": 1, "status": "ok"},
        citations=build_citations(results),
        provider=None,
    )
    assert payload["answer"] == "Generated answer text."


def test_case_context_extraction_basic():
    """Test basic case context extraction from user queries."""
    service = ConversationService()

    # Test extracting user role
    with _fake_db():
        analysis = service.analyze_question("मेरो नाम राम हो", [])
        assert "case_context_updates" in analysis
        updates = analysis["case_context_updates"]
        # Should extract that it's about self
        assert updates.get("user_role") == "self" or updates.get("user_role") is not None

        # Test extracting opposing party
        analysis = service.analyze_question("मेरा भाईले मलाई चोरि गरियो", [])
        updates = analysis.get("case_context_updates", {})
        # Should extract brother as opposing party
        assert updates.get("opposing_party") == "brother"

        # Test extracting matter type
        analysis = service.analyze_question("यो सम्पत्तिको मामला हो", [])
        updates = analysis.get("case_context_updates", {})
        # Debug: print what we got
        print(f"Matter type updates: {updates}")
        print(f"Normalized query: {'यो सम्पत्तिको मामला हो'.strip().lower()}")
        assert updates.get("matter_type") == "property"

        # Test extracting location
        analysis = service.analyze_question("म काठमाण्डौमा छु", [])
        updates = analysis.get("case_context_updates", {})
        print(f"Location updates: {updates}")
        print(f"Normalized query for location: {'म काठमाण्डौमा छु'.strip().lower()}")
        assert updates.get("incident_location") == "Kathmandu"

        # Test extracting court information
        analysis = service.analyze_question("जिल्ला अदालतबाट सूचना आएको छ", [])
        updates = analysis.get("case_context_updates", {})
        assert updates.get("court") == "court"
        assert updates.get("court_level") == "district"

        # Test extracting notice
        analysis = service.analyze_question("मलाई सूचना प्राप्त भयो", [])
        updates = analysis.get("case_context_updates", {})
        assert updates.get("notice_received") == True

        # Test extracting deadline
        analysis = service.analyze_question("मาลัย 15 दिनको समय दिएको छ", [])
        updates = analysis.get("case_context_updates", {})
        # Should extract deadline days
        assert updates.get("deadline_days") == 15 or updates.get("deadline") is not None


def test_context_block_caps_entries_and_truncates_content():
    results = _results(*[(str(i), f"T{i}", "क" * 5000, 1.0) for i in range(9)])
    assert context_entry_count(results) == MAX_CONTEXT_ENTRIES == 5

    block = build_context_block(results)
    assert block.count("document:") == MAX_CONTEXT_ENTRIES
    assert len(block) < 5 * 5000  # each entry's text is truncated
    assert CONTEXT_CLOSE in block


# --------------------------------------------------------------------------- #
# Session key normalisation (pure function, no database)
# --------------------------------------------------------------------------- #

def test_valid_uuid_session_keys_pass_through():
    from app.repositories.conversation import session_uuid

    key = "11111111-2222-3333-4444-555555555555"
    assert session_uuid(key) == key


def test_non_uuid_session_keys_are_stable_and_distinct():
    from app.repositories.conversation import session_uuid

    assert session_uuid("sess-abc") == session_uuid("sess-abc")
    assert session_uuid("sess-abc") != session_uuid("sess-xyz")
    # Must be parseable as the UUID column type.
    from uuid import UUID

    UUID(session_uuid("sess-abc"))


# --------------------------------------------------------------------------- #
# Route registration + request validation
# --------------------------------------------------------------------------- #

def test_conversation_routes_are_registered_exactly_once():
    paths = app.openapi()["paths"]
    assert "/api/conversations/{session_id}/messages" in paths
    assert "/api/conversations/{session_id}" in paths
    # The router must not double the application's /api prefix.
    assert not any(p.startswith("/api/api") for p in paths)


def test_post_message_is_registered():
    assert "post" in app.openapi()["paths"]["/api/conversations/{session_id}/messages"]


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"message": ""},
        {"message": "   "},
        {"message": 123},
        {"message": None},
        {"message": ["a"]},
    ],
)
def test_invalid_message_is_rejected_before_any_database_access(body):
    response = client.post("/api/conversations/unit-test-session/messages", json=body)
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "HTTP_ERROR"
    assert "non-empty string" in error["message"]


def test_missing_body_is_rejected():
    response = client.post("/api/conversations/unit-test-session/messages")
    assert response.status_code == 422


def test_non_object_body_is_rejected():
    response = client.post("/api/conversations/unit-test-session/messages", json="hello")
    assert response.status_code == 422
