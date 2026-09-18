"""Database session/pool management around the Neon PostgreSQL connection.

Phase 1 provides pool lifecycle and a health check only. Persistence models
and repository helpers will build on ``get_connection`` in later phases.
"""

from contextlib import contextmanager
from typing import Any, Iterator

from psycopg_pool import ConnectionPool

from app.core.config import settings
from app.core.exceptions import DatabaseUnavailableError

_pool: ConnectionPool | None = None


def is_database_configured() -> bool:
    return bool(settings.database_url)


def init_pool() -> None:
    """Create and open the connection pool. No-op when DATABASE_URL is unset."""
    global _pool
    if not settings.database_url:
        return
    _pool = ConnectionPool(
        settings.database_url,
        min_size=1,
        max_size=5,
        open=False,
    )
    _pool.open(wait=True)


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def get_connection() -> Iterator[Any]:
    """Yield a pooled connection, translating failures into a safe error."""
    if _pool is None:
        raise DatabaseUnavailableError()
    try:
        with _pool.connection() as conn:
            yield conn
    except Exception:
        raise DatabaseUnavailableError()


def check_database() -> bool:
    """Run ``SELECT 1`` against the pool. Raises on failure (never leaks)."""
    if not is_database_configured() or _pool is None:
        raise DatabaseUnavailableError()
    with get_connection() as conn:
        conn.execute("SELECT 1")
    return True