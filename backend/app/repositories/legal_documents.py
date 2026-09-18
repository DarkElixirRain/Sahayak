"""Repository for legal_documents."""

from __future__ import annotations

from typing import Any, Sequence
from uuid import uuid4

from app.repositories.base import BaseRepository

DOCUMENT_TYPES = (
    "act", "code", "regulation", "rule", "directive",
    "procedure", "policy", "other",
)


class LegalDocumentRepository(BaseRepository):
    def create(
        self,
        domain_id,
        title: str,
        document_type: str,
        short_title: str | None = None,
        jurisdiction: str | None = None,
        issuing_authority: str | None = None,
        official_source_url: str | None = None,
        language: str | None = None,
        effective_date=None,
        status: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        row_id = uuid4()
        self._execute(
            """
            INSERT INTO legal_documents (
                id, domain_id, title, short_title, document_type, jurisdiction,
                issuing_authority, official_source_url, language, effective_date,
                status, description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                row_id, domain_id, title, short_title, document_type,
                jurisdiction, issuing_authority, official_source_url, language,
                effective_date, status, description,
            ),
        )
        return self.get_by_id(row_id)  # type: ignore[return-value]

    def get_by_id(self, doc_id) -> dict[str, Any] | None:
        return self._fetch_one(
            "SELECT * FROM legal_documents WHERE id = %s", (doc_id,)
        )

    def get_by_domain(self, domain_id) -> list[dict[str, Any]]:
        return self._fetch_all(
            "SELECT * FROM legal_documents WHERE domain_id = %s ORDER BY title",
            (domain_id,),
        )

    def find_by_title_type(
        self, domain_id, title: str, document_type: str
    ) -> dict[str, Any] | None:
        return self._fetch_one(
            """
            SELECT * FROM legal_documents
            WHERE domain_id = %s AND title = %s AND document_type = %s
            """,
            (domain_id, title, document_type),
        )

    def get_or_create(
        self,
        domain_id,
        title: str,
        document_type: str,
        **fields: Any,
    ) -> tuple[dict[str, Any], bool]:
        existing = self.find_by_title_type(domain_id, title, document_type)
        if existing is not None:
            return existing, False
        doc = self.create(domain_id=domain_id, title=title, document_type=document_type, **fields)
        return doc, True