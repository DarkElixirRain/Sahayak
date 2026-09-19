"""Database session/pool management around the Neon PostgreSQL connection.

Phase 1 provides pool lifecycle and a health check only. Persistence models
and repository helpers will build on ``get_connection`` in later phases.
"""

from contextlib import contextmanager
from typing import Any, Iterator, Optional

from psycopg_pool import ConnectionPool

from app.core.config import settings
from app.core.exceptions import DatabaseUnavailableError

_pool: Optional["ConnectionPool"] = None


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
    """Yield a pooled connection, initializing the pool on first use if necessary.

    In the FastAPI server the pool is created during the ``lifespan`` startup hook.
    Unit‑tests and other background code (e.g. the ``CaseContextManager`` used in
    the six‑turn tests) instantiate the connection manager without running the
    FastAPI lifecycle, which previously resulted in ``_pool`` being ``None`` and
    consequently raising ``DatabaseUnavailableError``.  This broke persistence of
    ``CaseContext`` across fresh manager instances, causing the test
    ``test_context_persists_across_manager_instances`` to fail.

    The fix lazily calls :func:`init_pool` the first time a connection is
    requested when ``_pool`` is not yet initialised.  ``init_pool`` is idempotent –
    calling it multiple times simply replaces the existing pool with a new one –
    so this change is safe for both the running server (where the pool is already
    created) and test environments.
    """
    # Initialise the pool lazily for non‑FastAPI contexts (e.g., tests).
    if _pool is None:
        init_pool()
    if _pool is None:
        raise DatabaseUnavailableError()
    import psycopg
    try:
        with _pool.connection() as conn:
            yield conn
    except psycopg.Error:
        # Any lower‑level error (e.g., connection drop) is surfaced as the same
        # safe, user‑facing exception used elsewhere in the codebase.
        raise DatabaseUnavailableError()


def db_dependency():
    """FastAPI dependency that yields a pooled database connection.

    Deliberately an *undecorated* generator function: FastAPI (0.141+) wraps
    sync generator dependencies in ``functools.contextmanager`` itself, so a
    ``@contextmanager``-decorated function such as ``get_connection`` would be
    wrapped twice and break every route that uses it as a ``Depends``.
    """
    with get_connection() as conn:
        yield conn


def check_database() -> bool:
    """Run ``SELECT 1`` against the pool. Raises on failure (never leaks)."""
    if not is_database_configured() or _pool is None:
        raise DatabaseUnavailableError()
    with get_connection() as conn:
        conn.execute("SELECT 1")
    return True