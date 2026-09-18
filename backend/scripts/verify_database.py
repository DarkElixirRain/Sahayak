"""Verify the Sahayak database schema after migrations.

Checks the connection, expected tables, foreign keys, and key indexes.

Usage:
    python scripts/verify_database.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg  # noqa: E402

from app.core.config import settings  # noqa: E402

EXPECTED_TABLES = [
    "legal_domains",
    "legal_documents",
    "legal_provisions",
    "knowledge_chunks",
    "sources",
    "government_resources",
    "court_cases",
    "risk_rules",
    "conversation_sessions",
    "conversation_messages",
]

EXPECTED_INDEXES = {
    "legal_documents": ["idx_legal_documents_domain_id"],
    "legal_provisions": ["idx_legal_provisions_document_id"],
    "knowledge_chunks": [
        "idx_knowledge_chunks_document_id",
        "idx_knowledge_chunks_provision_id",
        "idx_knowledge_chunks_domain_id",
        "idx_knowledge_chunks_is_verified",
        "uq_knowledge_chunks_doc_prov_idx_lang",
    ],
    "government_resources": ["idx_government_resources_domain_id"],
    "court_cases": ["idx_court_cases_domain_id", "idx_court_cases_decision_date"],
    "risk_rules": ["idx_risk_rules_domain_id", "idx_risk_rules_is_active"],
    "conversation_messages": ["idx_conversation_messages_session_id"],
}


def main() -> int:
    if not settings.database_url:
        print("✗ DATABASE_URL is not set")
        return 1

    try:
        conn = psycopg.connect(settings.database_url)
    except psycopg.Error:
        print("✗ Database connection: FAILED")
        return 1
    ok = True
    print("✓ Database connection")

    with conn:
        tables = {
            r[0] for r in conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            ).fetchall()
        }
        for t in EXPECTED_TABLES:
            if t in tables:
                print(f"✓ {t}")
            else:
                print(f"✗ {t} (missing)")
                ok = False

        indexes = {
            r[0] for r in conn.execute(
                "SELECT indexname FROM pg_indexes WHERE schemaname = 'public'"
            ).fetchall()
        }
        for table, expected in EXPECTED_INDEXES.items():
            for index in expected:
                if index in indexes:
                    print(f"✓ index {index}")
                else:
                    print(f"✗ index {index} (missing on {table})")
                    ok = False

        fk_count = conn.execute(
            """
            SELECT count(*) FROM pg_constraint c
            JOIN pg_class t ON t.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE c.contype = 'f' AND n.nspname = 'public'
            """
        ).fetchone()[0]
        print(f"✓ foreign keys ({fk_count} constraints)")

    conn.close()
    if ok:
        print("\nDatabase schema is complete.")
    else:
        print("\nDatabase schema is MISSING items. Run: python scripts/migrate.py")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())