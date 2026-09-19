"""Top-level pytest fixtures for Sahayak backend tests."""

from __future__ import annotations

import os
import pytest

DATABASE_URL = os.environ.get("DATABASE_URL", "")


@pytest.fixture(scope="session", autouse=True)
def init_live_db_pool():
    """Initialize the psycopg connection pool from DATABASE_URL for tests
    that exercise the real retrieval service.

    Only active when DATABASE_URL is set. The pool is torn down after the
    session. Tests that use TEST_DATABASE_URL manage their own pool in their
    own fixtures (see integration/test_phase4_retrieval.py).
    """
    if not DATABASE_URL:
        yield
        return

    import app.core.config as config
    from app.db import session as db_session

    # If the app pool is already pointing at the live DB, leave it alone.
    if config.settings.database_url == DATABASE_URL and db_session._pool is not None:
        yield
        return

    original_url = config.settings.database_url
    # Only replace the pool if DATABASE_URL differs from what's configured.
    needs_pool_reset = (
        config.settings.database_url != DATABASE_URL
        or db_session._pool is None
    )

    if needs_pool_reset:
        config.settings.database_url = DATABASE_URL
        db_session.close_pool()
        db_session.init_pool()

    yield

    if needs_pool_reset:
        db_session.close_pool()
        config.settings.database_url = original_url


@pytest.fixture(autouse=True)
def mock_auth():
    """Mock get_current_user for all existing tests that don't test auth explicitly."""
    from app.main import app
    from app.api.dependencies.auth import get_current_user

    def override_get_current_user():
        return {"id": "00000000-0000-0000-0000-000000000000", "email": "test@example.com"}

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.clear()

