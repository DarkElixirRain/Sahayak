"""Phase 4 retrieval integration tests (run against ``TEST_DATABASE_URL``).

These exercise the **real** retrieval service end to end: a small corpus is
seeded, the service queries it through the application's psycopg 3 connection
pool, and results are asserted including ranking order, thresholds, filters,
traceability and Unicode handling.

Why the data is committed rather than rolled back: ``retrieve_legal_context``
acquires its own connection from the application pool, so data written inside
an uncommitted transaction on a different connection would be invisible.
Every seeded row is created with generated UUIDs and deleted again in
teardown, so nothing outside this test's own rows is ever touched.

If ``TEST_DATABASE_URL`` is not set the whole module skips.
"""

import os
from uuid import uuid4

import psycopg
import pytest
from psycopg.rows import dict_row

import app.core.config as config
from app.db import session as db_session
from app.db.migrate import run_migrations
from app.services.knowledge_retrieval import retrieve_legal_context

TEST_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_URL,
    reason="TEST_DATABASE_URL not configured",
)



@pytest.fixture(scope="module")
def corpus():
    """Seed a tiny corpus in the test database and point the pool at it."""
    run_migrations(TEST_URL)

    original_url = config.settings.database_url
    config.settings.database_url = TEST_URL
    db_session.close_pool()
    db_session.init_pool()

    token = uuid4().hex[:8]
    html_marker = f"p4marker{token}"
    nepali_marker = f"संरक्षक{token}"

    conn = psycopg.connect(TEST_URL, row_factory=dict_row)
    domain_id = uuid4()
    doc_id = uuid4()
    source_id = uuid4()
    rows = {
        "domain_key": f"p4test_{token}",
        "domain_id": domain_id,
        "doc_id": doc_id,
        "doc_title": f"Phase4 Test Act {token}",
        "source_id": source_id,
        # (provision_number, title, content)
        "provisions": {
            # title AND content match -> 1.4 with a domain filter
            "1": (f"{html_marker} Guardian Duty", f"{html_marker} provision body text."),
            # content only -> 1.1
            "2": ("Unrelated Heading", f"{html_marker} content only body text."),
            # title only -> 0.4
            "3": (f"{html_marker} Title Only", "This body does not contain the token."),
            # neither -> must never be returned
            "4": ("Nothing Here", "Completely unrelated provision body."),
            # Nepali marker for Unicode coverage -> 1.1
            "141": (f"{nepali_marker} नेपाली शीर्षक", f"{nepali_marker} नेपाली पाठ।"),
        },
        "marker": html_marker,
        "nepali_marker": nepali_marker,
    }
    rows["nepali_query"] = nepali_marker

    conn.execute(
        "INSERT INTO legal_domains (id, key, name, description, is_active) "
        "VALUES (%s, %s, %s, %s, TRUE)",
        (domain_id, rows["domain_key"], "Phase4 Test Domain", "test fixture"),
    )
    conn.execute(
        """
        INSERT INTO legal_documents
            (id, domain_id, title, document_type, official_source_url, language)
        VALUES (%s, %s, %s, 'act', %s, 'nepali')
        """,
        (doc_id, domain_id, rows["doc_title"], f"https://example.invalid/{token}"),
    )
    conn.execute(
        """
        INSERT INTO sources (id, name, source_type, official_url, is_official, is_verified)
        VALUES (%s, %s, 'law_commission', %s, TRUE, FALSE)
        """,
        (source_id, f"Phase4 Test Source {token}", f"https://example.invalid/{token}"),
    )
    for number, (title, content) in rows["provisions"].items():
        provision_id = uuid4()
        conn.execute(
            """
            INSERT INTO legal_provisions
                (id, document_id, provision_number, title, text, language)
            VALUES (%s, %s, %s, %s, %s, 'nepali')
            """,
            (provision_id, doc_id, number, title, content),
        )
        conn.execute(
            """
            INSERT INTO knowledge_chunks
                (id, document_id, provision_id, domain_id, source_id, title,
                 content, language, chunk_index, source_type, is_verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'nepali', 1, 'official_document', FALSE)
            """,
            (uuid4(), doc_id, provision_id, domain_id, source_id, title, content),
        )
    conn.commit()
    conn.close()

    yield rows

    # Scoped cleanup: only rows this fixture created, by their IDs.
    cleanup = psycopg.connect(TEST_URL, row_factory=dict_row)
    cleanup.execute("DELETE FROM knowledge_chunks WHERE document_id = %s", (doc_id,))
    cleanup.execute("DELETE FROM legal_provisions WHERE document_id = %s", (doc_id,))
    cleanup.execute("DELETE FROM legal_documents WHERE id = %s", (doc_id,))
    cleanup.execute("DELETE FROM legal_domains WHERE id = %s", (domain_id,))
    cleanup.execute("DELETE FROM sources WHERE id = %s", (source_id,))
    cleanup.commit()
    cleanup.close()

    db_session.close_pool()
    config.settings.database_url = original_url


