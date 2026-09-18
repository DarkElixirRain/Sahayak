"""Repository for government_resources."""

from __future__ import annotations

from typing import Any, Sequence
from uuid import uuid4

from psycopg.types.json import Jsonb

from app.repositories.base import BaseRepository


class GovernmentResourceRepository(BaseRepository):
    def create(
        self,
        title: str,
        domain_id=None,
        description: str | None = None,
        authority_name: str | None = None,
        service_name: str | None = None,
        instructions: str | None = None,
        required_documents: list | dict | None = None,
        contact_information: list | dict | None = None,
        official_url: str | None = None,
        source_id=None,
        is_verified: bool = False,
        verified_at=None,
    ) -> dict[str, Any]:
        row_id = uuid4()
        self._execute(
            """
            INSERT INTO government_resources (
                id, domain_id, title, description, authority_name, service_name,
                instructions, required_documents, contact_information, official_url,
                source_id, is_verified, verified_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                row_id, domain_id, title, description, authority_name, service_name,
                instructions,
                Jsonb(required_documents) if required_documents is not None else None,
                Jsonb(contact_information) if contact_information is not None else None,
                official_url,
                source_id, is_verified, verified_at,
            ),
        )
        return self.get_by_id(row_id)  # type: ignore[return-value]

    def get_by_id(self, resource_id) -> dict[str, Any] | None:
        return self._fetch_one(
            "SELECT * FROM government_resources WHERE id = %s", (resource_id,)
        )

    def find_by_domain(
        self, domain_id, verified_only: bool = True
    ) -> list[dict[str, Any]]:
        verified = "AND is_verified = TRUE" if verified_only else ""
        return self._fetch_all(
            f"SELECT * FROM government_resources WHERE domain_id = %s {verified} ORDER BY title",
            (domain_id,),
        )