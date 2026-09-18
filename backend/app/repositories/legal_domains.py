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

    def map_by_keys(self, keys: Sequence[str]) -> dict[str, dict[str, Any]]:
        """Fetch several domains at once, keyed by their stable ``key``."""
        keys = list(keys)
        if not keys:
            return {}
        rows = self._fetch_all(
            "SELECT * FROM legal_domains WHERE key = ANY(%s)", (keys,)
        )
        return {r["key"]: r for r in rows}

    def create_many(
        self, items: Sequence[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Insert several domains in one batch and return them keyed by ``key``.

        Existing keys are left completely untouched (``DO NOTHING``), so a bulk
        import can never overwrite the seeded taxonomy.
        """
        if not items:
            return {}
        self._executemany(
            """
            INSERT INTO legal_domains (id, key, name, description, is_active)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (key) DO NOTHING
            """,
            [
                (
                    uuid4(), i["key"], i["name"], i.get("description"),
                    i.get("is_active", True),
                )
                for i in items
            ],
        )
        return self.map_by_keys([i["key"] for i in items])

    def get_or_create(
        self,
        key: str,
        name: str,
        description: str | None = None,
        is_active: bool = True,
    ) -> tuple[dict[str, Any], bool]:
        """Reuse the existing domain for ``key``; create it only when missing.

        Unlike ``upsert`` this never overwrites an existing domain's metadata,
        so imports never alter the seeded taxonomy as a side effect.
        """
        existing = self.get_by_key(key)
        if existing is not None:
            return existing, False
        return (
            self.create(key=key, name=name, description=description, is_active=is_active),
            True,
        )

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