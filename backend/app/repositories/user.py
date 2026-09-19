from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """Repository for user accounts."""

    def create_user(
        self,
        email: str,
        password_hash: str,
        name: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a new user.

        Raises:
            psycopg.errors.UniqueViolation: If the email already exists.
        """
        user_id = str(uuid4())
        row = self._execute_returning(
            """
            INSERT INTO users (id, email, password_hash, name)
            VALUES (%s, %s, %s, %s)
            RETURNING id, email, password_hash, name, created_at, updated_at
            """,
            (user_id, email, password_hash, name),
        )
        return row or {}

    def get_user_by_email(self, email: str) -> Optional[dict[str, Any]]:
        """Retrieve a user by their email address."""
        return self._fetch_one(
            """
            SELECT id, email, password_hash, name, created_at, updated_at
            FROM users
            WHERE email = %s
            """,
            (email,),
        )

    def get_user_by_id(self, user_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a user by their ID."""
        return self._fetch_one(
            """
            SELECT id, email, password_hash, name, created_at, updated_at
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        )