# --------------------------------------------------------------------------- #
# Ranking
# --------------------------------------------------------------------------- #

def test_ranking_follows_the_documented_weights(corpus):
    """content x1.0, title x0.3, domain x0.1 — with a domain filter:
    1.4 (title+content+domain), 1.1 (content+domain), 0.4 (title+domain)."""
    result = retrieve_legal_context(
        query=corpus["marker"],
        domain_id=corpus["domain_key"],
        document_filter=[corpus["doc_title"]],
        verified_only=False,
        top_k=10,
        minimum_score=0.0,
    )

    scores = {r["section_number"]: r["score"] for r in result["results"]}
    assert scores["1"] == pytest.approx(1.4)
    assert scores["2"] == pytest.approx(1.1)
    assert scores["3"] == pytest.approx(0.4)
    assert "4" not in scores, "non-matching provision must never be returned"

    # Descending by score; ties broken deterministically.
    assert [r["section_number"] for r in result["results"]] == ["1", "2", "3"]


def test_ranking_is_deterministic_across_runs(corpus):
    kwargs = dict(
        query=corpus["marker"], document_filter=[corpus["doc_title"]],
        verified_only=False, top_k=10, minimum_score=0.0,
    )
    first = retrieve_legal_context(**kwargs)
    second = retrieve_legal_context(**kwargs)
    assert [r["section_number"] for r in first["results"]] == [
        r["section_number"] for r in second["results"]
    ]


def test_domain_filter_adds_the_domain_signal(corpus):
    common = dict(
        query=corpus["marker"], document_filter=[corpus["doc_title"]],
        verified_only=False, top_k=10, minimum_score=0.0,
    )
    with_domain = retrieve_legal_context(domain_id=corpus["domain_key"], **common)
    without_domain = retrieve_legal_context(**common)

    a_with = next(r for r in with_domain["results"] if r["section_number"] == "1")
    a_without = next(r for r in without_domain["results"] if r["section_number"] == "1")
    assert a_with["score"] - a_without["score"] == pytest.approx(0.1)


# --------------------------------------------------------------------------- #
# top_k / minimum_score
# --------------------------------------------------------------------------- #

def test_top_k_limits_results(corpus):
    result = retrieve_legal_context(
        query=corpus["marker"], document_filter=[corpus["doc_title"]],
        verified_only=False, top_k=2, minimum_score=0.0,
    )
    assert len(result["results"]) == 2
    assert result["total_found"] >= 3, "total_found counts matches before slicing"


def test_minimum_score_filters_results(corpus):
    # With the domain filter the scores are 1.4 / 1.1 / 0.4 for sections
    # 1 / 2 / 3, so a 1.2 threshold keeps only section 1 and a 1.05 threshold
    # keeps sections 1 and 2.
    scope = dict(
        query=corpus["marker"], domain_id=corpus["domain_key"],
        document_filter=[corpus["doc_title"]], verified_only=False, top_k=10,
    )
    high = retrieve_legal_context(minimum_score=1.2, **scope)
    assert [r["section_number"] for r in high["results"]] == ["1"]

    mid = retrieve_legal_context(minimum_score=1.05, **scope)
    assert sorted(r["section_number"] for r in mid["results"]) == ["1", "2"]

    for r in mid["results"]:
        assert r["score"] >= 1.05


# --------------------------------------------------------------------------- #
# Filters
# --------------------------------------------------------------------------- #

def test_document_filter_by_title_is_scoped(corpus):
    result = retrieve_legal_context(
        query=corpus["marker"], document_filter=[corpus["doc_title"]],
        verified_only=False, top_k=10, minimum_score=0.0,
    )
    assert result["results"]
    assert all(r["document_title"] == corpus["doc_title"] for r in result["results"])


