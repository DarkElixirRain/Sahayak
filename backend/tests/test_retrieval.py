"""Unit tests for Phase 4 retrieval: normalization, query building, ranking
constants, and the `POST /api/knowledge/retrieve` API contract.

These tests are deliberately **database-free**: the retrieval service is
mocked, so the suite runs anywhere (no `DATABASE_URL`, no pool). Real
retrieval against PostgreSQL is covered separately by
``tests/integration/test_phase4_retrieval.py``.

History: the original Phase 4 test file patched
``app.api.routes.knowledge.get_connection``, which the service does not use
(it resolves ``get_connection`` from ``app.db.session``), so the "mocked" tests
silently hit the real database and several asserted nothing about the
application at all. Those defects are corrected here.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.knowledge_retrieval import (
    CONTENT_WEIGHT,
    DOMAIN_WEIGHT,
    MAX_SCORE,
    SEARCH_TYPES,
    TITLE_WEIGHT,
    _build_search_clause,
    _normalize_query,
)

client = TestClient(app, raise_server_exceptions=False)

SERVICE = "app.api.routes.knowledge.retrieve_legal_context"

NEPALI_141_QUERY = "देहायका व्यक्तिहरू"


def _ok_result(**overrides):
    """A well-formed service response usable as a mocked return value."""
    payload = {
        "query": NEPALI_141_QUERY,
        "normalized_query": NEPALI_141_QUERY,
        "results": [
            {
                "document_id": "91e32e59-c125-4a28-936d-3101bdf69b1a",
                "document_title": "मुलुकी देवानी संहिता, २०७४",
                "section_number": "141",
                "section_title": "संरक्षक हुन नसक्ने",
                "content": "देहायका व्यक्तिहरू संरक्षक हुन सक्नेछन्।",
                "domain": "family",
                "source": "नेपाल कानून आयोग (Nepal Law Commission)",
                "source_url": "https://lawcommission.gov.np/content/13455/civil-code-2074",
                "score": 1.1,
                "is_verified": False,
                "chunk_index": 1,
            }
        ],
        "total_found": 1,
    }
    payload.update(overrides)
    return payload


# --------------------------------------------------------------------------- #
# Query normalization
# --------------------------------------------------------------------------- #

def test_normalize_collapses_whitespace_and_lowercases():
    assert _normalize_query("  Property   Partition  ") == "property partition"


def test_normalize_nepali_query():
    result = _normalize_query("  संरक्षक   हुन   नसक्ने  ")
    assert result == "संरक्षक हुन नसक्ने"
    assert "  " not in result


def test_normalize_mixed_language_query_preserves_both_scripts():
    result = _normalize_query("जग्गा dispute")
    assert "जग्गा" in result
    assert "dispute" in result


def test_normalize_empty_query_returns_empty():
    assert _normalize_query("") == ""


def test_normalize_whitespace_only_query_returns_empty():
    assert _normalize_query("   \t\n  ") == ""


def test_normalize_is_idempotent():
    for raw in ("मरो पैतृक सम्पत्तिमा अधिकार", "property partition",
                "जग्गा dispute", "a  b"):
        once = _normalize_query(raw)
        assert _normalize_query(once) == once


def test_normalize_case_variants_converge():
    for raw in ("PROPERTY", "Property", "property", "PROPERTY PARTITION"):
        assert _normalize_query(raw) == _normalize_query(raw).lower()


def test_normalize_strips_edges_but_keeps_punctuation():
    assert _normalize_query("  संरक्षक?  ") == "संरक्षक?"


def test_normalize_leaves_uuid_like_strings_usable():
    value = "11111111-1111-1111-1111-111111111111"
    assert _normalize_query(value) == value


# --------------------------------------------------------------------------- #
# Search clause construction
# --------------------------------------------------------------------------- #

def test_keyword_clause_matches_title_and_content():
    clause, params = _build_search_clause("x", "keyword")
    assert "c.title ILIKE" in clause and "c.content ILIKE" in clause
    assert params == ["%x%", "%x%"]


def test_title_clause_matches_only_title():
    clause, params = _build_search_clause("x", "title")
    assert clause == "c.title ILIKE %s"
    assert params == ["%x%"]


def test_content_clause_matches_only_content():
    clause, params = _build_search_clause("x", "content")
    assert clause == "c.content ILIKE %s"
    assert params == ["%x%"]


def test_domain_clause_uses_the_legal_domains_key_column():
    """Regression: the original used `d.key`, but the key lives on
    legal_domains (dm) — `legal_documents` has no `key` column."""
    clause, params = _build_search_clause("family", "domain")
    assert clause == "dm.key ILIKE %s"
    assert params == ["%family%"]


@pytest.mark.parametrize("bad", ["bogus", "", "KEYWORD", "fulltext"])
def test_unknown_search_type_falls_back_to_keyword(bad):
    clause, _ = _build_search_clause("x", bad)
    assert clause == _build_search_clause("x", "keyword")[0]


def test_every_declared_search_type_is_buildable():
    for search_type in SEARCH_TYPES:
        clause, params = _build_search_clause("x", search_type)
        assert "%s" in clause
        assert params


# --------------------------------------------------------------------------- #
# Ranking constants
# --------------------------------------------------------------------------- #

def test_score_weights_match_the_documented_values():
    assert CONTENT_WEIGHT == 1.0
    assert TITLE_WEIGHT == 0.3
    assert DOMAIN_WEIGHT == 0.1
    assert MAX_SCORE == pytest.approx(1.4)


# --------------------------------------------------------------------------- #
# API contract — successful response
# --------------------------------------------------------------------------- #

def test_retrieve_endpoint_returns_service_payload():
    with patch(SERVICE, return_value=_ok_result()) as mocked:
        response = client.post(
            "/api/knowledge/retrieve", json={"query": NEPALI_141_QUERY}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == NEPALI_141_QUERY
    assert body["total_found"] == 1
    assert len(body["results"]) == 1
    mocked.assert_called_once()


def test_retrieve_result_exposes_full_source_traceability():
    with patch(SERVICE, return_value=_ok_result()):
        body = client.post(
            "/api/knowledge/retrieve", json={"query": NEPALI_141_QUERY}
        ).json()

    result = body["results"][0]
    for key in (
        "document_id", "document_title", "section_number", "section_title",
        "content", "domain", "source", "source_url", "score", "is_verified",
        "chunk_index",
    ):
        assert key in result, key

    assert result["document_id"]
    assert result["document_title"]
    assert result["section_number"] == "141"
    assert result["source"]
    assert result["source_url"].startswith("https://")


def test_retrieve_forwards_request_fields_to_the_service():
    with patch(SERVICE, return_value=_ok_result()) as mocked:
        client.post(
            "/api/knowledge/retrieve",
            json={
                "query": NEPALI_141_QUERY,
                "top_k": 7,
                "minimum_score": 0.5,
                "domain_id": "family",
                "document_title": "मुलुकी देवानी संहिता, २०७४",
                "verified_only": False,
                "search_type": "title",
            },
        )

    kwargs = mocked.call_args.kwargs
    assert kwargs["query"] == NEPALI_141_QUERY
    assert kwargs["top_k"] == 7
    assert kwargs["minimum_score"] == 0.5
    assert kwargs["domain_id"] == "family"
    assert kwargs["document_filter"] == ["मुलुकी देवानी संहिता, २०७४"]
    assert kwargs["verified_only"] is False
    assert kwargs["search_type"] == "title"


def test_retrieve_forwards_document_filter_as_none_when_absent():
    with patch(SERVICE, return_value=_ok_result()) as mocked:
        client.post("/api/knowledge/retrieve", json={"query": "x"})
    assert mocked.call_args.kwargs["document_filter"] is None


def test_retrieve_defaults_are_verified_only_true_and_keyword():
    with patch(SERVICE, return_value=_ok_result()) as mocked:
        client.post("/api/knowledge/retrieve", json={"query": "x"})
    kwargs = mocked.call_args.kwargs
    assert kwargs["verified_only"] is True
    assert kwargs["search_type"] == "keyword"
    assert kwargs["top_k"] == 5
    assert kwargs["minimum_score"] == 0.3


def test_retrieve_top_k_is_clamped_to_the_documented_range():
    with patch(SERVICE, return_value=_ok_result()) as mocked:
        client.post("/api/knowledge/retrieve", json={"query": "x", "top_k": 9999})
        assert mocked.call_args.kwargs["top_k"] == 50

    with patch(SERVICE, return_value=_ok_result()) as mocked:
        client.post("/api/knowledge/retrieve", json={"query": "x", "top_k": 0})
        assert mocked.call_args.kwargs["top_k"] == 1


def test_retrieve_minimum_score_is_clamped_to_the_score_range():
    with patch(SERVICE, return_value=_ok_result()) as mocked:
        client.post(
            "/api/knowledge/retrieve", json={"query": "x", "minimum_score": -5}
        )
        assert mocked.call_args.kwargs["minimum_score"] == 0.0

    with patch(SERVICE, return_value=_ok_result()) as mocked:
        client.post(
            "/api/knowledge/retrieve", json={"query": "x", "minimum_score": 99}
        )
        assert mocked.call_args.kwargs["minimum_score"] == pytest.approx(MAX_SCORE)


def test_retrieve_empty_results_are_a_valid_200_response():
    empty = {"query": "x", "normalized_query": "x", "results": [], "total_found": 0}
    with patch(SERVICE, return_value=empty):
        response = client.post("/api/knowledge/retrieve", json={"query": "x"})
    assert response.status_code == 200
    assert response.json()["results"] == []
    assert response.json()["total_found"] == 0


def test_retrieve_unknown_domain_becomes_404():
    error = {
        "query": "x", "normalized_query": "x", "results": [], "total_found": 0,
        "error": "Unknown domain_id: nope",
    }
    with patch(SERVICE, return_value=error):
        response = client.post(
            "/api/knowledge/retrieve", json={"query": "x", "domain_id": "nope"}
        )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


# --------------------------------------------------------------------------- #
# API contract — malformed input (structured 422s)
# --------------------------------------------------------------------------- #

def _assert_validation_error(response):
    assert response.status_code == 422, response.text
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"]


@pytest.mark.parametrize(
    "payload",
    [
        {},                      # missing query
        {"query": None},         # null
        {"query": 123},          # number
        {"query": {"a": 1}},     # object
        {"query": ["a"]},        # array
        {"query": True},         # bool is not a string
        {"query": ""},           # empty
        {"query": "   "},        # whitespace only
    ],
)
def test_missing_or_non_string_query_is_rejected(payload):
    _assert_validation_error(
        client.post("/api/knowledge/retrieve", json=payload)
    )


@pytest.mark.parametrize("bad", ["abc", None, 1.5, [1], {"a": 1}, True])
def test_invalid_top_k_is_rejected(bad):
    _assert_validation_error(
        client.post("/api/knowledge/retrieve", json={"query": "x", "top_k": bad})
    )


@pytest.mark.parametrize("bad", ["abc", None, [1], {"a": 1}, True])
def test_invalid_minimum_score_is_rejected(bad):
    _assert_validation_error(
        client.post(
            "/api/knowledge/retrieve", json={"query": "x", "minimum_score": bad}
        )
    )


@pytest.mark.parametrize("bad", ["bogus", "", "KEYWORD", "fulltext", 5, None])
def test_invalid_search_type_is_rejected(bad):
    _assert_validation_error(
        client.post(
            "/api/knowledge/retrieve", json={"query": "x", "search_type": bad}
        )
    )


@pytest.mark.parametrize("bad", [123, ["family"], {"k": "v"}])
def test_invalid_domain_id_type_is_rejected(bad):
    _assert_validation_error(
        client.post("/api/knowledge/retrieve", json={"query": "x", "domain_id": bad})
    )


@pytest.mark.parametrize("bad", [123, ["t"], {"t": 1}])
def test_invalid_document_title_type_is_rejected(bad):
    _assert_validation_error(
        client.post(
            "/api/knowledge/retrieve", json={"query": "x", "document_title": bad}
        )
    )


@pytest.mark.parametrize("bad", ["yes", "true", 1, 0, None])
def test_invalid_verified_only_is_rejected(bad):
    _assert_validation_error(
        client.post(
            "/api/knowledge/retrieve", json={"query": "x", "verified_only": bad}
        )
    )


def test_non_object_body_is_rejected():
    assert client.post("/api/knowledge/retrieve", json=["a"]).status_code == 422


def test_validation_failures_never_reach_the_service():
    with patch(SERVICE, return_value=_ok_result()) as mocked:
        client.post("/api/knowledge/retrieve", json={})
        client.post("/api/knowledge/retrieve", json={"query": "x", "top_k": "abc"})
        client.post("/api/knowledge/retrieve", json={"query": "x", "search_type": "no"})
    assert mocked.call_count == 0
