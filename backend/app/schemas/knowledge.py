"""Read-only knowledge API contracts."""

from uuid import UUID

from pydantic import BaseModel


class DomainOut(BaseModel):
    id: UUID
    key: str
    name: str
    description: str | None = None
    is_active: bool


class KnowledgeChunkOut(BaseModel):
    id: UUID
    chunk_title: str | None = None
    content: str
    language: str | None = None
    chunk_index: int | None = None
    is_verified: bool
    document_title: str
    document_type: str | None = None
    source_name: str | None = None
    source_url: str | None = None