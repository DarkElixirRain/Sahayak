"""Repository for conversation sessions and messages.

Handles persistence of conversation state using the existing
``conversation_sessions`` and ``conversation_messages`` tables.
No ORM - raw psycopg queries consistent with the project conventions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
from typing import Any, Sequence

import psycopg

from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository):
    """Repository for conversation sessions and messages."""

    def create_session(
        self,
        session_id: str,
        status: str = "active",
        language: str | None = None,
    ) -> dict[str, Any]:
        """Create a new conversation session.

        Args:
            session_id: Unique session identifier (UUID string).
            status: Initial status (e.g. "active", "ended").
            language: User's preferred language (e.g. "nepali", "english").

        Returns:
            Created session row as dict.
        """
        row_id = self._execute(
            """
            INSERT INTO conversation_sessions (id, session_id, status, language)
            VALUES (%s, %s, %s, %s)
            RETURNING *
            """,
            (str(uuid4()), session_id, status, language),
        )
        return row_id  # type: ignore[return-value]

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get a conversation session by session_id.

        Returns None if not found.
        """
        return self._fetch_one(
            """
            SELECT * FROM conversation_sessions
            WHERE session_id = %s
            """,
            (session_id,),
        )

    def list_session_messages(
        self, session_id: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """List messages for a session, optionally limited.

        Most recent messages first.
        """
        if limit:
            return self._fetch_all(
                """
                SELECT * FROM conversation_messages
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (session_id, limit),
            )
        return self._fetch_all(
            """
            SELECT * FROM conversation_messages
            WHERE session_id = %s
            ORDER BY created_at DESC
            """,
            (session_id,),
        )

    def add_message(
        self,
        session_id: str,
        role: str,
        input_mode: str | None = None,
        content: str | None = None,
    ) -> dict[str, Any]:
        """Add a message to a conversation session.

        role: 'user', 'assistant', or 'system'
        input_mode: 'voice' or 'text' (optional)
        content: the message text
        """
        return self._execute(
            """
            INSERT INTO conversation_messages (id, session_id, role, input_mode, content)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (str(uuid4()), session_id, role, input_mode, content),
        )

    def update_session_status(self, session_id: str, status: str) -> None:
        """Update a session's status (e.g. 'active' -> 'ended')."""
        self._execute(
            """
            UPDATE conversation_sessions
            SET status = %s, updated_at = now()
            WHERE session_id = %s
            """,
            (status, session_id),
        )

    def get_recent_context(
        self, session_id: str, max_messages: int = 10
    ) -> list[dict[str, Any]]:
        """Get recent conversation context as a list of (role, content) tuples.

        Limits to the most recent ``max_messages`` entries.
        Used for multi-turn context assembly.
        """
        rows = self._fetch_all(
            """
            SELECT role, content, created_at
            FROM conversation_messages
            WHERE session_id = %s
            ORDER BY created_at ASC
            LIMIT %s
            """,
            (session_id, max_messages),
        )
        return [
            {"role": row["role"], "content": row["content"]}
            for row in rows
        ]