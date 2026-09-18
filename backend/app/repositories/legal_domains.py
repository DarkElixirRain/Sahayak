"""Repository for legal_domains."""

from __future__ import annotations

from typing import Any, Sequence
from uuid import uuid4

from app.repositories.base import BaseRepository


class LegalDomainRepository(BaseRepository):
    def create(
        self,
        key: str,
        name: str,
        description: str | None = None,
        is_active: bool = True,
    ) -> dict[str, Any]:
        row_id = uuid4()
        self._execute(
            """
            INSERT INTO legal_domains (id, key, name, description, is_active)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (row_id, key, name, description, is_active),
        )
        return self.get_by_id(row_id)  # type: ignore[return-value]

    def get_by_id(self, domain_id) -> dict[str, Any] | None:
        return self._fetch_one(
            "SELECT * FROM legal_domains WHERE id = %s", (domain_id,)
        )

    def get_by_key(self, key: str) -> dict[str, Any] | None:
        return self._fetch_one(
            "SELECT * FROM legal_domains WHERE key = %s", (key,)
        )

    def list(self, active_only: bool = True) -> list[dict[str, Any]]:
        query = "SELECT * FROM legal_domains"
        if active_only:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY key"
        return self._fetch_all(query)

    def upsert(
        self,
        key: str,
        name: str,
        description: str | None = None,
        is_active: bool = True,
    ) -> dict[str, Any]:
        self._execute(
            """
            INSERT INTO legal_domains (id, key, name, description, is_active)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (key) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                is_active = EXCLUDED.is_active,
                updated_at = now()
            """,
            (uuid4(), key, name, description, is_active),
        )
        return self.get_by_key(key)  # type: ignore[return-value]

    def exists(self, key: str) -> bool:
        return self.get_by_key(key) is not None