"""Read-only knowledge API contracts."""

from uuid import UUID
from typing import Optional

from pydantic import BaseModel


class DomainOut(BaseModel):
    id: UUID
    key: str
    name: str
    description: Optional[str] = None
    is_active: bool


class KnowledgeChunkOut(BaseModel):
    id: UUID
    chunk_title: Optional[str] = None
    content: str
    language: Optional[str] = None
    chunk_index: Optional[int] = None
    is_verified: bool
    document_title: str
    document_type: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None