def test_document_filter_by_uuid_is_scoped(corpus):
    result = retrieve_legal_context(
        query=corpus["marker"], document_filter=[corpus["doc_id"]],
        verified_only=False, top_k=10, minimum_score=0.0,
    )
    assert result["results"]
    assert all(r["document_id"] == str(corpus["doc_id"]) for r in result["results"])


def test_document_filter_matching_nothing_returns_no_results(corpus):
    result = retrieve_legal_context(
        query=corpus["marker"], document_filter=["no such document title"],
        verified_only=False, top_k=5, minimum_score=0.0,
    )
    assert result["results"] == []
    assert result["total_found"] == 0


def test_unknown_domain_key_returns_an_error(corpus):
    result = retrieve_legal_context(
        query=corpus["marker"], domain_id="definitely_not_a_domain",
        verified_only=False,
    )
    assert result["results"] == []
    assert "error" in result


def test_verified_only_excludes_unverified_chunks(corpus):
    """The seeded chunks are unverified, so verified_only=True yields nothing."""
    unverified = retrieve_legal_context(
        query=corpus["marker"], document_filter=[corpus["doc_title"]],
        verified_only=False, top_k=10, minimum_score=0.0,
    )
    assert unverified["results"]

    verified = retrieve_legal_context(
        query=corpus["marker"], document_filter=[corpus["doc_title"]],
        verified_only=True, top_k=10, minimum_score=0.0,
    )
    assert verified["results"] == []
    assert verified["total_found"] == 0


# --------------------------------------------------------------------------- #
# Query behaviour
# --------------------------------------------------------------------------- #

def test_empty_query_short_circuits_without_touching_the_database():
    for query in ("", None):
        result = retrieve_legal_context(query=query, verified_only=False)
        assert result["results"] == []
        assert result["total_found"] == 0


def test_unknown_query_returns_no_results(corpus):
    result = retrieve_legal_context(
        query=f"zzz_nothing_matches_{uuid4().hex}", verified_only=False,
        top_k=5, minimum_score=0.0,
    )
    assert result["results"] == []
    assert result["total_found"] == 0


def test_whitespace_heavy_query_still_matches(corpus):
    padded = f"  {corpus['marker']}  "
    result = retrieve_legal_context(
        query=padded, document_filter=[corpus["doc_title"]],
        verified_only=False, top_k=5, minimum_score=0.0,
    )
    assert result["results"], "query normalization must trim/collapse whitespace"
    assert result["normalized_query"] == corpus["marker"]


def test_english_term_matches_an_english_heading(corpus):
    """Updated deliberately: matching is now per-term (OR), so an English word
    that appears in the corpus matches it. The seeded fixture has a provision
    titled "<marker> Guardian Duty", which a single-term search must find.

    Previously the whole query "guardian appointment" was matched as one
    substring, which matched nothing - the limitation this phase removed.
    """
    result = retrieve_legal_context(
        query="guardian appointment", document_filter=[corpus["doc_title"]],
        verified_only=False, top_k=5, minimum_score=0.0,
    )
    assert result["tokens"] == ["guardian", "appointment"]
    assert [r["section_number"] for r in result["results"]] == ["1"]


def test_unrelated_english_query_returns_nothing(corpus):
    result = retrieve_legal_context(
        query="quarterly marketing budget",
        document_filter=[corpus["doc_title"]],
        verified_only=False, top_k=5, minimum_score=0.0,
    )
    assert result["results"] == []
    assert result["status"] == "no_match"


def test_partial_term_match_is_ranked_below_a_full_match(corpus):
    """Recall increased, but relevance ordering still holds: a provision that
    matches more of the question ranks above one that matches less."""
    result = retrieve_legal_context(
        query=f"{corpus['marker']} Guardian",
        document_filter=[corpus["doc_title"]],
        verified_only=False, top_k=10, minimum_score=0.0,
    )
    numbers = [r["section_number"] for r in result["results"]]
    assert numbers[0] == "1", "the row matching both terms must rank first"
    assert numbers.index("1") < numbers.index("2")


