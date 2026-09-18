"""Read-only knowledge endpoints (Phase 2 & 4).

Phase 2: Basic search endpoints.
Phase 4: RAG / legal retrieval engine - POST /api/knowledge/retrieve
with structured response, multilingual support, ranking, and source traceability.
"""

from fastapi import APIRouter, HTTPException, Body

from app.db.session import get_connection
from app.repositories.knowledge_chunks import KnowledgeChunkRepository
from app.repositories.legal_domains import LegalDomainRepository
from app.schemas.knowledge import DomainOut, KnowledgeChunkOut
from app.services.knowledge_retrieval import retrieve_legal_context

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


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


@router.post("/retrieve", response_model=dict[str, Any])
def retrieve_legal_context(
    request: dict[str, Any] = Body(
        ...,
        description={
            "Input": {
                "query": "User legal question in Nepali or English or mixed",
                "top_k": "Number of results to return (default: 5)",
                "optional filters": [
                    "domain_id": "Filter by legal domain key",
                    "document_title": "Filter by document title",
                    "verified_only": "Only return verified content (default: True)",
                    "search_type": "Keyword title content domain (default: keyword)",
                    "minimum_score": "Minimum relevance score threshold (default: 0.3)",
                ],
                "examples": [
                    "मेरो पैतृक सम्पत्तिमा मेरो अधिकार के हो?",
                    "property partition",
                    "जग्गा dispute",
                    "divorce प्रक्रिया",
                ],
            }
        },
    ),
):
    """Retrieve legal provisions relevant to a user's legal question.

    This is a read-only retrieval endpoint that returns structured legal provisions
    from the database. It does NOT generate legal advice, answers, or guidance.

    The retrieval pipeline:
    1. Query preprocessing: Unicode NFC normalization + whitespace + case normalization
    2. Candidate retrieval: PostgreSQL ILIKE across title and content with optional filters
    3. Ranking: Explainable composite score (title match + content match + domain match)
    4. Top-K selection: Return only top_k results above minimum_score

    Returns structured records with full source traceability:
    - document_id, document_title, section_number, section_title
    - content, domain, source, source_url
    - score (0.0 to 1.0, explainable relevance signals)
    - is_verified: bool

    Never returns anonymous legal text - every result traces back to a source row.
    """
    query = request.get("query", "")
    top_k = request.get("top_k", 5)
    domain_id = request.get("domain_id")
    document_title = request.get("document_title")
    verified_only = request.get("verified_only", True)
    search_type = request.get("search_type", "keyword")
    minimum_score = request.get("minimum_score", 0.3)

    # Validate inputs
    if not isinstance(query, str):
        raise HTTPException(status_code=422, detail="query must be a string")
    top_k = max(1, min(top_k, 50))
    minimum_score = max(0.0, min(1.0, minimum_score))

    result = retrieve_legal_context(
        query=query,
        top_k=top_k,
        minimum_score=minimum_score,
        domain_id=domain_id,
        document_filter=[document_title] if document_title else None,
        verified_only=verified_only,
        search_type=search_type,
    )

    if result["total_found"] == 0 and query:
        # Return empty results rather than error - retrieval is best-effort
        return {
            "query": query,
            "normalized_query": result["normalized_query"],
            "results": [],
            "total_found": 0,
        }

    return result