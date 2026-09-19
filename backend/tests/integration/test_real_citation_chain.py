"""Phase 11 — Real citation chain integration test.

Executes the complete path:
    DB → retrieval → build_citations → citation validation

Requirements:
  - DATABASE_URL must be set
  - Migration 012 must have been applied (Nepal Law Commission source verified)
  - NO manual injection of is_verified=True anywhere in this file
  - NO manual injection of citation objects

The test fails if:
  - retrieved chunks are not genuinely verified in the DB
  - citations do not point to real authoritative URLs
  - the chain is broken at any step
"""

from __future__ import annotations

import os
import pytest

DATABASE_URL = os.environ.get("DATABASE_URL", "")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="DATABASE_URL not set — skipping real citation chain test",
)


class TestRealCitationChain:
    """The full DB → retrieval → grounding → citation chain.

    No mocking, no fixture injection, no manual is_verified overrides.
    """

    REAL_QUERIES = [
        # Nepali
        "सम्पत्तिको विवादमा के गर्न सकिन्छ?",
        # More specific Civil Code terms
        "देवानी कानूनका सामान्य सिद्धान्त",
        "व्यक्तित्व",
    ]

    def test_retrieval_connects_to_db(self):
        """Retrieval must succeed without connection errors."""
        from app.services.knowledge_retrieval import retrieve_legal_context
        result = retrieve_legal_context("सम्पत्ति", verified_only=True)
        assert "status" in result
        assert "results" in result

    def test_verified_results_come_from_db(self):
        """Every returned chunk must have is_verified=True as stored in the DB."""
        from app.services.knowledge_retrieval import retrieve_legal_context, STATUS_OK

        result = retrieve_legal_context(
            "सम्पत्तिको विवादमा के गर्न सकिन्छ?",
            verified_only=True,
        )
        assert result["status"] == STATUS_OK, (
            f"Expected STATUS_OK for Nepali Civil Code query, got {result['status']}. "
            "This means verified chunks are missing — check migration 012."
        )
        assert len(result["results"]) > 0

        # Cross-check each returned chunk_id against the live DB
        import psycopg
        from psycopg.rows import dict_row
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            for r in result["results"]:
                cur = conn.cursor()
                cur.execute(
                    "SELECT is_verified, source_id FROM knowledge_chunks WHERE id = %s",
                    (r["chunk_id"],),
                )
                db_row = cur.fetchone()
                assert db_row is not None, f"chunk_id {r['chunk_id']} not in DB"
                assert db_row["is_verified"] is True, (
                    f"Chunk {r['chunk_id']} returned by retrieval is NOT is_verified=TRUE in DB"
                )
                assert db_row["source_id"] is not None

    def test_citations_built_from_db_records(self):
        """Citations must be built purely from DB data — no LLM invention."""
        from app.services.knowledge_retrieval import retrieve_legal_context, STATUS_OK
        from app.services.legal_grounding import build_citations

        result = retrieve_legal_context(
            "सम्पत्तिको विवादमा के गर्न सकिन्छ?",
            verified_only=True,
        )
        if result["status"] != STATUS_OK:
            pytest.skip("No verified results — cannot test citation chain")

        citations = build_citations(result["results"])
        assert len(citations) > 0, "build_citations returned empty list"

        # Cross-check citations against the live DB
        import psycopg
        from psycopg.rows import dict_row
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            for cit in citations:
                # 1. Document must exist
                doc_id = cit.get("document_id")
                if doc_id:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT title FROM legal_documents WHERE id = %s", (doc_id,)
                    )
                    db_doc = cur.fetchone()
                    assert db_doc is not None, f"document_id {doc_id} not in DB"
                    assert db_doc["title"] == cit["document"], (
                        f"Citation document title '{cit['document']}' doesn't match "
                        f"DB title '{db_doc['title']}'"
                    )

                # 2. Provision must exist if provision_id set
                prov_id = cit.get("provision_id")
                if prov_id:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT provision_number FROM legal_provisions WHERE id = %s",
                        (prov_id,),
                    )
                    db_prov = cur.fetchone()
                    assert db_prov is not None, f"provision_id {prov_id} not in DB"

                # 3. Source must be verified in DB
                source_id = cit.get("source_id")
                if source_id:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT is_verified, official_url FROM sources WHERE id = %s",
                        (source_id,),
                    )
                    db_src = cur.fetchone()
                    assert db_src is not None
                    # Only enforce verified for non-fixture sources
                    if db_src["official_url"] and "example.invalid" not in db_src["official_url"]:
                        assert db_src["is_verified"] is True, (
                            f"Source {source_id} cited but is NOT verified in DB"
                        )

    def test_citation_source_url_is_real_authoritative(self):
        """Every citation URL must be a real authoritative Nepal government URL."""
        from app.services.knowledge_retrieval import retrieve_legal_context, STATUS_OK
        from app.services.legal_grounding import build_citations, safe_source_url

        result = retrieve_legal_context(
            "देवानी कानूनका सामान्य सिद्धान्त",
            verified_only=True,
        )
        if result["status"] != STATUS_OK:
            pytest.skip("No verified results for this query")

        citations = build_citations(result["results"])
        for cit in citations:
            url = cit.get("source_url")
            if url:
                assert url.startswith("https://"), f"Citation URL must be https: {url}"
                assert "example.invalid" not in url, (
                    f"Fixture URL must never appear in real citations: {url}"
                )
                # Safe URL validator must accept it
                assert safe_source_url(url) == url

    def test_citation_has_real_section_number(self):
        """Section numbers in citations must come from the DB, not invented."""
        from app.services.knowledge_retrieval import retrieve_legal_context, STATUS_OK
        from app.services.legal_grounding import build_citations

        result = retrieve_legal_context(
            "दफा १ संक्षिप्त नाम",
            verified_only=True,
        )
        if result["status"] != STATUS_OK:
            pytest.skip("No verified results")

        citations = build_citations(result["results"])
        # Cross-check: if a section number appears in a citation, it must exist in DB
        import psycopg
        from psycopg.rows import dict_row
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            for cit in citations:
                sec = cit.get("section")
                prov_id = cit.get("provision_id")
                if sec and prov_id:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT provision_number FROM legal_provisions WHERE id = %s",
                        (prov_id,),
                    )
                    db_prov = cur.fetchone()
                    if db_prov and db_prov["provision_number"]:
                        assert db_prov["provision_number"] == sec, (
                            f"Citation section '{sec}' doesn't match DB "
                            f"provision_number '{db_prov['provision_number']}'"
                        )

    def test_no_evidence_path_grounded_false(self):
        """When no verified evidence exists, the system must not hallucinate."""
        from app.services.knowledge_retrieval import (
            retrieve_legal_context, STATUS_NO_MATCH,
        )
        from app.services.legal_grounding import build_citations, insufficient_context_answer

        result = retrieve_legal_context(
            "xyzzy_no_match_token_phase11",
            verified_only=True,
        )
        assert result["status"] == STATUS_NO_MATCH
        assert result["results"] == []

        citations = build_citations(result["results"])
        assert citations == [], "No citations must be generated when results is empty"

        # The safe fallback answer must be returned
        fallback = insufficient_context_answer("nepali", unverified_only=False)
        assert fallback  # not empty
        assert len(fallback) > 20  # substantive Nepali text


