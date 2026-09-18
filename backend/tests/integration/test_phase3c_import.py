"""Phase 3C regression tests (run against ``TEST_DATABASE_URL`` only).

These tests exercise the *real* import path (``import_rows`` /
``import_csv_file``) against a live PostgreSQL database and cover the Phase 3C
correctness contract:

* domain reuse (existing metadata never overwritten) and domain creation
* provision text refresh — stale pre-Phase-3B text is corrected in place
* chunk text refresh — stale chunk content is corrected in place
* idempotency — a second identical import is a genuine no-op
* Section 141 keeps the authorised ``व्यक्ति`` correction, never ``mव्यति``
* transaction rollback — a mid-import failure leaves no partial writes
* no destructive operations — unrelated legal data survives an import
* the full 721-row validated dataset round-trips byte-for-byte
* the import stays set-based (no per-row round trips) so it is practical
  against remote Neon

These tests never touch the real ``DATABASE_URL``. If ``TEST_DATABASE_URL`` is
not set the whole module skips.

Run with:
    TEST_DATABASE_URL="postgresql://..." python -m pytest tests/integration/
"""

import csv
import os
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest

from app.db.migrate import run_migrations
from app.db.seed_data import SEED_DOMAINS
from app.repositories.knowledge_chunks import KnowledgeChunkRepository
from app.repositories.legal_documents import LegalDocumentRepository
from app.repositories.legal_domains import LegalDomainRepository
from app.repositories.legal_provisions import LegalProvisionRepository
from app.services.csv_importer import CsvRow, import_rows

TEST_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_URL,
    reason="TEST_DATABASE_URL not configured",
)

IMPORTER_READY = (
    Path(__file__).parents[2] / "data" / "legal"
    / "muluki_dewani_samhita_2074_importer_ready.csv"
)

# A set-based import of the 721-row dataset must stay far below this; the old
# per-row implementation needed ~6,500 round trips.
MAX_DB_OPERATIONS = 20

STALE_SECTION_TEXT = "पुरानो कानूनी पाठ — stale pre-3B legal text that must be refreshed."
FRESH_SECTION_TEXT = "सुधारिएको कानूनी पाठ — corrected validated legal text from the CSV."


@pytest.fixture(scope="module")
def conn():
    connection = psycopg.connect(TEST_URL)
    run_migrations(TEST_URL)
    yield connection
    connection.close()


@pytest.fixture
def tx(conn):
    conn.execute("SAVEPOINT test_savepoint")
    yield conn
    conn.execute("ROLLBACK TO SAVEPOINT test_savepoint")


def _row(n, *, domain, title, provision, content, **kw):
    return CsvRow(
        row_number=n,
        domain=domain,
        document_title=title,
        document_type=kw.get("document_type", "act"),
        provision_number=provision,
        provision_title=kw.get("provision_title", f"दफा {provision}"),
        content=content,
        language=kw.get("language", "nepali"),
        source_name=kw.get("source_name", "Phase 3C Test Source"),
        source_type=kw.get("source_type", "law_commission"),
        source_url=kw.get("source_url", "https://example.invalid/phase3c-test"),
        verified=kw.get("verified", False),
    )


