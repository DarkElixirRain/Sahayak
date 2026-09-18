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
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Sequence
from urllib.parse import urlsplit

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
    file: str = ""
    total: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    verified: int = 0
    unverified: int = 0
    failures: list[str] = field(default_factory=list)


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


def import_rows(conn: psycopg.Connection, rows: Sequence[CsvRow]) -> ImportReport:
    """Import validated rows on the given connection (caller controls the
    transaction). Deterministic matching prevents duplicate records on re-import.
    """
    report = ImportReport(total=len(rows))

    domains = LegalDomainRepository(conn)
    documents = LegalDocumentRepository(conn)
    provisions = LegalProvisionRepository(conn)
    sources = SourceRepository(conn)
    chunks = KnowledgeChunkRepository(conn)

    # per (document, provision) chunk_index assignment, stable within a file
    chunk_indexes: dict[tuple, int] = {}
    now = datetime.now(timezone.utc)

    for row in rows:
        domain = domains.upsert(row.domain, _domain_name(row.domain))
        document, _ = documents.get_or_create(
            domain["id"], row.document_title, row.document_type,
            official_source_url=row.source_url, language=row.language,
        )
        source, _ = sources.get_or_create(
            name=row.source_name,
            source_type=row.source_type or "official_document",
            official_url=row.source_url,
            is_official=row.source_type in OFFICIAL_SOURCE_TYPES,
            is_verified=row.verified,
            verified_at=now if row.verified else None,
        )

        provision = None
        if row.provision_number:
            provision, _ = provisions.get_or_create(
                document_id=document["id"],
                text=row.content,
                provision_number=row.provision_number,
                title=row.provision_title,
                language=row.language,
            )

        key = (document["id"], provision["id"] if provision else None)
        chunk_indexes[key] = chunk_indexes.get(key, 0) + 1
        chunk_index = chunk_indexes[key]

        existing = chunks.find_existing(
            document["id"],
            provision["id"] if provision else None,
            chunk_index,
            row.language,
        )

        fields = dict(
            title=row.provision_title or document["title"],
            content=row.content,
            language=row.language,
            chunk_index=chunk_index,
            source_type=row.source_type or "official_document",
            is_verified=row.verified,
            verified_at=now if row.verified else None,
        )

        try:
            if existing is None:
                chunks.create(
                    document_id=document["id"],
                    provision_id=provision["id"] if provision else None,
                    domain_id=domain["id"],
                    source_id=source["id"],
                    **fields,
                )
                report.inserted += 1
            else:
                changed = any(existing.get(k) != v for k, v in fields.items())
                if changed:
                    chunks._execute(
                        """
                        UPDATE knowledge_chunks SET
                            title = %s, content = %s, language = %s,
                            chunk_index = %s, source_type = %s,
                            is_verified = %s, verified_at = %s, updated_at = now()
                        WHERE id = %s
                        """,
                        (
                            fields["title"], fields["content"], fields["language"],
                            fields["chunk_index"], fields["source_type"],
                            fields["is_verified"], fields["verified_at"],
                            existing["id"],
                        ),
                    )
                    report.updated += 1
                else:
                    report.skipped += 1
        except psycopg.Error as exc:
            report.failed += 1
            report.failures.append(f"Row {row.row_number}: database error ({exc})")
            raise

        if row.verified:
            report.verified += 1
        else:
            report.unverified += 1

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