def test_natural_nepali_sentence_retrieves_matching_provisions(corpus):
    """The headline fix: a full sentence is tokenized, not matched whole."""
    sentence = f"मेरो भाइले मलाई मुद्दा हाल्यो, अब {corpus['nepali_marker']} के गर्नुपर्छ?"
    result = retrieve_legal_context(
        query=sentence,
        document_filter=[corpus["doc_title"]],
        verified_only=False, top_k=10, minimum_score=0.0,
    )

    assert len(result["tokens"]) > 3
    assert result["total_found"] >= 1
    hit = next(r for r in result["results"] if r["section_number"] == "141")
    assert corpus["nepali_marker"] in hit["content"]
    assert 0 < hit["score"] <= 1.4


def test_nepali_query_round_trips(corpus):
    result = retrieve_legal_context(
        query=corpus["nepali_query"], document_filter=[corpus["doc_title"]],
        verified_only=False, top_k=5, minimum_score=0.0,
    )
    assert result["results"]
    hit = result["results"][0]
    assert hit["section_number"] == "141"
    assert corpus["nepali_marker"] in hit["content"]


@pytest.mark.parametrize("search_type", ["keyword", "title", "content"])
def test_search_types_return_relevant_rows(corpus, search_type):
    result = retrieve_legal_context(
        query=corpus["marker"], document_filter=[corpus["doc_title"]],
        search_type=search_type, verified_only=False, top_k=10, minimum_score=0.0,
    )
    assert result["results"], search_type
    assert all(corpus["marker"] in (r["content"] + r["section_title"])
               for r in result["results"])


def test_search_type_title_excludes_content_only_matches(corpus):
    result = retrieve_legal_context(
        query=corpus["marker"], document_filter=[corpus["doc_title"]],
        search_type="title", verified_only=False, top_k=10, minimum_score=0.0,
    )
    numbers = {r["section_number"] for r in result["results"]}
    assert numbers == {"1", "3"}, numbers  # section 2 matches content only


def test_search_type_content_excludes_title_only_matches(corpus):
    result = retrieve_legal_context(
        query=corpus["marker"], document_filter=[corpus["doc_title"]],
        search_type="content", verified_only=False, top_k=10, minimum_score=0.0,
    )
    numbers = {r["section_number"] for r in result["results"]}
    assert numbers == {"1", "2"}, numbers  # section 3 matches title only


# --------------------------------------------------------------------------- #
# Traceability
# --------------------------------------------------------------------------- #

def test_results_expose_database_backed_traceability(corpus):
    result = retrieve_legal_context(
        query=corpus["marker"], document_filter=[corpus["doc_title"]],
        verified_only=False, top_k=1, minimum_score=0.0,
    )
    hit = result["results"][0]

    conn = psycopg.connect(TEST_URL, row_factory=dict_row)
    stored = conn.execute(
        """
        SELECT c.id AS chunk_id, c.content, c.is_verified, c.chunk_index,
               c.language, d.id AS document_id, d.title AS document_title,
               dm.key AS domain_key, p.provision_number, p.title AS section_title,
               s.name AS source_name, s.official_url AS source_url
        FROM knowledge_chunks c
        JOIN legal_documents d ON d.id = c.document_id
        JOIN legal_domains dm ON dm.id = c.domain_id
        JOIN legal_provisions p ON p.id = c.provision_id
        LEFT JOIN sources s ON s.id = c.source_id
        WHERE c.document_id = %s AND p.provision_number = %s
        """,
        (corpus["doc_id"], hit["section_number"]),
    ).fetchone()
    conn.close()

    assert hit["document_id"] == str(stored["document_id"])
    assert hit["document_title"] == stored["document_title"]
    assert hit["section_number"] == stored["provision_number"]
    assert hit["section_title"] == stored["section_title"]
    assert hit["content"] == stored["content"]
    assert hit["domain"] == stored["domain_key"]
    assert hit["source"] == stored["source_name"]
    assert hit["source_url"] == stored["source_url"]
    assert hit["is_verified"] is stored["is_verified"]
    assert hit["chunk_index"] == stored["chunk_index"]


def test_every_result_is_source_traceable_and_never_anonymous(corpus):
    result = retrieve_legal_context(
        query=corpus["marker"], document_filter=[corpus["doc_title"]],
        verified_only=False, top_k=10, minimum_score=0.0,
    )
    assert result["results"]
    for hit in result["results"]:
        assert hit["document_id"]
        assert hit["document_title"]
        assert hit["section_number"]
        assert hit["content"]
        assert hit["domain"]
        assert hit["source"], "anonymous legal text is never returned"
        assert isinstance(hit["is_verified"], bool)
        assert isinstance(hit["score"], float)
