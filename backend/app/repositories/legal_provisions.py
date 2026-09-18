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

    def list_by_document_ids(
        self, document_ids: Sequence[Any]
    ) -> list[dict[str, Any]]:
        """Fetch every provision for the given documents in one query."""
        document_ids = list(document_ids)
        if not document_ids:
            return []
        return self._fetch_all(
            "SELECT * FROM legal_provisions WHERE document_id = ANY(%s)",
            (document_ids,),
        )

    def create_many(self, items: Sequence[dict[str, Any]]) -> None:
        """Insert several provisions in one batch."""
        if not items:
            return
        self._executemany(
            """
            INSERT INTO legal_provisions
                (id, document_id, parent_id, provision_number, title, text, language)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    i["id"], i["document_id"], i.get("parent_id"),
                    i.get("provision_number"), i.get("title"), i["text"],
                    i.get("language"),
                )
                for i in items
            ],
        )

    def update_text_many(self, updates: Sequence[tuple[str, Any, Any]]) -> None:
        """Refresh ``(text, title, id)`` triples in one batch.

        Only ever called for provisions whose stored legal text actually
        differs from the validated dataset; ids are preserved so dependent
        knowledge chunks keep pointing at the same provision.
        """
        if not updates:
            return
        self._executemany(
            """
            UPDATE legal_provisions
            SET text = %s, title = %s, updated_at = now()
            WHERE id = %s
            """,
            list(updates),
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
                # Keep stored legal text in sync with the validated dataset:
                # an existing provision must never keep stale text after a
                # re-import of corrected source data (e.g. Phase 3B output).
                if existing.get("text") != text or existing.get("title") != title:
                    self._execute(
                        """
                        UPDATE legal_provisions SET
                            text = %s, title = %s, updated_at = now()
                        WHERE id = %s
                        """,
                        (text, title, existing["id"]),
                    )
                    existing = self.get_by_id(existing["id"]) or existing
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