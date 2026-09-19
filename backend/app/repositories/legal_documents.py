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

    def list_by_domain_ids(self, domain_ids: Sequence[Any]) -> list[dict[str, Any]]:
        """Fetch every document for the given domains in one query."""
        domain_ids = list(domain_ids)
        if not domain_ids:
            return []
        return self._fetch_all(
            "SELECT * FROM legal_documents WHERE domain_id = ANY(%s)",
            (domain_ids,),
        )

    def list_by_ids(self, doc_ids: Sequence[Any]) -> list[dict[str, Any]]:
        doc_ids = list(doc_ids)
        if not doc_ids:
            return []
        return self._fetch_all(
            "SELECT * FROM legal_documents WHERE id = ANY(%s)", (doc_ids,)
        )

    def list_by_titles(self, titles: Sequence[str]) -> list[dict[str, Any]]:
        """Fetch every document whose title matches any of ``titles``.

        Titles are not unique across domains (a law imported once per domain
        repeats its title), so callers filter on the returned id list.
        """
        titles = list(titles)
        if not titles:
            return []
        return self._fetch_all(
            "SELECT * FROM legal_documents WHERE title = ANY(%s)", (titles,)
        )

    def create_many(self, items: Sequence[dict[str, Any]]) -> None:
        """Insert several documents in one batch, ignoring existing rows."""
        if not items:
            return
        self._executemany(
            """
            INSERT INTO legal_documents (
                id, domain_id, title, short_title, document_type, jurisdiction,
                issuing_authority, official_source_url, language, effective_date,
                status, description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            [
                (
                    i.get("id") or uuid4(), i["domain_id"], i["title"],
                    i.get("short_title"), i["document_type"], i.get("jurisdiction"),
                    i.get("issuing_authority"), i.get("official_source_url"),
                    i.get("language"), i.get("effective_date"), i.get("status"),
                    i.get("description"),
                )
                for i in items
            ],
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