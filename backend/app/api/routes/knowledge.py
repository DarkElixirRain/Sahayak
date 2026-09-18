"""Read-only knowledge endpoints (Phase 2).

These endpoints only expose verified-safe metadata and retrieval for future
use. They are NOT legal-advice endpoints and never generate guidance.
"""

from fastapi import APIRouter, HTTPException

from app.db.session import get_connection
from app.repositories.knowledge_chunks import KnowledgeChunkRepository
from app.repositories.legal_domains import LegalDomainRepository
from app.schemas.knowledge import DomainOut, KnowledgeChunkOut

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/domains", response_model=list[DomainOut])
def list_domains(active_only: bool = True):
    with get_connection() as conn:
        return LegalDomainRepository(conn).list(active_only=active_only)


@router.get("/search", response_model=list[KnowledgeChunkOut])
def search_knowledge(
    domain: str | None = None,
    q: str | None = None,
    verified: bool = True,
    limit: int = 20,
):
    limit = max(1, min(limit, 100))
    rows: list = []
    unknown_domain = False
    domain_id = None
    with get_connection() as conn:
        if domain:
            domain_row = LegalDomainRepository(conn).get_by_key(domain)
            unknown_domain = domain_row is None
            if not unknown_domain:
                domain_id = domain_row["id"]
        if not unknown_domain:
            rows = KnowledgeChunkRepository(conn).search(
                domain_id=domain_id,
                q=q,
                verified_only=verified,
                limit=limit,
            )
    if unknown_domain:
        raise HTTPException(status_code=404, detail=f"Unknown domain: {domain}")
    return rows