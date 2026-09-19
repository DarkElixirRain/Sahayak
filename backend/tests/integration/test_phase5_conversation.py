"""Phase 5 conversation integration tests (run against ``TEST_DATABASE_URL``).

These exercise the real conversation engine end to end: sessions are persisted
through the repository, turns are written to ``conversation_messages``, and the
HTTP endpoints are driven with FastAPI's TestClient against a live database.

Seeding: a *verified* provision/chunk is inserted so the grounded path can be
exercised. The engine retrieves with ``verified_only=True`` (a deliberate
policy - answers are never grounded on unverified text), so without verified
fixture data every query would fall into the no-retrieval branch. Marking the
fixture data verified is confined to the throwaway test database; the real
corpus's verification state is never touched.

Every seeded row is created with generated UUIDs and deleted again in teardown,
so nothing outside this test's own rows is ever modified.

If ``TEST_DATABASE_URL`` is not set the whole module skips.
"""

import os
from uuid import uuid4
from typing import Optional

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row
from unittest.mock import patch

import app.core.config as config
from app.db import session as db_session
from app.db.migrate import run_migrations
from app.main import app
from app.repositories.conversation import ConversationRepository, session_uuid
from app.services.conversation import ConversationService
from app.services.llm import LLMCompletion, LLMProvider, LLMTimeoutError

TEST_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_URL,
    reason="TEST_DATABASE_URL not configured",
)


@pytest.fixture(scope="module")
def corpus():
    """Seed a tiny verified corpus in the test database and point the pool at it."""
    run_migrations(TEST_URL)

    original_url = config.settings.database_url
    config.settings.database_url = TEST_URL
    db_session.close_pool()
    db_session.init_pool()

    token = uuid4().hex[:8]
    # Deliberately avoids the analyzer's domain keywords so the query classifies
    # as plain legal_information with no domain filter.
    marker = f"p5m{token}"

    conn = psycopg.connect(TEST_URL, row_factory=dict_row)
    domain_id = uuid4()
    doc_id = uuid4()
    source_id = uuid4()
    provision_id = uuid4()

    rows = {
        "marker": marker,
        "domain_key": f"p5test_{token}",
        "domain_id": domain_id,
        "doc_id": doc_id,
        "doc_title": f"Phase5 Test Act {token}",
        "doc_url": f"https://example.invalid/p5/{token}",
        "source_id": source_id,
        "source_name": f"Phase5 Test Source {token}",
        "provision_id": provision_id,
        "section_number": "141",
        "section_title": f"{marker} संरक्षक व्यवस्था",
        "content": f"{marker} व्यक्ति को संरक्षक सम्बन्धी प्रावधान।",
    }
    # The Phase 4 matcher applies the *whole* normalized query as one ILIKE
    # pattern, so only a single-token query can match the seeded marker. The
    # multi-word form is covered separately as a documented limitation.
    rows["query"] = marker
    rows["natural_query"] = f"धारा {marker} बारे जानकारी"
    rows["unmatched_query"] = f"zzznomatch{token}"
    # Session keys created by the tests, deleted again in teardown.
    rows["session_keys"] = []

    conn.execute(
        "INSERT INTO legal_domains (id, key, name, description, is_active) "
        "VALUES (%s, %s, %s, %s, TRUE)",
        (domain_id, rows["domain_key"], "Phase5 Test Domain", "test fixture"),
    )
    conn.execute(
        """
        INSERT INTO legal_documents
            (id, domain_id, title, document_type, official_source_url, language)
        VALUES (%s, %s, %s, 'act', %s, 'nepali')
        """,
        (doc_id, domain_id, rows["doc_title"], rows["doc_url"]),
    )
    conn.execute(
        """
        INSERT INTO sources (id, name, source_type, official_url, is_official, is_verified)
        VALUES (%s, %s, 'law_commission', %s, TRUE, TRUE)
        """,
        (source_id, rows["source_name"], rows["doc_url"]),
    )
    conn.execute(
        """
        INSERT INTO legal_provisions
            (id, document_id, provision_number, title, text, language)
        VALUES (%s, %s, %s, %s, %s, 'nepali')
        """,
        (provision_id, doc_id, rows["section_number"], rows["section_title"],
         rows["content"]),
    )
    # verified = TRUE so the engine's verified_only=True policy can ground on it.
    conn.execute(
        """
        INSERT INTO knowledge_chunks
            (id, document_id, provision_id, domain_id, source_id, title,
             content, language, chunk_index, source_type, is_verified)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'nepali', 1, 'official_document', TRUE)
        """,
        (uuid4(), doc_id, provision_id, domain_id, source_id,
         rows["section_title"], rows["content"]),
    )
    conn.commit()
    conn.close()

    yield rows

    cleanup = psycopg.connect(TEST_URL, row_factory=dict_row)
    session_uuids = [session_uuid(key) for key in rows["session_keys"]]
    if session_uuids:
        # Messages cascade with their session row.
        cleanup.execute(
            "DELETE FROM conversation_sessions WHERE session_id = ANY(%s)",
            (session_uuids,),
        )
    cleanup.execute("DELETE FROM knowledge_chunks WHERE document_id = %s", (doc_id,))
    cleanup.execute("DELETE FROM legal_provisions WHERE document_id = %s", (doc_id,))
    cleanup.execute("DELETE FROM legal_documents WHERE id = %s", (doc_id,))
    cleanup.execute("DELETE FROM legal_domains WHERE id = %s", (domain_id,))
    cleanup.execute("DELETE FROM sources WHERE id = %s", (source_id,))
    cleanup.commit()
    cleanup.close()

    db_session.close_pool()
    config.settings.database_url = original_url


