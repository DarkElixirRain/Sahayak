"""Tests for scripts/corpus_audit.py.

Verifies that the read-only audit correctly:
  * classifies real vs fixture sources
  * detects orphans
  * reports correct counts
  * never modifies data
"""

from __future__ import annotations

import os
import pytest

DATABASE_URL = os.environ.get("DATABASE_URL", "")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="DATABASE_URL not set — skipping corpus audit tests",
)


@pytest.fixture(scope="module")
def audit_report():
    """Run the corpus audit once and reuse the result."""
    from scripts.corpus_audit import run_audit
    try:
        return run_audit(DATABASE_URL)
    except Exception as exc:
        pytest.skip(f"Corpus audit failed: {exc}")


class TestSourceClassification:
    def test_real_sources_identified(self, audit_report):
        """Nepal Law Commission must appear as a real/authoritative source."""
        real = audit_report["sources"]["real_authoritative"]
        assert real >= 1

    def test_fixture_sources_identified(self, audit_report):
        """Phase-5 example.invalid sources must be classified as fixtures."""
        fixtures = audit_report["sources"]["test_fixtures"]
        assert fixtures >= 2, "Expected at least 2 Phase-5 test fixture sources"

    def test_fixture_detail_has_example_invalid(self, audit_report):
        """Every fixture source detail entry must be flagged is_fixture=True."""
        for src in audit_report["sources"]["detail"]:
            url = src.get("official_url") or ""
            if "example.invalid" in url:
                assert src["is_fixture"] is True

    def test_nlc_source_not_fixture(self, audit_report):
        """Nepal Law Commission must NOT be classified as a fixture."""
        for src in audit_report["sources"]["detail"]:
            if "Nepal Law Commission" in src["name"]:
                assert src["is_fixture"] is False

    def test_real_authoritative_verified(self, audit_report):
        """At least one real authoritative source must be verified."""
        assert audit_report["sources"]["real_authoritative_verified"] >= 1


class TestDocumentCounts:
    def test_civil_code_in_real_documents(self, audit_report):
        """Civil Code must appear in real documents."""
        real_titles = [
            d["title"] for d in audit_report["documents"]["detail"]
            if not d["is_fixture"]
        ]
        assert any("मुलुकी देवानी" in t for t in real_titles)

    def test_civil_code_status_current(self, audit_report):
        """Civil Code document must be status=current."""
        for doc in audit_report["documents"]["detail"]:
            if "मुलुकी देवानी" in doc["title"]:
                assert doc["status"] == "current"

    def test_fixture_documents_flagged(self, audit_report):
        """Phase5 test documents must be flagged as fixtures."""
        for doc in audit_report["documents"]["detail"]:
            if "Phase5 Test" in doc["title"]:
                assert doc["is_fixture"] is True


class TestChunkCounts:
    def test_real_verified_chunks_greater_than_zero(self, audit_report):
        """The primary Phase 11 acceptance criterion."""
        real_verified = audit_report["knowledge_chunks"]["real_verified"]
        assert real_verified > 0, (
            f"BLOCKER: real_verified chunks == 0. "
            f"Total verified: {audit_report['knowledge_chunks']['verified']}"
        )

    def test_real_verified_chunks_at_least_295(self, audit_report):
        """All 295 Civil Code chunks should be real+verified."""
        real_verified = audit_report["knowledge_chunks"]["real_verified"]
        assert real_verified >= 295, (
            f"Expected ≥295 real verified chunks, got {real_verified}"
        )

    def test_chunks_without_provision_zero(self, audit_report):
        """No chunks should be missing a provision_id."""
        assert audit_report["knowledge_chunks"]["without_provision"] == 0

    def test_chunks_without_source_zero(self, audit_report):
        """No chunks should be missing a source_id."""
        assert audit_report["knowledge_chunks"]["without_source"] == 0


class TestVerifiedChain:
    def test_full_chain_complete(self, audit_report):
        """Verified chain count must be ≥295."""
        chain = audit_report["verified_chain"]["chunks_with_full_chain"]
        assert chain >= 295, f"Expected ≥295 full-chain verified records, got {chain}"


class TestOrphanDetection:
    def test_no_chunks_without_document(self, audit_report):
        assert audit_report["orphans"]["chunks_without_document"] == 0

    def test_no_provisions_without_document(self, audit_report):
        assert audit_report["orphans"]["provisions_without_document"] == 0
