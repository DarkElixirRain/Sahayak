"""Bulk transactional Phase 3C import for the validated Muluki dataset.

This uses the Phase 2 schema and natural keys, but batches the repeated
provision/chunk writes so a remote PostgreSQL connection does not require one
round trip per repository lookup. The input is validated before the write
transaction begins.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from uuid import uuid4

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.services.csv_importer import CsvFormatError, validate_file  # noqa: E402

DOCUMENT_TYPE = "act"
DOCUMENT_TITLE = "मुलुकी देवानी संहिता, २०७४"
SOURCE_TYPE = "law_commission"
OFFICIAL_SOURCE_TYPES = {"government", "law_commission", "court", "ministry", "police", "regulator"}


def _fetch_map(conn, query: str, params: tuple) -> dict[tuple, dict]:
    return {tuple(row[:-1]): dict(zip(("key",), (row[-1],))) for row in conn.execute(query, params).fetchall()}


def import_dataset(path: Path) -> dict[str, int | float]:
    validation = validate_file(path, database_url=None)
    if validation.invalid:
        raise ValueError(f"Input validation failed for {validation.invalid} row(s)")
    rows = validation.rows
    if len(rows) != 721:
        raise ValueError(f"Expected 721 validated rows, got {len(rows)}")

    started = time.perf_counter()
    result: dict[str, int | float] = {
        "rows_attempted": len(rows), "documents_inserted": 0, "provisions_inserted": 0,
        "chunks_inserted": 0, "documents_reused": 0, "provisions_reused": 0,
        "chunks_skipped": 0, "chunks_updated": 0, "sources_inserted": 0,
        "sources_reused": 0,
    }
    with psycopg.connect(settings.database_url) as conn:
        with conn.transaction():
            domain_keys = sorted({row.domain for row in rows})
            domain_rows = conn.execute(
                "SELECT id, key FROM legal_domains WHERE key = ANY(%s)", (domain_keys,)
            ).fetchall()
            domains = {row[1]: row[0] for row in domain_rows}
            if set(domains) != set(domain_keys):
                raise ValueError(f"Missing seeded domains: {sorted(set(domain_keys) - set(domains))}")

            documents: dict[tuple[str, str], object] = {}
            for key in sorted({(row.domain, row.document_title) for row in rows}):
                domain, title = key
                existing = conn.execute(
                    "SELECT id, official_source_url, language FROM legal_documents "
                    "WHERE domain_id = %s AND title = %s AND document_type = %s",
                    (domains[domain], title, DOCUMENT_TYPE),
                ).fetchone()
                if existing:
                    documents[key] = existing[0]
                    result["documents_reused"] += 1
                    continue
                doc_id = uuid4()
                conn.execute(
                    "INSERT INTO legal_documents "
                    "(id, domain_id, title, document_type, official_source_url, language) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (doc_id, domains[domain], title, DOCUMENT_TYPE,
                     rows[0].source_url, rows[0].language),
                )
                documents[key] = doc_id
                result["documents_inserted"] += 1

            source_url = rows[0].source_url
            source = conn.execute(
                "SELECT id, name, source_type, is_verified FROM sources WHERE official_url = %s",
                (source_url,),
            ).fetchone()
            if source:
                source_id = source[0]
                result["sources_reused"] += 1
            else:
                source_id = uuid4()
                conn.execute(
                    "INSERT INTO sources "
                    "(id, name, source_type, official_url, is_official, is_verified) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (source_id, rows[0].source_name, rows[0].source_type, source_url,
                     rows[0].source_type in OFFICIAL_SOURCE_TYPES, False),
                )
                result["sources_inserted"] += 1

            expected = []
            for row in rows:
                document_id = documents[(row.domain, row.document_title)]
                expected.append((row, document_id, domains[row.domain]))

            document_ids = sorted({item[1] for item in expected})
            existing_provisions = {
                (row[0], row[1]): row[2:]
                for row in conn.execute(
                    "SELECT document_id, provision_number, id, title, text, language "
                    "FROM legal_provisions WHERE document_id = ANY(%s)",
                    (document_ids,),
                ).fetchall()
            }
            missing_provisions = []
            for row, document_id, _domain_id in expected:
                key = (document_id, row.provision_number)
                existing = existing_provisions.get(key)
                if existing:
                    if existing[1:] != (row.provision_title, row.content, row.language):
                        raise ValueError(f"Existing provision differs from CSV: {row.provision_number}")
                    result["provisions_reused"] += 1
                else:
                    missing_provisions.append((uuid4(), document_id, row))
            if missing_provisions:
                with conn.cursor() as cursor:
                    cursor.executemany(
                    "INSERT INTO legal_provisions "
                    "(id, document_id, provision_number, title, text, language) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                                                [(item[0], item[1], item[2].provision_number, item[2].provision_title,
                                                    item[2].content, item[2].language) for item in missing_provisions],
                                        )
                result["provisions_inserted"] += len(missing_provisions)
                existing_provisions.update({
                    (item[1], item[2].provision_number): (item[0], item[2].provision_title, item[2].content, item[2].language)
                    for item in missing_provisions
                })

            existing_chunks = {
                (row[0], row[1], row[2], row[3]): row[4:]
                for row in conn.execute(
                    "SELECT document_id, provision_id, chunk_index, language, id, title, content, "
                    "source_type, is_verified FROM knowledge_chunks WHERE document_id = ANY(%s)",
                    (document_ids,),
                ).fetchall()
            }
            missing_chunks = []
            for row, document_id, domain_id in expected:
                provision_id = existing_provisions[(document_id, row.provision_number)][0]
                key = (document_id, provision_id, 1, row.language)
                fields = (row.provision_title, row.content, row.source_type, False)
                existing = existing_chunks.get(key)
                if existing:
                    if existing != fields:
                        conn.execute(
                            "UPDATE knowledge_chunks SET title=%s, content=%s, source_type=%s, "
                            "is_verified=%s, updated_at=now() WHERE id=%s",
                            (*fields, existing[0]),
                        )
                        result["chunks_updated"] += 1
                    else:
                        result["chunks_skipped"] += 1
                else:
                    missing_chunks.append((uuid4(), document_id, provision_id, domain_id, source_id, row))
            if missing_chunks:
                with conn.cursor() as cursor:
                    cursor.executemany(
                    "INSERT INTO knowledge_chunks "
                    "(id, document_id, provision_id, domain_id, source_id, title, content, language, "
                    "chunk_index, source_type, is_verified) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, %s, %s)",
                                                [(item[0], item[1], item[2], item[3], item[4], item[5].provision_title,
                                                    item[5].content, item[5].language, item[5].source_type, False)
                                                 for item in missing_chunks],
                                        )
                result["chunks_inserted"] += len(missing_chunks)
    result["duration_seconds"] = round(time.perf_counter() - started, 3)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bulk transactional Phase 3C Muluki import.")
    parser.add_argument("input", type=Path)
    args = parser.parse_args(argv)
    try:
        report = import_dataset(args.input)
    except (CsvFormatError, ValueError, OSError, psycopg.Error) as exc:
        print(f"PHASE 3C IMPORT FAILED: {type(exc).__name__}: {exc}")
        return 1
    for key, value in report.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())