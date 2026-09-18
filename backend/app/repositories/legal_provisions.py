"""Repository for legal_provisions."""

from __future__ import annotations

from typing import Any, Sequence
from uuid import uuid4

from app.repositories.base import BaseRepository


class LegalProvisionRepository(BaseRepository):
    def create(
        self,
        document_id,
        text: str,
        provision_number: str | None = None,
        title: str | None = None,
        parent_id=None,
        language: str | None = None,
    ) -> dict[str, Any]:
        row_id = uuid4()
        self._execute(
            """
            INSERT INTO legal_provisions
                (id, document_id, parent_id, provision_number, title, text, language)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (row_id, document_id, parent_id, provision_number, title, text, language),
        )
        return self.get_by_id(row_id)  # type: ignore[return-value]

    def get_by_id(self, provision_id) -> dict[str, Any] | None:
        return self._fetch_one(
            "SELECT * FROM legal_provisions WHERE id = %s", (provision_id,)
        )

    def list_by_document(self, document_id) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT * FROM legal_provisions
            WHERE document_id = %s ORDER BY provision_number NULLS LAST
            """,
            (document_id,),
        )

    def find_by_number(
        self, document_id, provision_number: str
    ) -> dict[str, Any] | None:
        return self._fetch_one(
            """
            SELECT * FROM legal_provisions
            WHERE document_id = %s AND provision_number = %s
            """,
            (document_id, provision_number),
        )

    def get_or_create(
        self,
        document_id,
        text: str,
        provision_number: str | None = None,
        title: str | None = None,
        parent_id=None,
        language: str | None = None,
    ) -> tuple[dict[str, Any], bool]:
        if provision_number:
            existing = self.find_by_number(document_id, provision_number)
            if existing is not None:
                return existing, False
        provision = self.create(
            document_id=document_id,
            text=text,
            provision_number=provision_number,
            title=title,
            parent_id=parent_id,
            language=language,
        )
        return provision, True