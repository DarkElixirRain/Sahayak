"""Repository for conversation sessions and messages.

Handles persistence of conversation state using the existing
``conversation_sessions`` and ``conversation_messages`` tables.
No ORM - raw psycopg queries consistent with the project conventions.

Schema contract (migration 009_create_conversation_tables.sql):

* ``conversation_sessions.id`` is the row primary key (UUID).
* ``conversation_sessions.session_id`` is the caller-facing session key
  (UUID, unique) - the value that appears in the API path.
* ``conversation_messages.session_id`` is a foreign key to
  ``conversation_sessions.id`` (the primary key), *not* to the caller-facing
  key, so message queries join through the session row.

Callers may pass any opaque string as the session key, so it is normalised
deterministically to a UUID: a valid UUID is used as-is, anything else is
mapped through ``uuid5`` with a fixed namespace, which means the same key
always resolves to the same session row across processes.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4, uuid5

from app.repositories.base import BaseRepository

# Fixed namespace so non-UUID session keys map to stable UUIDs across processes.
_SESSION_NAMESPACE = UUID("6f1a2b3c-4d5e-4f60-8a71-9b0c1d2e3f40")


def session_uuid(session_id: str) -> str:
    """Map a caller-supplied session key to the UUID stored in the database."""
    try:
        return str(UUID(str(session_id)))
    except (ValueError, AttributeError, TypeError):
        return str(uuid5(_SESSION_NAMESPACE, str(session_id)))


class ConversationRepository(BaseRepository):
    """Repository for conversation sessions and messages."""

    def create_session(
        self,
        session_id: str,
        user_id: str | None = None,
        status: str = "active",
        language: str | None = None,
    ) -> dict[str, Any]:
        """Create a new conversation session, or return the existing one.

        Repeated calls with the same session key are a no-op that leaves the
        stored ``status``/``language`` untouched.

        Args:
            session_id: Caller-facing session key (any string).
            user_id: ID of the user creating the session.
            status: Initial status (e.g. "active", "ended").
            language: User's preferred language (e.g. "nepali", "english").

        Returns:
            The persisted session row as a dict.
        """
        row = self._execute_returning(
            """
            INSERT INTO conversation_sessions (id, session_id, user_id, status, language)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (session_id) DO UPDATE SET updated_at = now()
            RETURNING *
            """,
            (str(uuid4()), session_uuid(session_id), user_id, status, language),
        )
        return row or {}

    def get_session(self, session_id: str, user_id: str | None = None) -> dict[str, Any] | None:
        """Get a conversation session by its caller-facing session key.

        If user_id is provided, enforces that the session belongs to that user.
        Returns None if not found or if the user does not own it.
        """
        query = "SELECT * FROM conversation_sessions WHERE session_id = %s"
        params = [session_uuid(session_id)]
        if user_id is not None:
            query += " AND user_id = %s"
            params.append(user_id)
        return self._fetch_one(query, tuple(params))

    def _session_row_id(self, session_id: str) -> str | None:
        """Resolve the session primary key that messages reference."""
        row = self.get_session(session_id)
        return str(row["id"]) if row else None

    def list_session_messages(
        self, session_id: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """List messages for a session, optionally limited.

        Most recent messages first.
        """
        # ``created_at DESC, id DESC`` keeps the order total even if two rows
        # ever share a timestamp.
        query = """
            SELECT m.*
            FROM conversation_messages m
            JOIN conversation_sessions s ON s.id = m.session_id
            WHERE s.session_id = %s
            ORDER BY m.created_at DESC, m.id DESC
        """
        params: list[Any] = [session_uuid(session_id)]
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        return self._fetch_all(query, params)

    def count_session_messages(self, session_id: str) -> int:
        """Count the messages stored for a session."""
        row = self._fetch_one(
            """
            SELECT COUNT(*) AS n
            FROM conversation_messages m
            JOIN conversation_sessions s ON s.id = m.session_id
            WHERE s.session_id = %s
            """,
            (session_uuid(session_id),),
        )
        return int(row["n"]) if row else 0

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

        Raises:
            ValueError: if the session does not exist (the caller must create
                it first), which is clearer than a raw foreign-key violation.
        """
        row_id = self._session_row_id(session_id)
        if row_id is None:
            raise ValueError(f"Unknown conversation session: {session_id}")

        # ``created_at`` is set explicitly with ``clock_timestamp()`` rather
        # than relying on the column default ``now()``. ``now()`` is the
        # *transaction* start time, so a user turn and the assistant reply
        # written in the same transaction would share a timestamp and the
        # history order would become undefined. This needs no migration: the
        # default still applies to any other writer.
        row = self._execute_returning(
            """
            INSERT INTO conversation_messages
                (id, session_id, role, input_mode, content, created_at)
            VALUES (%s, %s, %s, %s, %s, clock_timestamp())
            RETURNING *
            """,
            (str(uuid4()), row_id, role, input_mode, content),
        )
        return row or {}

    def update_session_status(self, session_id: str, status: str) -> None:
        """Update a session's status (e.g. 'active' -> 'ended')."""
        self._execute(
            """
            UPDATE conversation_sessions
            SET status = %s, updated_at = now()
            WHERE session_id = %s
            """,
            (status, session_uuid(session_id)),
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
            SELECT m.role, m.content, m.created_at
            FROM conversation_messages m
            JOIN conversation_sessions s ON s.id = m.session_id
            WHERE s.session_id = %s
            ORDER BY m.created_at ASC, m.id ASC
            LIMIT %s
            """,
            (session_uuid(session_id), max_messages),
        )
        return [{"role": row["role"], "content": row["content"]} for row in rows]

    def get_case_context(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve the persisted case context JSON for a session.

        Returns the stored dict, or None when no context has been saved yet.
        """
        row = self._fetch_one(
            """
            SELECT case_context
            FROM conversation_sessions
            WHERE session_id = %s
            """,
            (session_uuid(session_id),),
        )
        if row is None:
            return None
        return row.get("case_context")  # may be None if column is NULL

    def save_case_context(
        self, session_id: str, context: dict[str, Any], user_id: str | None = None
    ) -> None:
        """Persist an updated case context dict for a session.

        A PostgreSQL JSONB merge (``||``) is NOT used here because we want the
        full, authoritative state from the in-memory CaseContext to always win
        (it already incorporates prior turns). A simple SET is correct.
        """
        import json as _json
        # First try to UPDATE existing row
        update_sql = """
            UPDATE conversation_sessions
            SET case_context = %s::jsonb, updated_at = now()
            WHERE session_id = %s
            RETURNING id
        """
        rows = self._execute_returning(update_sql, (_json.dumps(context), session_uuid(session_id)))
        if not rows:
            # No existing row, INSERT with required defaults
            insert_sql = """
                INSERT INTO conversation_sessions (
                    id, session_id, user_id, status, language, case_context
                ) VALUES (
                    gen_random_uuid(), %s, %s, 'active', NULL, %s::jsonb
                )
            """
            self._execute(insert_sql, (session_uuid(session_id), user_id, _json.dumps(context)))

