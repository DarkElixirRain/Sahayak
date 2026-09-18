"""Versioned SQL migration runner.

Each file in ``app/db/migrations/`` is applied at most once, tracked in a
``schema_migrations`` table.  Every migration runs inside its own transaction
so a failure rolls back cleanly.

Application code never calls ``Base.metadata.create_all(...)``; schema
changes are reproducible through plain SQL files.
"""

from __future__ import annotations

import pathlib
from typing import Sequence

import psycopg

MIGRATIONS_DIR = pathlib.Path(__file__).parent / "migrations"
_MIGRATIONS_TABLE = "schema_migrations"


def _ensure_migrations_table(conn: psycopg.Connection) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {_MIGRATIONS_TABLE} (
            version     TEXT PRIMARY KEY,
            applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def _applied_versions(conn: psycopg.Connection) -> set[str]:
    rows = conn.execute(f"SELECT version FROM {_MIGRATIONS_TABLE}").fetchall()
    return {r[0] for r in rows}


def _migration_files(migrations_dir: pathlib.Path) -> list[pathlib.Path]:
    return sorted(
        p for p in migrations_dir.iterdir()
        if p.suffix == ".sql" and p.is_file()
    )


def run_migrations(
    database_url: str,
    migrations_dir: pathlib.Path | None = None,
) -> list[str]:
    """Apply all pending migrations and return the list of applied versions."""
    migrations_dir = migrations_dir or MIGRATIONS_DIR
    with psycopg.connect(database_url) as conn:
        _ensure_migrations_table(conn)
        applied = _applied_versions(conn)
        files = _migration_files(migrations_dir)
        newly_applied: list[str] = []

        for path in files:
            version = path.name
            if version in applied:
                continue
            sql = path.read_text(encoding="utf-8")
            with conn.transaction():
                conn.execute(sql)
                conn.execute(
                    f"INSERT INTO {_MIGRATIONS_TABLE} (version) VALUES (%s)",
                    (version,),
                )
            newly_applied.append(version)

        return newly_applied


def main() -> None:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from app.core.config import settings

    if not settings.database_url:
        print("DATABASE_URL not set — skipping migrations.")
        raise SystemExit(1)

    applied = run_migrations(settings.database_url)
    if applied:
        for v in applied:
            print(f"  applied: {v}")
    else:
        print("No pending migrations.")
    print(f"Total migrations applied this run: {len(applied)}")


if __name__ == "__main__":
    main()