def _unique_key(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


def _seed_domains(conn) -> None:
    """Mirror the real deployment: the taxonomy exists before the import."""
    repo = LegalDomainRepository(conn)
    for seed in SEED_DOMAINS:
        repo.upsert(seed["key"], seed["name"], seed["description"])


# --------------------------------------------------------------------------- #
# 1. Domain reuse
# --------------------------------------------------------------------------- #

def test_existing_domain_is_reused_and_metadata_preserved(tx):
    repo = LegalDomainRepository(tx)
    key = _unique_key("p3c_reuse")
    original = repo.create(
        key=key, name="Original Name", description="Original description"
    )

    report = import_rows(
        tx,
        [_row(1, domain=key, title="Reuse Doc", provision="1", content=FRESH_SECTION_TEXT)],
    )

    assert report.domains_reused == 1
    assert report.domains_created == 0
    after = repo.get_by_key(key)
    assert after["id"] == original["id"]
    assert after["name"] == "Original Name"
    # A CSV without domain metadata must never null out an existing description.
    assert after["description"] == "Original description"


# --------------------------------------------------------------------------- #
# 2. Domain creation
# --------------------------------------------------------------------------- #

def test_missing_domain_is_created(tx):
    repo = LegalDomainRepository(tx)
    key = _unique_key("p3c_create")
    assert repo.get_by_key(key) is None

    report = import_rows(
        tx,
        [_row(1, domain=key, title="Create Doc", provision="1", content=FRESH_SECTION_TEXT)],
    )

    assert report.domains_created == 1
    assert report.domains_reused == 0
    created = repo.get_by_key(key)
    assert created is not None
    assert created["key"] == key
    assert created["is_active"] is True


# --------------------------------------------------------------------------- #
# 3. Provision text refresh
# --------------------------------------------------------------------------- #

def test_stale_provision_text_is_refreshed_in_place(tx):
    domain = LegalDomainRepository(tx).create(key=_unique_key("p3c_prov"), name="Prov")
    document = LegalDocumentRepository(tx).create(domain["id"], "Prov Doc", "act")
    provisions = LegalProvisionRepository(tx)
    stale = provisions.create(
        document_id=document["id"], text=STALE_SECTION_TEXT,
        provision_number="141", title="दफा १४१",
    )

    rows = [_row(
        1, domain=domain["key"], title="Prov Doc", provision="141",
        provision_title="दफा १४१", content=FRESH_SECTION_TEXT,
    )]
    report = import_rows(tx, rows)

    assert report.provisions_updated == 1
    assert report.provisions_created == 0
    refreshed = provisions.get_by_id(stale["id"])
    assert refreshed["id"] == stale["id"]  # id preserved, chunks keep their link
    assert refreshed["text"] == FRESH_SECTION_TEXT
    assert refreshed["text"] != STALE_SECTION_TEXT


# --------------------------------------------------------------------------- #
# 4. Chunk text refresh
# --------------------------------------------------------------------------- #

def test_stale_chunk_text_is_refreshed_in_place(tx):
    domain = LegalDomainRepository(tx).create(key=_unique_key("p3c_chunk"), name="Chunk")
    document = LegalDocumentRepository(tx).create(domain["id"], "Chunk Doc", "act")
    provision = LegalProvisionRepository(tx).create(
        document_id=document["id"], text=STALE_SECTION_TEXT,
        provision_number="1", title="दफा १",
    )
    chunks = KnowledgeChunkRepository(tx)
    stale = chunks.create(
        document_id=document["id"], provision_id=provision["id"],
        domain_id=domain["id"], title="दफा १", content=STALE_SECTION_TEXT,
        language="nepali", chunk_index=1,
    )

    rows = [_row(
        1, domain=domain["key"], title="Chunk Doc", provision="1",
        provision_title="दफा १", content=FRESH_SECTION_TEXT,
    )]
    report = import_rows(tx, rows)

    assert report.chunks_updated == 1
    assert report.chunks_created == 0
    refreshed = chunks.get_by_id(stale["id"])
    assert refreshed["id"] == stale["id"]
    assert refreshed["content"] == FRESH_SECTION_TEXT
    assert refreshed["provision_id"] == provision["id"]  # provenance intact


# --------------------------------------------------------------------------- #
# 5. Idempotency
# --------------------------------------------------------------------------- #

def test_second_import_is_a_no_op(tx):
    key = _unique_key("p3c_idem")
    rows = [
        _row(1, domain=key, title="Idem Doc", provision="1", content=FRESH_SECTION_TEXT),
        _row(2, domain=key, title="Idem Doc", provision="2", content=FRESH_SECTION_TEXT + " २"),
    ]

    first = import_rows(tx, rows)
    assert first.chunks_created == 2
    assert first.inserted == 2

    second = import_rows(tx, rows)
    assert second.chunks_created == 0
    assert second.chunks_updated == 0
    assert second.provisions_created == 0
    assert second.provisions_updated == 0
    assert second.domains_created == 0
    assert second.documents_created == 0
    assert second.sources_created == 0
    assert second.inserted == 0
    assert second.updated == 0
    assert second.skipped == 2

    domain = LegalDomainRepository(tx).get_by_key(key)
    document = LegalDocumentRepository(tx).find_by_title_type(
        domain["id"], "Idem Doc", "act"
    )
    assert len(LegalProvisionRepository(tx).list_by_document(document["id"])) == 2
    assert len(KnowledgeChunkRepository(tx).find_by_document(document["id"])) == 2


# --------------------------------------------------------------------------- #
# 6. Section 141
# --------------------------------------------------------------------------- #

def test_section_141_contains_vyakti(tx):
    raw_rows = _csv_rows()
    rows = [_to_csv_row(raw, n) for n, raw in enumerate(raw_rows, start=1)]
    import_rows(tx, rows)

    section = [r for r in raw_rows if r["provision_number"] == "141"]
    assert section, "Section 141 must exist in the validated dataset"
    for raw in section:
        domain = LegalDomainRepository(tx).get_by_key(raw["domain"])
        document = LegalDocumentRepository(tx).find_by_title_type(
            domain["id"], raw["document_title"], raw["document_type"]
        )
        provision = LegalProvisionRepository(tx).find_by_number(document["id"], "141")
        assert "व्यक्ति" in provision["text"]
        assert "mव्यति" not in provision["text"]


# --------------------------------------------------------------------------- #
# 7. Transaction rollback
# --------------------------------------------------------------------------- #

def test_failure_rolls_back_without_partial_writes(monkeypatch):
    """A failure after provisions were written must leave the database untouched.

    Uses an independent connection (not the rollback-only ``tx`` savepoint) so
    the assertion is about the importer's own transactional behaviour.
    """
    key = _unique_key("p3c_rollback")
    marker = f"ROLLBACK-MARKER-{uuid4().hex}"
    content = f"{marker} — content that must never survive a failed import."
    rows = [_row(1, domain=key, title=marker, provision="1", content=content)]

    observed: dict[str, int] = {}
    original_create_many = KnowledgeChunkRepository.create_many

    def failing_create_many(self, items):
        # Runs *after* domains/documents/provisions were inserted, proving the
        # import had already written rows before failing.
        observed["provisions"] = self.conn.execute(
            "SELECT count(*) FROM legal_provisions WHERE text = %s", (content,)
        ).fetchone()[0]
        raise psycopg.Error("simulated failure during the chunk write phase")

    monkeypatch.setattr(KnowledgeChunkRepository, "create_many", failing_create_many)
    connection = psycopg.connect(TEST_URL)
    try:
        with pytest.raises(psycopg.Error):
            with connection.transaction():
                import_rows(connection, rows)

        assert observed.get("provisions", 0) > 0, "provisions should have been written"
        assert connection.execute(
            "SELECT count(*) FROM legal_domains WHERE key = %s", (key,)
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT count(*) FROM legal_documents WHERE title = %s", (marker,)
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT count(*) FROM legal_provisions WHERE text = %s", (content,)
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT count(*) FROM knowledge_chunks WHERE content = %s", (content,)
        ).fetchone()[0] == 0
    finally:
        monkeypatch.setattr(KnowledgeChunkRepository, "create_many", original_create_many)
        connection.close()


# --------------------------------------------------------------------------- #
# 8. No destructive operations
# --------------------------------------------------------------------------- #

def test_import_does_not_touch_unrelated_records(tx):
    other_key = _unique_key("p3c_bystander")
    domain = LegalDomainRepository(tx).create(
        key=other_key, name="Bystander", description="Must survive untouched"
    )
    document = LegalDocumentRepository(tx).create(domain["id"], "Bystander Doc", "act")
    provision = LegalProvisionRepository(tx).create(
        document_id=document["id"], text="Unrelated provision text, untouched.",
        provision_number="999", title="Unrelated",
    )
    chunk = KnowledgeChunkRepository(tx).create(
        document_id=document["id"], provision_id=provision["id"],
        domain_id=domain["id"], content="Unrelated chunk content, untouched.",
        chunk_index=1,
    )

    import_rows(
        tx,
        [_row(1, domain=_unique_key("p3c_other"), title="Fresh Doc",
              provision="1", content=FRESH_SECTION_TEXT)],
    )

    after_domain = LegalDomainRepository(tx).get_by_id(domain["id"])
    assert after_domain is not None
    assert after_domain["description"] == "Must survive untouched"
    assert LegalDocumentRepository(tx).get_by_id(document["id"]) is not None
    assert LegalProvisionRepository(tx).get_by_id(provision["id"]) is not None
    assert KnowledgeChunkRepository(tx).get_by_id(chunk["id"]) is not None


# --------------------------------------------------------------------------- #
# Full validated dataset round-trip
# --------------------------------------------------------------------------- #

def _csv_rows():
    with IMPORTER_READY.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _to_csv_row(raw, row_number):
    return CsvRow(
        row_number=row_number,
        domain=raw["domain"],
        document_title=raw["document_title"],
        document_type=raw["document_type"],
        provision_number=raw["provision_number"] or None,
        provision_title=raw["provision_title"] or None,
        content=raw["content"],
        language=raw["language"] or None,
        source_name=raw["source_name"],
        source_type=raw["source_type"],
        source_url=raw["source_url"],
        verified=raw["verified"].strip().lower() == "true",
    )


def test_full_dataset_round_trips_and_stays_set_based(tx):
    """All 721 validated rows must import and read back byte-for-byte."""
    raw_rows = _csv_rows()
    assert len(raw_rows) == 721
    _seed_domains(tx)

    rows = [_to_csv_row(raw, n) for n, raw in enumerate(raw_rows, start=1)]
    first = import_rows(tx, rows)

    # No duplicates from a single run.
    assert first.provisions_created == 721
    assert first.chunks_created == 721
    assert first.provisions_updated == 0
    assert first.domains_created == 0      # civil / family / land_property are seeded
    assert first.domains_reused == 3
    assert first.documents_created == 3
    assert first.sources_created <= 1

    # Set-based: a handful of round trips, not one or more per row.
    assert first.db_operations <= MAX_DB_OPERATIONS, first.db_operations

    # Every row reads back exactly as validated (provision + chunk text).
    for raw in raw_rows:
        domain = LegalDomainRepository(tx).get_by_key(raw["domain"])
        document = LegalDocumentRepository(tx).find_by_title_type(
            domain["id"], raw["document_title"], raw["document_type"]
        )
        provision = LegalProvisionRepository(tx).find_by_number(
            document["id"], raw["provision_number"]
        )
        assert provision is not None, raw["provision_number"]
        assert provision["text"] == raw["content"]
        assert (provision["title"] or "") == (raw["provision_title"] or "")

        chunks = KnowledgeChunkRepository(tx).find_by_provision_number(
            document["id"], raw["provision_number"]
        )
        assert len(chunks) == 1
        assert chunks[0]["content"] == raw["content"]

    # Second identical run changes nothing at all.
    second = import_rows(tx, rows)
    assert second.provisions_created == 0
    assert second.provisions_updated == 0
    assert second.chunks_created == 0
    assert second.chunks_updated == 0
    assert second.skipped == 721
    assert second.db_operations < first.db_operations


def test_full_dataset_leaves_no_duplicate_logical_records(tx):
    raw_rows = _csv_rows()
    _seed_domains(tx)
    rows = [_to_csv_row(raw, n) for n, raw in enumerate(raw_rows, start=1)]
    import_rows(tx, rows)
    import_rows(tx, rows)

    sample = next(r for r in raw_rows if r["domain"] == "family")
    domain = LegalDomainRepository(tx).get_by_key("family")
    document = LegalDocumentRepository(tx).find_by_title_type(
        domain["id"], sample["document_title"], sample["document_type"]
    )
    expected = sum(1 for r in raw_rows if r["domain"] == "family")
    provisions = LegalProvisionRepository(tx).list_by_document(document["id"])
    chunks = KnowledgeChunkRepository(tx).find_by_document(document["id"])
    assert len(provisions) == expected
    assert len(chunks) == expected
    assert len({p["provision_number"] for p in provisions}) == expected
