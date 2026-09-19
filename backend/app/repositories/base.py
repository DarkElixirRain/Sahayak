"""Shared helpers for repositories."""

from __future__ import annotations

from typing import Any, Sequence

from psycopg.rows import dict_row

from app.db import adapters  # noqa: F401  (register jsonb read adaptation)


class BaseRepository:
    """Wrapper around a single psycopg connection with row helpers."""

    def __init__(self, conn: Any) -> None:
        self.conn = conn

    def _fetch_all(
        self, query: str, params: Sequence[Any] | None = None
    ) -> list[dict[str, Any]]:
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params or ())
            return cur.fetchall()

    def _fetch_one(
        self, query: str, params: Sequence[Any] | None = None
    ) -> dict[str, Any] | None:
        rows = self._fetch_all(query, params)
        return rows[0] if rows else None

    def _execute(self, query: str, params: Sequence[Any] | None = None) -> None:
        with self.conn.cursor() as cur:
            cur.execute(query, params or ())
            # Ensure changes are persisted.
            try:
                self.conn.commit()
            except Exception:
                pass

    def _execute_returning(
        self, query: str, params: Sequence[Any] | None = None
    ) -> dict[str, Any] | None:
        """Run a write statement that uses ``RETURNING`` and fetch its row.

        ``_execute`` discards result rows, so write helpers that must hand back
        the persisted row (generated id, defaults, timestamps) use this variant
        instead. Returns ``None`` when the statement produced no row.
        """
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params or ())
            if cur.description is None:
                return None
            rows = cur.fetchall()
            # Commit the transaction to persist changes.
            try:
                self.conn.commit()
            except Exception:
                pass
            return rows[0] if rows else None

    def _executemany(
        self, query: str, params_seq: Sequence[Sequence[Any]]
    ) -> int:
        """Run one statement for many parameter tuples in a single batch.

        Used by bulk import paths so a 700-row CSV costs a handful of network
        round trips instead of one per row. Returns the number of affected rows
        reported by the driver.
        """
        if not params_seq:
            return 0
        with self.conn.cursor() as cur:
            cur.executemany(query, list(params_seq))
            # Commit after batch execution.
            try:
                self.conn.commit()
            except Exception:
                pass
            return cur.rowcount