@pytest.fixture
def sessions(corpus):
    """The session keys used by the tests, cleaned up in the corpus teardown."""
    token = uuid4().hex[:8]
    keys = [f"p5-session-{token}-{i}" for i in range(4)]
    corpus.setdefault("session_keys", []).extend(keys)
    yield keys


@pytest.fixture
def client(corpus, sessions):
    return TestClient(app, raise_server_exceptions=False)


class StubProvider(LLMProvider):
    """Deterministic stand-in for the configured provider."""

    name = "stub"
    model = "stub-model"

    def __init__(self, text: str = "STUB GROUNDED ANSWER", error: Optional[Exception] = None):
        self.text = text
        self.error = error
        self.calls: list[dict] = []

    def generate(self, *, system_prompt, messages, temperature=0.0, max_tokens=900):
        self.calls.append({"system_prompt": system_prompt, "messages": messages})
        if self.error is not None:
            raise self.error
        return LLMCompletion(text=self.text, provider=self.name, model=self.model)


# Grounded-path tests must be hermetic: they stub the provider unless a live
# call is explicitly requested with SAHAYAK_LIVE_LLM=1.
LIVE_LLM = os.getenv("SAHAYAK_LIVE_LLM") == "1"


@pytest.fixture(autouse=True)
def stub_llm():
    if LIVE_LLM:
        yield None
        return
    provider = StubProvider()
    with patch(
        "app.services.conversation.get_llm_provider", return_value=provider
    ):
        yield provider


# --------------------------------------------------------------------------- #
# Session persistence
# --------------------------------------------------------------------------- #

def test_session_creation_is_idempotent_for_the_same_key(corpus):
    key = f"p5-session-{uuid4().hex[:8]}"
    corpus["session_keys"].append(key)

    with db_session.get_connection() as conn:
        repo = ConversationRepository(conn)
        first = repo.create_session(session_id=key, status="active", language="nepali")
        second = repo.create_session(session_id=key, status="ended", language="english")
        fetched = repo.get_session(key)

    assert first["id"] == second["id"], "same key must reuse the same session row"
    assert fetched is not None
    # The conflicting insert must not clobber stored state.
    assert fetched["status"] == "active"
    assert fetched["language"] == "nepali"


def test_non_uuid_session_keys_map_to_valid_uuid_rows(corpus):
    key = f"p5-session-{uuid4().hex[:8]}"
    corpus["session_keys"].append(key)

    with db_session.get_connection() as conn:
        repo = ConversationRepository(conn)
        row = repo.create_session(session_id=key)

    # The stored value is a real UUID (the column type) and stable across calls.
    assert str(row["session_id"]) == session_uuid(key)
    assert str(row["session_id"]) == session_uuid(key)


