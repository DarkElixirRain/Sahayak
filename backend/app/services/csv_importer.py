"""CSV ingestion pipeline for the legal knowledge dataset.

Responsibilities:
    * read UTF-8 / UTF-8-BOM CSVs without corrupting Devanagari text
    * validate every row (never trust the CSV blindly)
    * import valid rows atomically in a single controlled transaction
    * deterministic matching so re-imports do not create duplicates
    * preserve source provenance and the dataset's own verification claim

The ``verified`` value is taken verbatim from the source dataset. A value of
``true`` means the content has been checked against the original authoritative
source by the research team — never because a parser succeeded.
"""

from __future__ import annotations

import csv
import pathlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Sequence
from urllib.parse import urlsplit
from uuid import uuid4

import psycopg

from app.core.config import settings
from app.db.seed_data import SEED_DOMAINS, SEED_DOMAIN_KEYS
from app.repositories.knowledge_chunks import KnowledgeChunkRepository
from app.repositories.legal_documents import LegalDocumentRepository
from app.repositories.legal_domains import LegalDomainRepository
from app.repositories.legal_provisions import LegalProvisionRepository
from app.repositories.sources import SourceRepository

REQUIRED_FIELDS = (
    "domain", "document_title", "document_type", "content",
    "source_name", "source_url", "verified",
)
EXPECTED_HEADER = (
    "domain", "document_title", "document_type", "provision_number",
    "provision_title", "content", "language", "source_name", "source_type",
    "source_url", "verified",
)
MIN_CONTENT_LENGTH = 10
DEFAULT_SOURCE_TYPE = "official_document"
OFFICIAL_SOURCE_TYPES = {
    "government", "law_commission", "court", "ministry", "police", "regulator",
}


class CsvFormatError(Exception):
    """Raised when a CSV file cannot be read or its header is unusable."""


@dataclass(frozen=True)
class CsvRow:
    row_number: int
    domain: str
    document_title: str
    document_type: str
    provision_number: str | None
    provision_title: str | None
    content: str
    language: str | None
    source_name: str
    source_type: str
    source_url: str
    verified: bool


@dataclass(frozen=True)
class RowIssue:
    field: str
    message: str


@dataclass
class ValidationReport:
    file: str
    total: int = 0
    valid: int = 0
    invalid: int = 0
    file_errors: list[str] = field(default_factory=list)
    issues: dict[int, list[RowIssue]] = field(default_factory=dict)
    rows: list[CsvRow] = field(default_factory=list)


@dataclass
class ImportReport:
    """Outcome of a single import run.

    ``inserted`` / ``updated`` / ``skipped`` count *rows* and therefore map to
    knowledge chunks (the retrieval-facing unit). The per-table counters report
    exactly what changed underneath, so a re-import of unchanged data can be
    shown to be a genuine no-op.
    """

    file: str = ""
    total: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    verified: int = 0
    unverified: int = 0
    failures: list[str] = field(default_factory=list)

    # per-table detail
    domains_created: int = 0
    domains_reused: int = 0
    documents_created: int = 0
    documents_reused: int = 0
    sources_created: int = 0
    sources_reused: int = 0
    provisions_created: int = 0
    provisions_updated: int = 0
    provisions_unchanged: int = 0
    chunks_created: int = 0
    chunks_updated: int = 0

    # performance bookkeeping
    db_operations: int = 0
    duration_seconds: float = 0.0


# --------------------------------------------------------------------------- #
# Parsing & reading
# --------------------------------------------------------------------------- #

def _clean(value: str | None) -> str:
    return (value or "").strip()


def parse_verified(value: str | None) -> bool | None:
    """Accept true/false/1/0 (case-insensitive); anything else is invalid."""
    v = _clean(value).lower()
    if v in ("true", "1"):
        return True
    if v in ("false", "0"):
        return False
    return None


def is_valid_url(value: str) -> bool:
    value = _clean(value)
    if not value:
        return False
    parts = urlsplit(value)
    return parts.scheme in ("http", "https") and bool(parts.netloc)


