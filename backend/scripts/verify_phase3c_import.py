"""Read-only post-import verification for the Phase 3C legal dataset.

Compares the *entire* database against the validated importer-ready CSV
(default: ``data/legal/muluki_dewani_samhita_2074_importer_ready.csv``) and
reports counts, referential integrity, duplicates and per-row text integrity.

This script never writes: it only runs SELECTs.

Usage:
    python scripts/verify_phase3c_import.py [path/to/importer_ready.csv]
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from app.core.config import settings  # noqa: E402

DEFAULT_CSV = (
    Path(__file__).resolve().parents[1]
    / "data" / "legal" / "muluki_dewani_samhita_2074_importer_ready.csv"
)
STALE_MARKERS = ("mव्यति",)
SECTION_141_TOKEN = "व्यक्ति"


class Checker:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.checks = 0

    def check(self, label: str, ok: bool, detail: str = "") -> None:
        self.checks += 1
        suffix = f" — {detail}" if detail else ""
        print(f"  {'PASS' if ok else 'FAIL'}  {label}{suffix}")
        if not ok:
            self.failures.append(label)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    csv_path = Path(argv[0]) if argv else DEFAULT_CSV

    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        return 2
    rows = load_csv(csv_path)
    print(f"Validated CSV: {csv_path.name} ({len(rows)} rows)")

    if not settings.database_url:
        print("DATABASE_URL is not set.")
        return 1

    checker = Checker()
    conn = psycopg.connect(settings.database_url, row_factory=dict_row)
    try:
        print("\nCounts")
        counts = {}
        for table in (
            "legal_domains", "legal_documents", "sources",
            "legal_provisions", "knowledge_chunks",
        ):
            counts[table] = conn.execute(f"SELECT count(*) AS n FROM {table}").fetchone()["n"]
            print(f"    {table}: {counts[table]}")

        print("\nImported dataset")
        source_urls = {r["source_url"] for r in rows}
        doc_rows = conn.execute(
            """
            SELECT d.id, d.title, d.document_type, dm.key AS domain_key
            FROM legal_documents d
            LEFT JOIN legal_domains dm ON dm.id = d.domain_id
            WHERE d.official_source_url = ANY(%s)
            """,
            (list(source_urls),),
        ).fetchall()
        print(f"    documents: {len(doc_rows)}")
        for d in doc_rows:
            print(f"      {d['domain_key']}: {d['title']} ({d['document_type']})")

        expected_documents = {r["domain"] for r in rows}
        found_domains = {d["domain_key"] for d in doc_rows}
        checker.check(
            "one document per dataset domain",
            found_domains == expected_documents and len(doc_rows) == len(expected_documents),
            f"found={sorted(found_domains)}",
        )

        db_rows: dict[tuple[str, str], dict] = {}
        for r in conn.execute(
            """
            SELECT dm.key AS domain_key, p.id AS provision_id, p.provision_number,
                   p.title AS provision_title, p.text AS provision_text,
                   c.id AS chunk_id, c.content AS chunk_content,
                   c.title AS chunk_title, c.language, c.source_id, c.chunk_index,
                   s.name AS source_name, s.official_url AS source_url
            FROM legal_provisions p
            JOIN legal_documents d ON d.id = p.document_id
            LEFT JOIN legal_domains dm ON dm.id = d.domain_id
            LEFT JOIN knowledge_chunks c ON c.provision_id = p.id
            LEFT JOIN sources s ON s.id = c.source_id
            WHERE d.official_source_url = ANY(%s)
            """,
            (list(source_urls),),
        ):
            db_rows[(r["domain_key"], r["provision_number"])] = r

        checker.check(
            "provision count matches CSV",
            len(db_rows) == len(rows),
            f"db={len(db_rows)} csv={len(rows)}",
        )

        print("\nText integrity (all rows)")
        missing, provision_mismatch, chunk_mismatch, title_mismatch = [], [], [], []
        for row in rows:
            key = (row["domain"], row["provision_number"])
            db = db_rows.get(key)
            if db is None:
                missing.append(key)
                continue
            if db["provision_text"] != row["content"]:
                provision_mismatch.append(key)
            if db["chunk_content"] is None or db["chunk_content"] != row["content"]:
                chunk_mismatch.append(key)
            if (db["provision_title"] or "") != (row["provision_title"] or ""):
                title_mismatch.append(key)

        checker.check("no missing provisions", not missing, f"{len(missing)} missing")
        checker.check(
            "provision text matches CSV (all rows)",
            not provision_mismatch,
            f"{len(provision_mismatch)} mismatches",
        )
        checker.check(
            "chunk text matches CSV (all rows)",
            not chunk_mismatch,
            f"{len(chunk_mismatch)} mismatches",
        )
        checker.check(
            "provision titles match CSV (all rows)",
            not title_mismatch,
            f"{len(title_mismatch)} mismatches",
        )
        for key in (provision_mismatch + chunk_mismatch)[:5]:
            print(f"      mismatch at {key}")

        print("\nSection 141")
        section_rows = [r for r in rows if r["provision_number"] == "141"]
        checker.check("Section 141 present in CSV", bool(section_rows))
        for raw in section_rows:
            db = db_rows.get((raw["domain"], "141"))
            ok = db is not None and SECTION_141_TOKEN in db["provision_text"]
            checker.check(
                f"Section 141 contains {SECTION_141_TOKEN!r} ({raw['domain']})",
                ok,
            )
        stale_provisions = conn.execute(
            "SELECT count(*) AS n FROM legal_provisions WHERE text LIKE ANY(%s)",
            ([f"%{m}%" for m in STALE_MARKERS],),
        ).fetchone()["n"]
        stale_chunks = conn.execute(
            "SELECT count(*) AS n FROM knowledge_chunks WHERE content LIKE ANY(%s)",
            ([f"%{m}%" for m in STALE_MARKERS],),
        ).fetchone()["n"]
        checker.check("no stale pre-3B provision text", stale_provisions == 0,
                      f"{stale_provisions} rows")
        checker.check("no stale pre-3B chunk text", stale_chunks == 0,
                      f"{stale_chunks} rows")

        print("\nReferential integrity")
        orphan_provisions = conn.execute(
            """
            SELECT count(*) AS n FROM legal_provisions p
            LEFT JOIN legal_documents d ON d.id = p.document_id
            WHERE d.id IS NULL
            """
        ).fetchone()["n"]
        orphan_chunks_doc = conn.execute(
            """
            SELECT count(*) AS n FROM knowledge_chunks c
            LEFT JOIN legal_documents d ON d.id = c.document_id
            WHERE d.id IS NULL
            """
        ).fetchone()["n"]
        orphan_chunks_domain = conn.execute(
            """
            SELECT count(*) AS n FROM knowledge_chunks c
            WHERE c.domain_id IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM legal_domains d WHERE d.id = c.domain_id)
            """
        ).fetchone()["n"]
        imported_without_source = conn.execute(
            """
            SELECT count(*) AS n FROM knowledge_chunks c
            JOIN legal_documents d ON d.id = c.document_id
            WHERE d.official_source_url = ANY(%s) AND c.source_id IS NULL
            """,
            (list(source_urls),),
        ).fetchone()["n"]
        broken_source = conn.execute(
            """
            SELECT count(*) AS n FROM knowledge_chunks c
            WHERE c.source_id IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM sources s WHERE s.id = c.source_id)
            """
        ).fetchone()["n"]
        checker.check("no orphan provisions", orphan_provisions == 0)
        checker.check("no orphan chunks (document)", orphan_chunks_doc == 0)
        checker.check("no orphan chunks (domain)", orphan_chunks_domain == 0)
        checker.check("every imported chunk keeps its source", imported_without_source == 0,
                      f"{imported_without_source} without source")
        checker.check("no chunk points at a missing source", broken_source == 0)

        print("\nDuplicates")
        dup_provisions = conn.execute(
            """
            SELECT count(*) AS n FROM (
                SELECT document_id, provision_number
                FROM legal_provisions WHERE provision_number IS NOT NULL
                GROUP BY 1, 2 HAVING count(*) > 1
            ) x
            """
        ).fetchone()["n"]
        dup_chunks = conn.execute(
            """
            SELECT count(*) AS n FROM (
                SELECT document_id, provision_id, chunk_index, language
                FROM knowledge_chunks GROUP BY 1, 2, 3, 4 HAVING count(*) > 1
            ) x
            """
        ).fetchone()["n"]
        dup_documents = conn.execute(
            """
            SELECT count(*) AS n FROM (
                SELECT domain_id, title, document_type FROM legal_documents
                GROUP BY 1, 2, 3 HAVING count(*) > 1
            ) x
            """
        ).fetchone()["n"]
        dup_domains = conn.execute(
            """
            SELECT count(*) AS n FROM (
                SELECT key FROM legal_domains GROUP BY 1 HAVING count(*) > 1
            ) x
            """
        ).fetchone()["n"]
        dup_sources = conn.execute(
            """
            SELECT count(*) AS n FROM (
                SELECT official_url FROM sources WHERE official_url IS NOT NULL
                GROUP BY 1 HAVING count(*) > 1
            ) x
            """
        ).fetchone()["n"]
        checker.check("no duplicate provisions", dup_provisions == 0)
        checker.check("no duplicate chunks", dup_chunks == 0)
        checker.check("no duplicate documents", dup_documents == 0)
        checker.check("no duplicate domains", dup_domains == 0)
        checker.check("no duplicate source URLs", dup_sources == 0)

        print("\nDomain integrity")
        empty_names = conn.execute(
            "SELECT count(*) AS n FROM legal_domains WHERE name IS NULL OR name = ''"
        ).fetchone()["n"]
        checker.check("no domain lost its name", empty_names == 0)
        for key in sorted({r["domain"] for r in rows}):
            d = conn.execute(
                "SELECT name, description, is_active FROM legal_domains WHERE key = %s",
                (key,),
            ).fetchone()
            checker.check(
                f"domain {key!r} present and active",
                d is not None and bool(d["name"]) and d["is_active"],
                f"description={'set' if d and d['description'] else 'none'}",
            )

        print("\nVerification state")
        n_unverified = conn.execute(
            """
            SELECT count(*) AS n FROM knowledge_chunks c
            JOIN legal_documents d ON d.id = c.document_id
            WHERE d.official_source_url = ANY(%s) AND c.is_verified = FALSE
            """,
            (list(source_urls),),
        ).fetchone()["n"]
        csv_unverified = sum(1 for r in rows if r["verified"].strip().lower() != "true")
        checker.check(
            "verification state matches the dataset",
            n_unverified == csv_unverified,
            f"db_unverified={n_unverified} csv_unverified={csv_unverified}",
        )
    finally:
        conn.close()

    print()
    if checker.failures:
        print(f"RESULT: FAIL ({len(checker.failures)}/{checker.checks} checks failed)")
        for f in checker.failures:
            print(f"  - {f}")
        return 1
    print(f"RESULT: PASS ({checker.checks}/{checker.checks} checks passed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