def test_messages_attach_to_the_session_row_and_are_readable(corpus):
    key = f"p5-session-{uuid4().hex[:8]}"
    corpus["session_keys"].append(key)

    with db_session.get_connection() as conn:
        repo = ConversationRepository(conn)
        repo.create_session(session_id=key)
        repo.add_message(session_id=key, role="user", input_mode="text",
                         content="पहिलो प्रश्न")
        repo.add_message(session_id=key, role="assistant", input_mode="text",
                         content="पहिलो उत्तर")

        count = repo.count_session_messages(key)
        listed = repo.list_session_messages(key)
        context = repo.get_recent_context(key)

    assert count == 2
    assert len(listed) == 2
    assert {m["role"] for m in listed} == {"user", "assistant"}
    # get_recent_context returns chronological order.
    assert [m["content"] for m in context] == ["पहिलो प्रश्न", "पहिलो उत्तर"]


def test_add_message_rejects_an_unknown_session(corpus):
    with db_session.get_connection() as conn:
        repo = ConversationRepository(conn)
        with pytest.raises(ValueError):
            repo.add_message(
                session_id=f"p5-missing-{uuid4().hex[:8]}",
                role="user",
                content="hello",
            )


def test_update_session_status(corpus):
    key = f"p5-session-{uuid4().hex[:8]}"
    corpus["session_keys"].append(key)

    with db_session.get_connection() as conn:
        repo = ConversationRepository(conn)
        repo.create_session(session_id=key, status="active")
        repo.update_session_status(key, "ended")
        row = repo.get_session(key)

    assert row["status"] == "ended"


def test_messages_are_isolated_per_session(corpus, sessions):
    with db_session.get_connection() as conn:
        repo = ConversationRepository(conn)
        for index, key in enumerate(sessions[:2]):
            repo.create_session(session_id=key)
            repo.add_message(session_id=key, role="user", content=f"session {index}")

        assert repo.count_session_messages(sessions[0]) == 1
        assert repo.count_session_messages(sessions[1]) == 1
        assert repo.count_session_messages(sessions[2]) == 0


# --------------------------------------------------------------------------- #
# End-to-end HTTP behaviour
# --------------------------------------------------------------------------- #

def test_post_message_grounds_an_answer_on_the_verified_corpus(client, corpus, sessions):
    key = sessions[0]
    response = client.post(
        f"/api/conversations/{key}/messages",
        json={"message": corpus["query"]},
    )

    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["answer"]
    assert payload["confidence"] in {"high", "medium", "low"}
    assert payload["disclaimer"]
    assert payload["citations"], "a matching verified provision must be cited"

    citation = payload["citations"][0]
    # Every citation value must come from the database rows, not hard-coded text.
    assert citation["document"] == corpus["doc_title"]
    assert citation["section"] == corpus["section_number"]
    assert citation["source"] == corpus["source_name"]
    assert citation["source_url"] == corpus["doc_url"]
    assert citation["score"] > 0


def test_post_message_persists_exactly_one_user_and_one_assistant_turn(
    client, corpus, sessions
):
    key = sessions[1]
    response = client.post(
        f"/api/conversations/{key}/messages",
        json={"message": corpus["query"]},
    )
    assert response.status_code == 200, response.text

    with db_session.get_connection() as conn:
        repo = ConversationRepository(conn)
        messages = repo.list_session_messages(key)
        count = repo.count_session_messages(key)

    assert count == 2, f"expected one user + one assistant turn, got {count}"
    roles = sorted(m["role"] for m in messages)
    assert roles == ["assistant", "user"]


