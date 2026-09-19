"""Shared pytest fixtures for Phase 11 integration tests."""

from __future__ import annotations

import os
import pytest

DATABASE_URL = os.environ.get("DATABASE_URL", "")


@pytest.fixture(scope="session", autouse=True)
def init_db_pool():
    """Initialize the psycopg connection pool for integration tests.

    Points the application pool at DATABASE_URL (the live Neon DB).
    Skips gracefully if DATABASE_URL is not set.
    """
    if not DATABASE_URL:
        yield
        return

    import app.core.config as config
    from app.db import session as db_session

    # Point the application pool at the live database
    original_url = config.settings.database_url
    config.settings.database_url = DATABASE_URL
    db_session.close_pool()
    db_session.init_pool()

    yield

    # Restore original state
    db_session.close_pool()
    config.settings.database_url = original_url
