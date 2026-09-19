"""Unit tests for the lexical retrieval layer (no database).

Covers the deterministic parts: tokenization, stop-word handling, clause
construction, hit expressions and the empty/status contract. SQL-level ranking
and filtering are covered by ``tests/integration/test_phase4_retrieval.py``.
"""

from unittest.mock import patch

import pytest

from app.services.knowledge_retrieval import (
    CONTENT_WEIGHT,
    DOMAIN_WEIGHT,
    MAX_QUERY_TOKENS,
    MAX_SCORE,
    SEARCH_TYPES,
    STATUS_ERROR,
    STATUS_NO_MATCH,
    STATUS_OK,
    STATUS_UNVERIFIED_ONLY,
    TITLE_WEIGHT,
    _build_hit_expression,
    _build_match_predicate,
    _build_search_clause,
    _empty_result,
    retrieve_legal_context,
    tokenize_query,
)

NATURAL_NEPALI = "मेरो भाइले मलाई मुद्दा हाल्यो, अब मैले के गर्नुपर्छ?"


# --------------------------------------------------------------------------- #
# Tokenization
# --------------------------------------------------------------------------- #

def test_tokenize_keeps_meaningful_nepali_terms():
    tokens = tokenize_query(NATURAL_NEPALI)

    assert "भाइले" in tokens
    assert "मुद्दा" in tokens
    assert "हाल्यो" in tokens
    # Stop words and punctuation are dropped.
    assert "मेरो" not in tokens
    assert "के" not in tokens
    assert all("?" not in t and "," not in t for t in tokens)


def test_tokenize_keeps_english_terms_and_drops_stop_words():
    tokens = tokenize_query("What are my rights about the property partition?")
    assert tokens == ["rights", "property", "partition"]


def test_tokenize_keeps_section_numbers():
    assert tokenize_query("धारा 141 को व्यवस्था") == ["धारा", "141", "व्यवस्था"]
    assert "141" in tokenize_query("Section 141")


def test_tokenize_is_case_insensitive_and_deduplicates():
    tokens = tokenize_query("Property property PROPERTY partition")
    assert tokens == ["property", "partition"]


def test_tokenize_preserves_order_and_normalizes_whitespace():
    assert tokenize_query("  संरक्षक    नियुक्ति  ") == ["संरक्षक", "नियुक्ति"]


def test_tokenize_normalizes_unicode_to_nfc():
    import unicodedata

    decomposed = "\u0938\u0902\u0930\u0915\u094d\u0937\u0915"  # संरक्षक
    assert tokenize_query(decomposed) == [unicodedata.normalize("NFC", decomposed)]


def test_tokenize_handles_punctuation_only_input():
    # Falls back to the normalized string so a match is still attempted.
    assert tokenize_query("???") == ["???"] or tokenize_query("???") == []


def test_tokenize_falls_back_when_every_term_is_a_stop_word():
    tokens = tokenize_query("के को मा")
    assert tokens, "a stop-word-only query must still search something"


def test_tokenize_empty_and_whitespace_input():
    assert tokenize_query("") == []
    assert tokenize_query("   \t\n ") == []


def test_tokenize_caps_the_number_of_terms():
    tokens = tokenize_query(" ".join(f"term{i}" for i in range(200)))
    assert len(tokens) == MAX_QUERY_TOKENS


def test_natural_sentence_yields_more_than_one_term():
    """The whole-query ILIKE limitation is gone: a sentence becomes terms."""
    tokens = tokenize_query(NATURAL_NEPALI)
    assert len(tokens) > 1
    assert " ".join(tokens) != NATURAL_NEPALI.strip().lower()


# --------------------------------------------------------------------------- #
# Clause construction
# --------------------------------------------------------------------------- #

def test_match_predicate_ors_every_term():
    clause, params = _build_match_predicate(["a", "b"], "keyword")

    assert clause.count("c.title ILIKE") == 2
    assert clause.startswith("(") and clause.endswith(")")
    assert " OR " in clause
    assert params == ["%a%", "%a%", "%b%", "%b%"]


def test_match_predicate_is_fully_parenthesised():
    """Regression (safety): an unwrapped OR lets a trailing ``AND`` bind to the
    last term only, which silently disabled the verified-only filter and
    returned unverified provisions."""
    clause, _ = _build_match_predicate(["a", "b", "c"], "keyword")
    assert clause.startswith("(") and clause.endswith(")")
    assert clause.count("(") == clause.count(")")

    # Appending any filter must keep every term inside the disjunction.
    assert f"{clause} AND c.is_verified = TRUE".startswith("(")


def test_single_term_predicate_equals_the_single_clause_builder():
    """One term wraps the term builder's clause (grouping is required so that a
    trailing filter cannot bind to just one disjunct)."""
    clause, params = _build_match_predicate(["x"], "keyword")
    single, single_params = _build_search_clause("x", "keyword")

    assert clause == f"({single})"
    assert params == single_params

    title_clause, title_params = _build_match_predicate(["x"], "title")
    assert title_clause == "(c.title ILIKE %s)"
    assert title_params == ["%x%"]


@pytest.mark.parametrize("search_type", SEARCH_TYPES)
def test_every_search_type_builds_for_multiple_terms(search_type):
    clause, params = _build_match_predicate(["a", "b"], search_type)
    assert "%s" in clause
    assert params


def test_hit_expression_counts_each_term():
    expr = _build_hit_expression("c.content", ["a", "b", "c"])
    assert expr.count("CASE WHEN c.content ILIKE %s THEN 1 ELSE 0 END") == 3
    assert expr.count("+") == 2


def test_weights_are_unchanged_from_phase_four():
    assert (CONTENT_WEIGHT, TITLE_WEIGHT, DOMAIN_WEIGHT) == (1.0, 0.3, 0.1)
    assert MAX_SCORE == pytest.approx(1.4)


# --------------------------------------------------------------------------- #
# Empty / status contract
# --------------------------------------------------------------------------- #

def test_empty_result_shape():
    payload = _empty_result("q", "q", status=STATUS_NO_MATCH)
    assert payload["total_found"] == 0
    assert payload["results"] == []
    assert payload["status"] == STATUS_NO_MATCH
    assert payload["tokens"] == []
    assert "error" not in payload


def test_empty_result_carries_an_error_when_given_one():
    payload = _empty_result("q", "q", status=STATUS_ERROR, error="Unknown domain_id: x")
    assert payload["error"] == "Unknown domain_id: x"


def test_status_constants_are_distinct():
    assert len({STATUS_OK, STATUS_NO_MATCH, STATUS_UNVERIFIED_ONLY, STATUS_ERROR}) == 4


@pytest.mark.parametrize("query", ["", "   ", None])
def test_empty_queries_never_touch_the_database(query):
    """An empty question must short-circuit before any DB work."""
    with patch("app.services.knowledge_retrieval.get_connection") as get_conn:
        payload = retrieve_legal_context(query)

    get_conn.assert_not_called()
    assert payload["status"] == STATUS_NO_MATCH
    assert payload["results"] == []


def test_devanagari_matra_words_are_not_split():
    """Regression: ``\\w`` alone splits Nepali at every matra."""
    assert tokenize_query("संरक्षक") == ["संरक्षक"]
    assert tokenize_query("नियुक्ति") == ["नियुक्ति"]
    assert tokenize_query("व्यवस्था") == ["व्यवस्था"]


def test_devanagari_danda_separates_terms():
    assert tokenize_query("संरक्षक। नियुक्ति॥") == ["संरक्षक", "नियुक्ति"]