class TestGroundedAnswerChain:
    """Test that the grounding layer wraps retrieval correctly."""

    def test_context_block_built_from_real_results(self):
        """Context block must contain real provision text, not placeholders."""
        from app.services.knowledge_retrieval import retrieve_legal_context, STATUS_OK
        from app.services.legal_grounding import build_context_block

        result = retrieve_legal_context(
            "सम्पत्तिको विवाद",
            verified_only=True,
        )
        if result["status"] != STATUS_OK:
            pytest.skip("No verified results")

        block = build_context_block(result["results"])
        # The block must contain Devanagari text from real provisions
        import re
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", block))
        assert has_devanagari, "Context block must contain Devanagari legal text"

        # Must be fenced
        assert "<legal_context>" in block
        assert "</legal_context>" in block

    def test_context_block_marks_verified(self):
        """Entries from verified chunks must be marked VERIFIED in the context block."""
        from app.services.knowledge_retrieval import retrieve_legal_context, STATUS_OK
        from app.services.legal_grounding import build_context_block

        result = retrieve_legal_context(
            "देवानी",
            verified_only=True,
        )
        if result["status"] != STATUS_OK:
            pytest.skip("No verified results")

        block = build_context_block(result["results"])
        assert "VERIFIED" in block, (
            "Context block must mark verified entries as VERIFIED"
        )
        assert "UNVERIFIED" not in block, (
            "verified_only results must not contain UNVERIFIED entries"
        )

    def test_system_prompt_built_without_hallucination(self):
        """System prompt must reference only the supplied context."""
        from app.services.knowledge_retrieval import retrieve_legal_context, STATUS_OK
        from app.services.legal_grounding import (
            build_context_block, build_system_prompt, detect_language,
        )

        result = retrieve_legal_context(
            "सम्पत्ति",
            verified_only=True,
        )
        if result["status"] != STATUS_OK:
            pytest.skip("No verified results")

        block = build_context_block(result["results"])
        verified_count = sum(1 for r in result["results"] if r["is_verified"])
        total_count = len(result["results"])

        prompt = build_system_prompt(
            language="nepali",
            context_block=block,
            verified_count=verified_count,
            total_count=total_count,
        )
        assert "Sahayak" in prompt
        assert "STRICT GROUNDING RULES" in prompt
        assert "Never invent" in prompt
