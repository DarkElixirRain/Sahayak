from contextlib import contextmanager

from psycopg_pool import ConnectionPool

from app.config import settings

_pool: ConnectionPool | None = None


def init_pool() -> None:
    global _pool
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
def get_connection():
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    with _pool.connection() as conn:
        yield conn