def read_rows(path: pathlib.Path) -> list[dict[str, str]]:
    """Read a CSV (UTF-8 or UTF-8 with BOM) into raw dict rows."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise CsvFormatError(f"Cannot read file: {exc}") from exc

    if raw.startswith(b"\xef\xbb\xbf"):
        text = raw.decode("utf-8-sig")
    else:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CsvFormatError(
                "CSV is not valid UTF-8 (expected UTF-8 or UTF-8 with BOM)."
            ) from exc

    reader = csv.DictReader(__import__("io").StringIO(text))
    if reader.fieldnames is None:
        raise CsvFormatError("CSV file has no header row.")
    header = [h.strip() for h in reader.fieldnames]

    missing = [f for f in REQUIRED_FIELDS if f not in header]
    if missing:
        raise CsvFormatError(
            f"CSV is missing required columns: {', '.join(missing)}."
        )

    rows: list[dict[str, str]] = []
    for row in reader:
        rows.append({k.strip(): _clean(v) for k, v in row.items()})
    return rows


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #

def validate_row(
    raw: dict[str, str],
    row_number: int,
    known_domains: set[str],
    seen: dict[tuple, int],
) -> list[RowIssue]:
    issues: list[RowIssue] = []

    def check(field: str, ok: bool, message: str) -> None:
        if not ok:
            issues.append(RowIssue(field=field, message=message))

    check("domain", bool(raw.get("domain")), "domain is empty")
    check("document_title", bool(raw.get("document_title")), "document_title is empty")
    check("document_type", bool(raw.get("document_type")), "document_type is empty")
    check("content", bool(raw.get("content")), "content is empty")
    check("source_name", bool(raw.get("source_name")), "source_name is empty")
    check("source_url", is_valid_url(raw.get("source_url", "")), "source_url is malformed")

    if raw.get("document_type") and raw["document_type"] not in ("act", "code", "regulation",
        "rule", "directive", "procedure", "policy", "other"):
        issues.append(RowIssue("document_type", f"invalid document_type: {raw['document_type']!r}"))

    verified = parse_verified(raw.get("verified"))
    if verified is None:
        issues.append(RowIssue(
            "verified", f"invalid verified value: {raw.get('verified')!r}"
        ))

    if raw.get("domain") and raw["domain"] not in known_domains:
        issues.append(RowIssue("domain", f"domain does not exist: {raw['domain']!r}"))

    content = raw.get("content", "")
    if 0 < len(content) < MIN_CONTENT_LENGTH:
        issues.append(RowIssue("content", f"content is suspiciously short ({len(content)} chars)"))

    if not issues:
        dedup_key = (raw.get("document_title"), raw.get("provision_number"), content)
        if dedup_key in seen:
            issues.append(RowIssue(
                "content", f"duplicate record (first seen at row {seen[dedup_key]})"
            ))
        else:
            seen[dedup_key] = row_number

    return issues


def to_row(raw: dict[str, str], row_number: int) -> CsvRow:
    verified = parse_verified(raw.get("verified"))
    return CsvRow(
        row_number=row_number,
        domain=raw.get("domain", ""),
        document_title=raw.get("document_title", ""),
        document_type=raw.get("document_type", ""),
        provision_number=raw.get("provision_number") or None,
        provision_title=raw.get("provision_title") or None,
        content=raw.get("content", ""),
        language=raw.get("language") or None,
        source_name=raw.get("source_name", ""),
        source_type=raw.get("source_type") or "official_document",
        source_url=raw.get("source_url", ""),
        verified=verified or False,
    )


def known_domain_keys(database_url: str | None = None) -> set[str]:
    """Seed domain keys merged with any domains already stored in the database."""
    keys: set[str] = set(SEED_DOMAIN_KEYS)
    if database_url:
        try:
            with psycopg.connect(database_url) as conn:
                rows = conn.execute("SELECT key FROM legal_domains").fetchall()
            keys.update(r[0] for r in rows)
        except psycopg.Error:
            pass  # database unavailable: fall back to seed keys only
    return keys


def validate_file(path: pathlib.Path, database_url: str | None = None) -> ValidationReport:
    report = ValidationReport(file=str(path))
    domains = known_domain_keys(database_url)
    rows = read_rows(path)
    report.total = len(rows)

    seen: dict[tuple, int] = {}
    for i, raw in enumerate(rows, start=1):
        issues = validate_row(raw, i, domains, seen)
        if issues:
            report.invalid += 1
            report.issues[i] = issues
        else:
            report.valid += 1
            report.rows.append(to_row(raw, i))
    return report


# --------------------------------------------------------------------------- #
# Import
# --------------------------------------------------------------------------- #

def _domain_name(key: str) -> str:
    for d in SEED_DOMAINS:
        if d["key"] == key:
            return d["name"]
    return key


def _source_identity(row: CsvRow) -> tuple:
    """Natural key used to reuse a source row.

    Mirrors ``SourceRepository.get_or_create``: a source with an official URL
    is identified by that URL (``sources.uq_sources_official_url``); otherwise
    it falls back to ``(name, source_type)``.
    """
    source_type = row.source_type or DEFAULT_SOURCE_TYPE
    if row.source_url:
        return ("url", row.source_url)
    return ("name", row.source_name, source_type)


def import_rows(conn: psycopg.Connection, rows: Sequence[CsvRow]) -> ImportReport:
    """Import validated rows on the given connection (caller controls the
    transaction). Deterministic matching prevents duplicate records on re-import.

    Performance contract
    --------------------
    No query is ever issued per CSV row. The work is set-based:

    1. prefetch every domain / source / document / provision / chunk that the
       file could possibly touch (one query per table, keyed to the domains and
       documents involved)
    2. decide create / refresh / no-op for each row in memory
    3. write each affected table with a single batched statement

    A 721-row file therefore costs roughly a dozen network round trips instead
    of the ~6,500 a per-row loop produces against remote PostgreSQL, which is
    what made a full Neon import time out. Transactional guarantees are
    unchanged: every statement runs on the caller's connection and transaction,
    so a failure rolls the whole import back.
    """
    report = ImportReport(total=len(rows))
    if not rows:
        return report

    started = time.perf_counter()
    now = datetime.now(timezone.utc)
    operations = 0

    domains_repo = LegalDomainRepository(conn)
    documents_repo = LegalDocumentRepository(conn)
    provisions_repo = LegalProvisionRepository(conn)
    sources_repo = SourceRepository(conn)
    chunks_repo = KnowledgeChunkRepository(conn)

    # ---------------------------------------------------------------- domains
    # Reuse by stable key. Existing metadata (name/description) is never
    # overwritten — the seeded taxonomy stays authoritative for itself.
    domain_keys = sorted({row.domain for row in rows})
    domains = domains_repo.map_by_keys(domain_keys)
    operations += 1
    missing_domains = [key for key in domain_keys if key not in domains]
    if missing_domains:
        domains.update(
            domains_repo.create_many(
                [{"key": key, "name": _domain_name(key)} for key in missing_domains]
            )
        )
        operations += 2
    report.domains_created = len(missing_domains)
    report.domains_reused = len(domain_keys) - len(missing_domains)

    # ---------------------------------------------------------------- sources
    source_identities: dict[tuple, CsvRow] = {}
    for row in rows:
        source_identities.setdefault(_source_identity(row), row)

    source_urls = {ident[1] for ident in source_identities if ident[0] == "url"}
    source_name_pairs = {
        (ident[1], ident[2]) for ident in source_identities if ident[0] == "name"
    }
    sources_by_url = sources_repo.map_by_urls(source_urls)
    sources_by_name = sources_repo.map_by_name_types(source_name_pairs)
    operations += 2

    def _lookup_source(ident: tuple) -> dict[str, Any] | None:
        if ident[0] == "url":
            return sources_by_url.get(ident[1])
        return sources_by_name.get((ident[1], ident[2]))

    source_ids: dict[tuple, Any] = {}
    new_sources: list[dict[str, Any]] = []
    for ident, row in source_identities.items():
        existing = _lookup_source(ident)
        if existing is not None:
            source_ids[ident] = existing["id"]
            continue
        source_type = row.source_type or DEFAULT_SOURCE_TYPE
        new_sources.append(
            {
                "name": row.source_name,
                "source_type": source_type,
                "official_url": row.source_url or None,
                "is_official": source_type in OFFICIAL_SOURCE_TYPES,
                "is_verified": row.verified,
                "verified_at": now if row.verified else None,
            }
        )
    reused_sources = len(source_ids)
    if new_sources:
        sources_repo.create_many(new_sources)
        operations += 1
        sources_by_url = sources_repo.map_by_urls(source_urls)
        sources_by_name = sources_repo.map_by_name_types(source_name_pairs)
        operations += 2
        for ident in source_identities:
            if ident in source_ids:
                continue
            found = _lookup_source(ident)
            if found is None:
                raise psycopg.Error(
                    f"Could not resolve source for identity {ident!r} during import"
                )
            source_ids[ident] = found["id"]
    report.sources_reused = reused_sources
    report.sources_created = len(source_identities) - reused_sources

    # -------------------------------------------------------------- documents
    # Reuse by deterministic (domain, title, document_type) — the same key as
    # the ``uq_legal_documents_domain_title_type`` index.
    doc_identities: dict[tuple, CsvRow] = {}
    for row in rows:
        doc_identities.setdefault(
            (row.domain, row.document_title, row.document_type), row
        )

    domain_ids = [domains[key]["id"] for key in domain_keys]
    existing_documents = documents_repo.list_by_domain_ids(domain_ids)
    operations += 1
    documents_by_key = {
        (d["domain_id"], d["title"], d["document_type"]): d
        for d in existing_documents
    }

    doc_ids: dict[tuple, Any] = {}
    new_documents: list[dict[str, Any]] = []
    for ident, row in doc_identities.items():
        domain_id = domains[ident[0]]["id"]
        found = documents_by_key.get((domain_id, ident[1], ident[2]))
        if found is not None:
            doc_ids[ident] = found["id"]
            continue
        new_documents.append(
            {
                "domain_id": domain_id,
                "title": row.document_title,
                "document_type": row.document_type,
                "official_source_url": row.source_url or None,
                "language": row.language,
            }
        )
    reused_documents = len(doc_ids)
    if new_documents:
        documents_repo.create_many(new_documents)
        operations += 1
        for d in documents_repo.list_by_domain_ids(domain_ids):
            documents_by_key[(d["domain_id"], d["title"], d["document_type"])] = d
        operations += 1
        for ident in doc_identities:
            if ident in doc_ids:
                continue
            domain_id = domains[ident[0]]["id"]
            found = documents_by_key.get((domain_id, ident[1], ident[2]))
            if found is None:
                raise psycopg.Error(
                    f"Could not resolve document for {ident!r} during import"
                )
            doc_ids[ident] = found["id"]
    report.documents_reused = reused_documents
    report.documents_created = len(doc_identities) - reused_documents

    document_titles = {d["id"]: d["title"] for d in documents_by_key.values()}
    import_document_ids = list({doc_ids[i] for i in doc_identities})

    # ------------------------------------------------------------- provisions
    existing_provisions = provisions_repo.list_by_document_ids(import_document_ids)
    operations += 1
    provisions_by_number: dict[tuple, dict[str, Any]] = {}
    unnumbered_by_content: dict[tuple, list[dict[str, Any]]] = {}
    for p in existing_provisions:
        if p["provision_number"] is not None:
            provisions_by_number[(p["document_id"], p["provision_number"])] = p
        else:
            unnumbered_by_content.setdefault(
                (p["document_id"], p["text"], p["title"]), []
            ).append(p)

    provision_inserts: list[dict[str, Any]] = []
    provision_updates: list[tuple] = []

    # chunk_index is assigned per (document, provision) exactly as the
    # per-row implementation did, so indexes stay stable across runs.
    chunk_indexes: dict[tuple, int] = {}
    prepared: list[dict[str, Any]] = []

    for row in rows:
        document_id = doc_ids[(row.domain, row.document_title, row.document_type)]
        source_id = source_ids[_source_identity(row)]

        if row.provision_number:
            existing = provisions_by_number.get((document_id, row.provision_number))
            if existing is None:
                provision_id = uuid4()
                provision_inserts.append(
                    {
                        "id": provision_id,
                        "document_id": document_id,
                        "provision_number": row.provision_number,
                        "title": row.provision_title,
                        "text": row.content,
                        "language": row.language,
                    }
                )
            else:
                provision_id = existing["id"]
                if (
                    existing["text"] != row.content
                    or existing["title"] != row.provision_title
                ):
                    # Stale legal text (e.g. a pre-Phase-3B import) is refreshed
                    # in place from the validated dataset.
                    provision_updates.append(
                        (row.content, row.provision_title, provision_id)
                    )
                    existing["text"] = row.content
                    existing["title"] = row.provision_title
                    report.provisions_updated += 1
                else:
                    report.provisions_unchanged += 1
        else:
            pool = unnumbered_by_content.get(
                (document_id, row.content, row.provision_title)
            )
            if pool:
                provision_id = pool.pop(0)["id"]
                report.provisions_unchanged += 1
            else:
                provision_id = uuid4()
                provision_inserts.append(
                    {
                        "id": provision_id,
                        "document_id": document_id,
                        "provision_number": None,
                        "title": row.provision_title,
                        "text": row.content,
                        "language": row.language,
                    }
                )

        key = (document_id, provision_id)
        chunk_indexes[key] = chunk_indexes.get(key, 0) + 1

        prepared.append(
            {
                "row": row,
                "document_id": document_id,
                "domain_id": domains[row.domain]["id"],
                "source_id": source_id,
                "provision_id": provision_id,
                "chunk_index": chunk_indexes[key],
            }
        )

    report.provisions_created = len(provision_inserts)

    # ----------------------------------------------------------------- chunks
    existing_chunks = chunks_repo.list_by_document_ids(import_document_ids)
    operations += 1
    chunks_by_key = {
        (c["document_id"], c["provision_id"], c["chunk_index"], c["language"]): c
        for c in existing_chunks
    }

    chunk_inserts: list[dict[str, Any]] = []
    chunk_updates: list[tuple] = []

    for item in prepared:
        row = item["row"]
        fields = {
            "title": row.provision_title or document_titles.get(item["document_id"]),
            "content": row.content,
            "language": row.language,
            "chunk_index": item["chunk_index"],
            "source_type": row.source_type or DEFAULT_SOURCE_TYPE,
            "is_verified": row.verified,
            "verified_at": now if row.verified else None,
        }
        existing = chunks_by_key.get(
            (
                item["document_id"],
                item["provision_id"],
                item["chunk_index"],
                row.language,
            )
        )
        if existing is None:
            chunk_inserts.append(
                {
                    "id": uuid4(),
                    "document_id": item["document_id"],
                    "provision_id": item["provision_id"],
                    "domain_id": item["domain_id"],
                    "source_id": item["source_id"],
                    **fields,
                }
            )
        elif any(existing.get(k) != v for k, v in fields.items()):
            chunk_updates.append(
                (
                    fields["title"], fields["content"], fields["language"],
                    fields["chunk_index"], fields["source_type"],
                    fields["is_verified"], fields["verified_at"], existing["id"],
                )
            )
        else:
            report.skipped += 1

    # ----------------------------------------------------------------- writes
    # Documents/domains/sources are already written above (provisions and
    # chunks depend on them). Everything below stays on the caller's
    # transaction: any error rolls the whole import back.
    try:
        if provision_inserts:
            provisions_repo.create_many(provision_inserts)
            operations += 1
        if provision_updates:
            provisions_repo.update_text_many(provision_updates)
            operations += 1
        if chunk_inserts:
            chunks_repo.create_many(chunk_inserts)
            operations += 1
        if chunk_updates:
            chunks_repo.update_content_many(chunk_updates)
            operations += 1
    except psycopg.Error as exc:
        report.failed += len(rows)
        report.failures.append(f"Database error during bulk import: {exc}")
        raise

    report.inserted = len(chunk_inserts)
    report.chunks_created = len(chunk_inserts)
    report.updated = len(chunk_updates)
    report.chunks_updated = len(chunk_updates)
    report.verified = sum(1 for row in rows if row.verified)
    report.unverified = len(rows) - report.verified
    report.db_operations = operations
    report.duration_seconds = time.perf_counter() - started
    return report


def import_csv_file(
    path: pathlib.Path,
    best_effort: bool = False,
    database_url: str | None = None,
) -> ImportReport:
    """Validate a CSV, then import valid rows atomically.

    Default behaviour: any invalid row aborts the import before touching the
    database. With ``best_effort``, valid rows are imported and invalid rows are
    reported as failed. Database errors always roll back the whole import.
    """
    database_url = database_url or settings.database_url
    report = validate_file(path, database_url)

    if not report.rows:
        return ImportReport(
            file=str(path), total=report.total,
            failed=report.invalid, failures=["No valid rows to import."],
        )

    if report.invalid and not best_effort:
        failures = [f"Row {n}: {', '.join(i.message for i in issues)}"
                    for n, issues in report.issues.items()]
        import_report = ImportReport(
            file=str(path), total=report.total, failed=report.invalid,
            failures=["Import aborted: validation failed."] + failures,
        )
        import_report.total = report.total
        import_report.verified = sum(1 for r in report.rows if r.verified)
        import_report.unverified = sum(1 for r in report.rows if not r.verified)
        return import_report

    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            result = import_rows(conn, report.rows)

    result.file = str(path)
    result.total = report.total
    result.failed += report.invalid
    if report.invalid:
        for n, issues in report.issues.items():
            result.failures.append(
                f"Row {n}: {', '.join(i.message for i in issues)}"
            )
    return result