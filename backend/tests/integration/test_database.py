"""Database integration tests.

These tests run ONLY when ``TEST_DATABASE_URL`` is configured. They never touch
the normal ``DATABASE_URL`` and never destroy real data: every write happens in
a transaction that is rolled back afterwards. If ``TEST_DATABASE_URL`` is not
set, the whole module skips.

Run with:
    TEST_DATABASE_URL="postgresql://..." python -m pytest tests/integration/
"""

import os
from datetime import datetime, timezone

import psycopg
import pytest

from app.db.migrate import run_migrations
from app.repositories.court_cases import CourtCaseRepository
from app.repositories.government_resources import GovernmentResourceRepository
from app.repositories.knowledge_chunks import KnowledgeChunkRepository
from app.repositories.legal_documents import LegalDocumentRepository
from app.repositories.legal_domains import LegalDomainRepository
from app.repositories.legal_provisions import LegalProvisionRepository
from app.repositories.risk_rules import RiskRuleRepository
from app.repositories.sources import SourceRepository
from app.services.csv_importer import CsvRow, import_rows

TEST_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_URL,
    reason="TEST_DATABASE_URL not configured",
)

EXPECTED_TABLES = {
    "legal_domains", "legal_documents", "legal_provisions", "knowledge_chunks",
    "sources", "government_resources", "court_cases", "risk_rules",
    "conversation_sessions", "conversation_messages",
}


@pytest.fixture(scope="module")
def conn():
    conn = psycopg.connect(TEST_URL)
    run_migrations(TEST_URL)
    yield conn
    conn.close()


@pytest.fixture
def tx(conn):
    conn.execute("SAVEPOINT test_savepoint")
    yield conn
    conn.execute("ROLLBACK TO SAVEPOINT test_savepoint")


def test_migrations_run_and_tables_exist(conn):
    names = {
        r[0] for r in conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        ).fetchall()
    }
    assert EXPECTED_TABLES <= names


def test_timestamps_default_populated(tx):
    repo = LegalDomainRepository(tx)
    domain = repo.create(key=f"ts_{datetime.now().timestamp()}", name="Timestamp Test")
    assert domain["created_at"] is not None
    assert domain["updated_at"] is not None


def test_domain_upsert_is_idempotent(tx):
    repo = LegalDomainRepository(tx)
    repo.upsert("test_dom", "Test Domain", "first")
    row = repo.get_by_key("test_dom")
    repo.upsert("test_dom", "Test Domain", "updated description")
    updated = repo.get_by_key("test_dom")
    assert updated["description"] == "updated description"
    assert row["id"] == updated["id"]


def test_document_provision_chunk_chain(tx):
    d = LegalDomainRepository(tx).create(key="repro_chain", name="Repro Chain")
    doc, created_doc = LegalDocumentRepository(tx).get_or_create(
        d["id"], "Repro Document", "act"
    )
    assert created_doc is True
    provision, created_prov = LegalProvisionRepository(tx).get_or_create(
        doc["id"], "Section text here that is sufficiently long.", "1", "Section One"
    )
    assert created_prov is True
    chunk = KnowledgeChunkRepository(tx).create(
        document_id=doc["id"],
        provision_id=provision["id"],
        domain_id=d["id"],
        content="Retrieval-ready chunk text that is long enough.",
        is_verified=True,
        verified_at=datetime.now(timezone.utc),
        chunk_index=1,
    )
    assert chunk["id"]
    found = KnowledgeChunkRepository(tx).get_by_id(chunk["id"])
    assert found["is_verified"] is True


def test_verified_and_domain_filters(tx):
    d = LegalDomainRepository(tx).create(key="filters_dom", name="Filters")
    doc = LegalDocumentRepository(tx).create(d["id"], "Filters Doc", "act")
    chunks = KnowledgeChunkRepository(tx)
    v = chunks.create(document_id=doc["id"], domain_id=d["id"],
                      content="This is a verified chunk with enough text.", is_verified=True,
                      chunk_index=1)
    u = chunks.create(document_id=doc["id"], domain_id=d["id"],
                      content="This is an unverified chunk with enough text.", is_verified=False,
                      chunk_index=2)
    assert {c["id"] for c in chunks.find_by_domain(d["id"])} == {v["id"]}
    assert {c["id"] for c in chunks.find_verified()} >= {v["id"]}
    assert u["id"] not in {c["id"] for c in chunks.find_by_domain(d["id"])}