def test_get_conversation_returns_status_and_message_count(client, corpus, sessions):
    key = sessions[2]
    client.post(f"/api/conversations/{key}/messages", json={"message": corpus["query"]})

    response = client.get(f"/api/conversations/{key}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["session_id"] == key
    assert body["status"] == "active"
    assert body["message_count"] == 2


def test_get_unknown_conversation_returns_structured_404(client, corpus):
    response = client.get(f"/api/conversations/p5-unknown-{uuid4().hex[:8]}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_no_match_query_returns_a_valid_fallback_response(client, corpus, sessions):
    key = sessions[3]
    response = client.post(
        f"/api/conversations/{key}/messages",
        json={"message": corpus["unmatched_query"]},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["citations"] == []
    assert payload["needs_clarification"] is True
    assert payload["confidence"] == "low"
    for item in payload["follow_up_questions"]:
        assert item["question"]

    # The fallback reply is persisted too, so history has no unanswered turn.
    with db_session.get_connection() as conn:
        repo = ConversationRepository(conn)
        assert repo.count_session_messages(key) == 2


def test_natural_nepali_sentence_reaches_the_verified_corpus(
    client, corpus, sessions, stub_llm
):
    """Replaces the previous limitation test.

    A full natural sentence used to be matched as one ILIKE substring and so
    matched nothing. Retrieval is now term-based, so the same sentence grounds
    an answer on the seeded provision.
    """
    key = f"p5-session-natural-{uuid4().hex[:8]}"
    corpus["session_keys"].append(key)

    response = client.post(
        f"/api/conversations/{key}/messages",
        json={"message": corpus["natural_query"]},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["citations"], "a natural sentence must find the provision"
    assert payload["citations"][0]["section"] == corpus["section_number"]
    assert payload["status"] == "answered"
    assert payload["grounded"] is True
    assert len(payload["search_terms"]) > 1


def test_unverified_provisions_are_never_cited(client, corpus):
    """The engine retrieves with verified_only=True: an unverified chunk that
    matches the query must not be used to ground an answer."""
    token = uuid4().hex[:8]
    marker = f"p5unverified{token}"
    domain_id, doc_id, source_id, provision_id = (uuid4() for _ in range(4))

    conn = psycopg.connect(TEST_URL, row_factory=dict_row)
    conn.execute(
        "INSERT INTO legal_domains (id, key, name, description, is_active) "
        "VALUES (%s, %s, %s, %s, TRUE)",
        (domain_id, f"p5unverified_{token}", "P5 Unverified Domain", "test fixture"),
    )
    conn.execute(
        """
        INSERT INTO legal_documents
            (id, domain_id, title, document_type, official_source_url, language)
        VALUES (%s, %s, %s, 'act', %s, 'nepali')
        """,
        (doc_id, domain_id, f"Unverified Act {token}", f"https://example.invalid/u/{token}"),
    )
    conn.execute(
        """
        INSERT INTO sources (id, name, source_type, official_url, is_official, is_verified)
        VALUES (%s, %s, 'law_commission', %s, FALSE, FALSE)
        """,
        (source_id, f"Unverified Source {token}", f"https://example.invalid/u/{token}"),
    )
    conn.execute(
        """
        INSERT INTO legal_provisions
            (id, document_id, provision_number, title, text, language)
        VALUES (%s, %s, '1', %s, %s, 'nepali')
        """,
        (provision_id, doc_id, f"{marker} शीर्षक", f"{marker} पाठ उपलब्ध।"),
    )
    conn.execute(
        """
        INSERT INTO knowledge_chunks
            (id, document_id, provision_id, domain_id, source_id, title,
             content, language, chunk_index, source_type, is_verified)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'nepali', 1, 'official_document', FALSE)
        """,
        (uuid4(), doc_id, provision_id, domain_id, source_id,
         f"{marker} शीर्षक", f"{marker} पाठ उपलब्ध।"),
    )
    conn.commit()
    conn.close()

    try:
        key = f"p5-session-unverified-{token}"
        corpus["session_keys"].append(key)
        response = client.post(
            f"/api/conversations/{key}/messages",
            json={"message": marker},
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["citations"] == [], "unverified content must never be cited"
        assert marker not in payload["answer"]
    finally:
        cleanup = psycopg.connect(TEST_URL, row_factory=dict_row)
        cleanup.execute("DELETE FROM knowledge_chunks WHERE document_id = %s", (doc_id,))
        cleanup.execute("DELETE FROM legal_provisions WHERE document_id = %s", (doc_id,))
        cleanup.execute("DELETE FROM legal_documents WHERE id = %s", (doc_id,))
        cleanup.execute("DELETE FROM legal_domains WHERE id = %s", (domain_id,))
        cleanup.execute("DELETE FROM sources WHERE id = %s", (source_id,))
        cleanup.commit()
        cleanup.close()


# --------------------------------------------------------------------------- #
# Grounded generation (stubbed provider)
# --------------------------------------------------------------------------- #

def test_grounded_answer_uses_the_llm_and_database_citations(client, corpus, stub_llm):
    key = f"p5-session-grounded-{uuid4().hex[:8]}"
    corpus["session_keys"].append(key)

    response = client.post(
        f"/api/conversations/{key}/messages", json={"message": corpus["query"]}
    )

    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["status"] == "answered"
    assert payload["grounded"] is True
    assert payload["generation"] == "llm"
    assert payload["answer"] == stub_llm.text
    assert payload["llm_provider"] == "stub"
    assert payload["llm_model"] == "stub-model"

    citation = payload["citations"][0]
    assert citation["document"] == corpus["doc_title"]
    assert citation["document_id"]
    assert citation["chunk_id"]
    assert citation["provision_id"]
    assert citation["section"] == corpus["section_number"]
    assert citation["source"] == corpus["source_name"]
    assert citation["source_url"] == corpus["doc_url"]
    assert citation["is_verified"] is True
    assert citation["chunk_index"] == 1
    assert citation["score"] > 0

    # The model really received the retrieved provision and the strict rules.
    system_prompt = stub_llm.calls[-1]["system_prompt"]
    assert corpus["content"] in system_prompt
    assert "Never invent a provision" in system_prompt
    assert stub_llm.calls[-1]["messages"][-1]["role"] == "user"


def test_multi_turn_history_is_forwarded_to_the_model(client, corpus, stub_llm):
    key = f"p5-session-memory-{uuid4().hex[:8]}"
    corpus["session_keys"].append(key)

    first = client.post(
        f"/api/conversations/{key}/messages", json={"message": corpus["query"]}
    )
    assert first.status_code == 200
    follow_up = f"धारा {corpus['marker']} बारे थप व्यवस्था के छ?"
    second = client.post(
        f"/api/conversations/{key}/messages", json={"message": follow_up}
    )
    assert second.status_code == 200

    assert len(stub_llm.calls) >= 2
    messages = stub_llm.calls[-1]["messages"]
    roles = [m["role"] for m in messages]

    # Prior question + prior answer are present, and the new question appears once.
    assert roles.count("user") >= 2
    assert roles.count("assistant") >= 1
    assert any(corpus["query"] in m["content"] for m in messages)
    assert sum(follow_up in m["content"] for m in messages) == 1

    with db_session.get_connection() as conn:
        repo = ConversationRepository(conn)
        assert repo.count_session_messages(key) == 4


def test_session_history_is_returned_without_internal_ids(client, corpus):
    key = f"p5-session-history-{uuid4().hex[:8]}"
    corpus["session_keys"].append(key)

    client.post(f"/api/conversations/{key}/messages", json={"message": corpus["query"]})
    response = client.get(f"/api/conversations/{key}")

    assert response.status_code == 200
    body = response.json()
    assert body["message_count"] == 2
    assert [m["role"] for m in body["messages"]] == ["user", "assistant"]
    assert all(set(m) == {"role", "content", "created_at"} for m in body["messages"])
    # Only the caller-supplied session key is echoed; no internal row ids and no
    # database UUIDs appear in the history payload.
    assert all(
        "session_id" not in m and "id" not in m for m in body["messages"]
    )
    assert session_uuid(key) not in response.text


def test_llm_timeout_still_returns_the_sources(client, corpus):
    key = f"p5-session-timeout-{uuid4().hex[:8]}"
    corpus["session_keys"].append(key)
    failing = StubProvider(error=LLMTimeoutError("timed out"))

    with patch("app.services.conversation.get_llm_provider", return_value=failing):
        response = client.post(
            f"/api/conversations/{key}/messages", json={"message": corpus["query"]}
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "llm_unavailable"
    assert payload["llm_error"] == "timeout"
    assert payload["grounded"] is False
    assert payload["citations"], "real sources are still reported"
    assert payload["answer"].strip()


def test_unconfigured_llm_is_reported_not_hidden(client, corpus):
    key = f"p5-session-nokey-{uuid4().hex[:8]}"
    corpus["session_keys"].append(key)

    with patch("app.services.conversation.get_llm_provider", return_value=None):
        response = client.post(
            f"/api/conversations/{key}/messages", json={"message": corpus["query"]}
        )

    payload = response.json()
    assert payload["status"] == "llm_unavailable"
    assert payload["llm_error"] == "not_configured"
    assert payload["generation"] == "unavailable"
    assert payload["citations"]


def test_unverified_only_matches_are_labelled_not_answered(client, corpus):
    """Verified-only policy: a match that is not verified must not ground an
    answer, and the response must say so rather than claim "nothing found"."""
    token = uuid4().hex[:8]
    marker = f"p5unvonly{token}"
    domain_id, doc_id, source_id, provision_id = (uuid4() for _ in range(4))

    conn = psycopg.connect(TEST_URL, row_factory=dict_row)
    conn.execute(
        "INSERT INTO legal_domains (id, key, name, description, is_active) "
        "VALUES (%s, %s, %s, %s, TRUE)",
        (domain_id, f"p5unv_{token}", "P5 Unverified", "test fixture"),
    )
    conn.execute(
        """
        INSERT INTO legal_documents
            (id, domain_id, title, document_type, official_source_url, language)
        VALUES (%s, %s, %s, 'act', %s, 'nepali')
        """,
        (doc_id, domain_id, f"Unverified Only Act {token}", f"https://example.invalid/u/{token}"),
    )
    conn.execute(
        """
        INSERT INTO sources (id, name, source_type, official_url, is_official, is_verified)
        VALUES (%s, %s, 'law_commission', %s, FALSE, FALSE)
        """,
        (source_id, f"Unverified Only Source {token}", f"https://example.invalid/u/{token}"),
    )
    conn.execute(
        """
        INSERT INTO legal_provisions
            (id, document_id, provision_number, title, text, language)
        VALUES (%s, %s, '7', %s, %s, 'nepali')
        """,
        (provision_id, doc_id, f"{marker} शीर्षक", f"{marker} पाठ।"),
    )
    conn.execute(
        """
        INSERT INTO knowledge_chunks
            (id, document_id, provision_id, domain_id, source_id, title,
             content, language, chunk_index, source_type, is_verified)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'nepali', 1, 'official_document', FALSE)
        """,
        (uuid4(), doc_id, provision_id, domain_id, source_id,
         f"{marker} शीर्षक", f"{marker} पाठ।"),
    )
    conn.commit()
    conn.close()

    try:
        key = f"p5-session-unvonly-{token}"
        corpus["session_keys"].append(key)
        # A Nepali question containing the marker, so the reply language is
        # Nepali (an ASCII-only marker would correctly get an English reply).
        response = client.post(
            f"/api/conversations/{key}/messages",
            json={"message": f"धारा {marker} बारे जानकारी"},
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["status"] == "no_verified_context"
        assert payload["retrieval_status"] == "unverified_only"
        assert payload["unverified_match_count"] >= 1
        assert payload["citations"] == []
        assert payload["grounded"] is False
        assert marker not in payload["answer"]
        assert "प्रमाणित" in payload["answer"]
    finally:
        cleanup = psycopg.connect(TEST_URL, row_factory=dict_row)
        cleanup.execute("DELETE FROM knowledge_chunks WHERE document_id = %s", (doc_id,))
        cleanup.execute("DELETE FROM legal_provisions WHERE document_id = %s", (doc_id,))
        cleanup.execute("DELETE FROM legal_documents WHERE id = %s", (doc_id,))
        cleanup.execute("DELETE FROM legal_domains WHERE id = %s", (domain_id,))
        cleanup.execute("DELETE FROM sources WHERE id = %s", (source_id,))
        cleanup.commit()
        cleanup.close()


@pytest.mark.skipif(
    LIVE_LLM is False,
    reason="live LLM test: set SAHAYAK_LIVE_LLM=1 (uses real API quota)",
)
def test_live_provider_answers_a_grounded_nepali_question(client, corpus):
    """Opt-in end-to-end call against the configured provider."""
    key = f"p5-session-live-{uuid4().hex[:8]}"
    corpus["session_keys"].append(key)

    response = client.post(
        f"/api/conversations/{key}/messages", json={"message": corpus["query"]}
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "answered", payload.get("llm_error")
    assert payload["answer"].strip()
    assert payload["citations"]


# --------------------------------------------------------------------------- #
# Service-level persistence
# --------------------------------------------------------------------------- #

def test_service_persists_the_assistant_turn_for_grounded_and_fallback_paths(corpus):
    service = ConversationService(provider=StubProvider())
    token = uuid4().hex[:8]

    for label, query in (("grounded", corpus["query"]), ("fallback", corpus["unmatched_query"])):
        key = f"p5-session-service-{label}-{token}"
        corpus["session_keys"].append(key)
        with db_session.get_connection() as conn:
            ConversationRepository(conn).create_session(session_id=key)

        result = service.generate_grounded_response(query=query, session_id=key)
        assert result["answer"]

        with db_session.get_connection() as conn:
            repo = ConversationRepository(conn)
            messages = repo.list_session_messages(key)

        assert len(messages) == 1
        assert messages[0]["role"] == "assistant"
