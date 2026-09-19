"""Knowledge endpoints (Phase 2 read-only + Phase 4 retrieval).

Phase 2: `GET /api/knowledge/domains`, `GET /api/knowledge/search`
Phase 4: `POST /api/knowledge/retrieve` — structured, ranked, source-traceable
retrieval of legal provisions.

The router prefix is `/knowledge`: the application mounts this router under the
global `/api` prefix (``app.include_router(api_router, prefix="/api")``), so
adding `/api` here would produce `/api/api/knowledge/...`.

None of these endpoints gives legal advice. They only return stored, sourced
legal content and metadata.
"""

from typing import Any, Optional

from fastapi import APIRouter, Body, HTTPException

from app.core.exceptions import ApiError
from app.db.session import get_connection
from app.repositories.knowledge_chunks import KnowledgeChunkRepository
from app.repositories.legal_domains import LegalDomainRepository
from app.schemas.knowledge import DomainOut, KnowledgeChunkOut
from app.services.knowledge_retrieval import (
    DEFAULT_SEARCH_TYPE,
    MAX_QUERY_LENGTH,
    MAX_SCORE,
    SEARCH_TYPES,
    retrieve_legal_context,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

TOP_K_MAX = 50


@router.get("/domains", response_model=list[DomainOut])
def list_domains(active_only: bool = True):
    with get_connection() as conn:
        return LegalDomainRepository(conn).list(active_only=active_only)


@router.get("/search", response_model=list[KnowledgeChunkOut])
def search_knowledge(
    domain: Optional[str] = None,
    q: Optional[str] = None,
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
def retrieve_knowledge(
    request: dict[str, Any] = Body(
        ...,
        description={
            "Input": {
                "query": "User legal question in Nepali, English or mixed",
                "top_k": f"Number of results to return (default: 5, max: {TOP_K_MAX})",
                "optional filters": {
                    "domain_id": "Filter by legal domain key (or UUID)",
                    "document_title": "Filter by document title (or document UUID)",
                    "verified_only": "Only return verified content (default: True)",
                    "search_type": (
                        "One of: " + ", ".join(SEARCH_TYPES) + " (default: keyword)"
                    ),
                    "minimum_score": (
                        f"Minimum relevance score, 0.0 to {MAX_SCORE} (default: 0.3)"
                    ),
                },
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

    Read-only retrieval: returns structured legal provisions from the database.
    It does NOT generate legal advice, answers, or guidance.

    Pipeline:

    1. Query preprocessing — Unicode NFC normalization, whitespace collapse
    2. Candidate retrieval — parameterized ILIKE across title / content / domain
       with optional domain, document, verification and chunk-index filters
    3. Ranking — explainable composite score
       (`content_match * 1.0 + title_match * 0.3 + domain_match * 0.1`)
    4. Selection — drop results below `minimum_score`, return the top `top_k`

    Every result carries full source traceability: `document_id`,
    `document_title`, `section_number`, `section_title`, `content`, `domain`,
    `source`, `source_url`, `score`, `is_verified`, `chunk_index`. Anonymous
    legal text is never returned.
    """
    query = request.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ApiError(
            "VALIDATION_ERROR", "query must be a non-empty string.", 422
        )
    if len(query) > MAX_QUERY_LENGTH:
        raise ApiError(
            "VALIDATION_ERROR",
            f"query must be at most {MAX_QUERY_LENGTH} characters.",
            422,
        )

    top_k = request.get("top_k", 5)
    if isinstance(top_k, bool) or not isinstance(top_k, int):
        raise ApiError("VALIDATION_ERROR", "top_k must be an integer.", 422)
    top_k = max(1, min(top_k, TOP_K_MAX))

    minimum_score = request.get("minimum_score", 0.3)
    if isinstance(minimum_score, bool) or not isinstance(minimum_score, (int, float)):
        raise ApiError("VALIDATION_ERROR", "minimum_score must be a number.", 422)
    minimum_score = max(0.0, min(float(minimum_score), MAX_SCORE))

    search_type = request.get("search_type", DEFAULT_SEARCH_TYPE)
    if not isinstance(search_type, str) or search_type not in SEARCH_TYPES:
        raise ApiError(
            "VALIDATION_ERROR",
            "search_type must be one of: " + ", ".join(SEARCH_TYPES) + ".",
            422,
        )

    domain_id = request.get("domain_id")
    if domain_id is not None and not isinstance(domain_id, str):
        raise ApiError("VALIDATION_ERROR", "domain_id must be a string.", 422)

    document_title = request.get("document_title")
    if document_title is not None and not isinstance(document_title, str):
        raise ApiError(
            "VALIDATION_ERROR", "document_title must be a string.", 422
        )

    verified_only = request.get("verified_only", True)
    if not isinstance(verified_only, bool):
        raise ApiError("VALIDATION_ERROR", "verified_only must be a boolean.", 422)

    result = retrieve_legal_context(
        query=query,
        top_k=top_k,
        minimum_score=minimum_score,
        domain_id=domain_id,
        document_filter=[document_title] if document_title else None,
        verified_only=verified_only,
        search_type=search_type,
    )

    # Unknown domain / unusable document filter is a client error, matching
    # the 404 semantics of GET /knowledge/search for an unknown domain.
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])

    return result