def test_source_get_or_create_is_idempotent(tx):
    repo = SourceRepository(tx)
    s1, created1 = repo.get_or_create("Nepal Law Commission", "law_commission",
                                      "https://example.invalid/nlc")
    s2, created2 = repo.get_or_create("Nepal Law Commission", "law_commission",
                                      "https://example.invalid/nlc")
    assert created1 is True and created2 is False
    assert s1["id"] == s2["id"]


def test_import_rows_is_idempotent(tx):
    d = LegalDomainRepository(tx).upsert("consumer", "Consumer")
    doc, _ = LegalDocumentRepository(tx).get_or_create(
        d["id"], "Import Doc", "act", language="nepali"
    )
    rows = [
        CsvRow(
            row_number=i,
            domain="consumer",
            document_title="Import Doc",
            document_type="act",
            provision_number=str(i),
            provision_title=f"Provision {i}",
            content=f"Importable content row {i} with sufficient length.",
            language="nepali",
            source_name="Import Source",
            source_type="official_document",
            source_url="https://example.invalid/import-doc",
            verified=False,
        )
        for i in (1, 2)
    ]
    first = import_rows(tx, rows)
    second = import_rows(tx, rows)
    assert first.inserted == 2
    assert second.inserted == 0
    assert second.skipped == 2
    total = KnowledgeChunkRepository(tx).find_by_document(doc["id"])
    assert len(total) == 2
    assert first.verified == 0
    assert first.unverified == 2


def test_import_preserves_verification(tx):
    d = LegalDomainRepository(tx).upsert("cyber", "Cyber")
    doc, _ = LegalDocumentRepository(tx).get_or_create(d["id"], "Verified Doc", "act")
    rows = [CsvRow(
        row_number=1,
        domain="cyber",
        document_title="Verified Doc",
        document_type="act",
        provision_number=None,
        provision_title=None,
        content="A verified import row with plenty of content to pass validation.",
        language="english",
        source_name="Verified Source",
        source_type="government",
        source_url="https://example.invalid/verified-doc",
        verified=True,
    )]
    report = import_rows(tx, rows)
    assert report.verified == 1
    chunks = KnowledgeChunkRepository(tx).find_by_document(doc["id"])
    assert len(chunks) == 1
    assert chunks[0]["is_verified"] is True


def test_govt_resource_and_court_case_repos(tx):
    d = LegalDomainRepository(tx).create(key="gov_repro", name="Govt Repro")
    source, _ = SourceRepository(tx).get_or_create(
        "Sample Ministry", "ministry", "https://example.invalid/ministry"
    )
    gov = GovernmentResourceRepository(tx).create(
        title="File a complaint",
        domain_id=d["id"],
        source_id=source["id"],
        required_documents=[{"name": "ID"}],
        contact_information={"phone": "100"},
        is_verified=True,
        verified_at=datetime.now(timezone.utc),
    )
    case = CourtCaseRepository(tx).create(
        court_name="Supreme Court",
        domain_id=d["id"],
        source_id=source["id"],
        is_verified=True,
    )
    assert GovernmentResourceRepository(tx).find_by_domain(d["id"]) == [gov]
    assert [c["id"] for c in CourtCaseRepository(tx).find_by_domain(d["id"])] == [case["id"]]


def test_risk_rule_repo(tx):
    repo = RiskRuleRepository(tx)
    rule = repo.create(
        key="otp_scam_test", label="OTP Scam", patterns=["otp", "verification code"],
        severity="high",
    )
    active = repo.find_active()
    assert any(r["id"] == rule["id"] for r in active)
    assert repo.get_by_key("otp_scam_test")["severity"] == "high"


def test_conversation_tables_store_only_benign_data(tx):
    session_id = "00000000-0000-0000-0000-0000000000aa"
    tx.execute(
        """
        INSERT INTO conversation_sessions (id, session_id, status, language)
        VALUES (%s, %s, 'active', 'nepali')
        """,
        ("00000000-0000-0000-0000-0000000000bb", session_id),
    )
    tx.execute(
        """
        INSERT INTO conversation_messages (id, session_id, role, input_mode, content)
        VALUES (%s, %s, 'user', 'text', 'Mero chora le malai mudda halyo')
        """,
        ("00000000-0000-0000-0000-0000000000cc", "00000000-0000-0000-0000-0000000000bb"),
    )
    count = tx.execute(
        "SELECT count(*) FROM conversation_messages WHERE session_id = %s",
        ("00000000-0000-0000-0000-0000000000bb",),
    ).fetchone()[0]
    assert count == 1