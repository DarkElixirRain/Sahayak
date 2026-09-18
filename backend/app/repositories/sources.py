"""Repository for sources (provenance)."""

from __future__ import annotations

from typing import Any, Sequence
from uuid import uuid4

from app.repositories.base import BaseRepository

SOURCE_TYPES = (
    "government", "law_commission", "court", "ministry",
    "police", "regulator", "official_document", "other",
)


class SourceRepository(BaseRepository):
    def create(
        self,
        name: str,
        source_type: str,
        official_url: str | None = None,
        organization: str | None = None,
        description: str | None = None,
        is_official: bool = False,
        is_verified: bool = False,
        verified_at=None,
    ) -> dict[str, Any]:
        row_id = uuid4()
        self._execute(
            """
            INSERT INTO sources (
                id, name, source_type, organization, official_url, description,
                is_official, is_verified, verified_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                row_id, name, source_type, organization, official_url, description,
                is_official, is_verified, verified_at,
            ),
        )
        return self.get_by_id(row_id)  # type: ignore[return-value]

    def get_by_id(self, source_id) -> dict[str, Any] | None:
        return self._fetch_one("SELECT * FROM sources WHERE id = %s", (source_id,))

    def find_by_url(self, official_url: str) -> dict[str, Any] | None:
        return self._fetch_one(
            "SELECT * FROM sources WHERE official_url = %s", (official_url,)
        )

    def find_by_name_type(
        self, name: str, source_type: str
    ) -> dict[str, Any] | None:
        return self._fetch_one(
            "SELECT * FROM sources WHERE name = %s AND source_type = %s ORDER BY created_at LIMIT 1",
            (name, source_type),
        )

    def get_or_create(
        self,
        name: str,
        source_type: str,
        official_url: str | None = None,
        organization: str | None = None,
        description: str | None = None,
        is_official: bool = False,
        is_verified: bool = False,
        verified_at=None,
    ) -> tuple[dict[str, Any], bool]:
        existing = self.find_by_url(official_url) if official_url else None
        if existing is None and official_url is None:
            existing = self.find_by_name_type(name, source_type)
        if existing is not None:
            return existing, False
        source = self.create(
            name=name,
            source_type=source_type,
            official_url=official_url,
            organization=organization,
            description=description,
            is_official=is_official,
            is_verified=is_verified,
            verified_at=verified_at,
        )
        return source, True