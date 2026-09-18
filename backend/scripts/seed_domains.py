"""Seed the initial legal domains.

Safely idempotent: can be run before the real CSV dataset arrives.
Only domains are seeded — never fabricated legal provisions or cases.

Usage:
    python scripts/seed_domains.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db.seed_data import SEED_DOMAINS  # noqa: E402
from app.repositories.legal_domains import LegalDomainRepository  # noqa: E402


def main() -> int:
    if not settings.database_url:
        print("DATABASE_URL is not set.")
        return 1

    with psycopg.connect(settings.database_url) as conn:
        repo = LegalDomainRepository(conn)
        for d in SEED_DOMAINS:
            repo.upsert(d["key"], d["name"], d["description"])
            print(f"  domain: {d['key']} -> {d['name']}")

    print(f"Seeded {len(SEED_DOMAINS)} legal domains.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())