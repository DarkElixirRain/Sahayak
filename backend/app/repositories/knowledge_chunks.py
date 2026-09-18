"""Repository for knowledge_chunks (retrieval-ready legal knowledge)."""

from __future__ import annotations

from typing import Any, Sequence
from uuid import uuid4

from app.repositories.base import BaseRepository


class KnowledgeChunkRepository(BaseRepository):
    def create(
        self,
        document_id,
        content: str,
        provision_id=None,
        domain_id=None,
        source_id=None,
        title: str | None = None,
        language: str | None = None,
        chunk_index: int = 1,
        source_type: str | None = None,
        is_verified: bool = False,
        verified_at=None,
    ) -> dict[str, Any]:
        row_id = uuid4()
        self._execute(
            """
            INSERT INTO knowledge_chunks (
                id, document_id, provision_id, domain_id, source_id, title,
                content, language, chunk_index, source_type, is_verified, verified_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                row_id, document_id, provision_id, domain_id, source_id, title,
                content, language, chunk_index, source_type, is_verified, verified_at,
            ),
        )
        return self.get_by_id(row_id)  # type: ignore[return-value]

    def get_by_id(self, chunk_id) -> dict[str, Any] | None:
        return self._fetch_one(
            "SELECT * FROM knowledge_chunks WHERE id = %s", (chunk_id,)
        )

    def find_existing(
        self,
        document_id,
        provision_id,
        chunk_index: int | None,
        language: str | None,
    ) -> dict[str, Any] | None:
        return self._fetch_one(
            """
            SELECT * FROM knowledge_chunks
            WHERE document_id = %s
              AND provision_id IS NOT DISTINCT FROM %s
              AND chunk_index IS NOT DISTINCT FROM %s
              AND language IS NOT DISTINCT FROM %s
            """,
            (document_id, provision_id, chunk_index, language),
        )

    # --- retrieval helpers (plain relational queries; no RAG/embeddings) ---

    def find_by_domain(
        self,
        domain_id,
        verified_only: bool = True,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        verified = "AND c.is_verified = TRUE" if verified_only else ""
        return self._fetch_all(
            f"""
            SELECT c.*, d.title AS document_title, d.document_type
            FROM knowledge_chunks c
            JOIN legal_documents d ON d.id = c.document_id
            WHERE c.domain_id = %s {verified}
            ORDER BY d.title, c.chunk_index
            LIMIT %s
            """,
            (domain_id, limit),
        )

    def find_by_document(self, document_id) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT c.* FROM knowledge_chunks c
            WHERE c.document_id = %s ORDER BY c.chunk_index
            """,
            (document_id,),
        )

    def find_by_provision_number(
        self, document_id, provision_number: str
    ) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT c.*
            FROM knowledge_chunks c
            JOIN legal_provisions p ON p.id = c.provision_id
            WHERE c.document_id = %s AND p.provision_number = %s
            ORDER BY c.chunk_index
            """,
            (document_id, provision_number),
        )

    def find_verified(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT c.*, d.title AS document_title, d.document_type
            FROM knowledge_chunks c
            JOIN legal_documents d ON d.id = c.document_id
            WHERE c.is_verified = TRUE
            ORDER BY d.title, c.chunk_index
            LIMIT %s
            """,
            (limit,),
        )

    def search(
        self,
        domain_id=None,
        q: str | None = None,
        verified_only: bool = True,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []

        if verified_only:
            clauses.append("c.is_verified = TRUE")
        if domain_id is not None:
            clauses.append("c.domain_id = %s")
            params.append(domain_id)
        if q:
            clauses.append("(c.content ILIKE %s OR c.title ILIKE %s)")
            pattern = f"%{q}%"
            params.extend([pattern, pattern])

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)
        return self._fetch_all(
            f"""
            SELECT c.id, c.title AS chunk_title, c.content, c.language,
                   c.chunk_index, c.is_verified,
                   d.title AS document_title, d.document_type,
                   s.name AS source_name, s.official_url AS source_url
            FROM knowledge_chunks c
            JOIN legal_documents d ON d.id = c.document_id
            LEFT JOIN sources s ON s.id = c.source_id
            {where}
            ORDER BY d.title, c.chunk_index
            LIMIT %s
            """,
            params,
        )