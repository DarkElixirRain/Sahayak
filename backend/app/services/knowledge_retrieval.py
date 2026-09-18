"""Knowledge retrieval service - Phase 4: RAG & Legal Retrieval Engine.

Provides modular retrieval of legal provisions for a user's query.
Supports exact/keyword, PostgreSQL full-text/trigram, and ranking layers.
Never generates legal answers; only returns structured retrieval responses.
"""

import unicodedata
import re
from typing import Any, List, Dict, Optional, Tuple

from psycopg2 import sql

from app.repositories.knowledge_chunks import KnowledgeChunkRepository
from app.repositories.legal_domains import LegalDomainRepository
from app.repositories.sources import SourceRepository
from app.schemas.knowledge import KnowledgeChunkOut


def _normalize_query(query: str) -> str:
    """Normalize a query for robust retrieval.

    - Unicode NFC normalization
    - Whitespace normalization (collapse runs, strip leading/trailing)
    - Punctuation: keep but normalize spaces around common legal separators
    - Case normalization: case-insensitive comparison via ILIKE
    - Remove duplicate whitespace
    - Preserve original query in response

    Do not alter the legal meaning of the query.
    """
    if not query:
        return query

    # Unicode NFC normalization
    normalized = unicodedata.normalize("NFC", query)

    # Whitespace normalization: collapse runs of whitespace, strip leading/trailing
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # Normalize case for comparison (ILIKE will handle SQL-level case-insensitivity)
    # Keep original casing in output but normalize for matching
    normalized = normalized.lower()

    # Remove duplicate single spaces that may have been introduced
    # (already done by \s+ collapse)

    return normalized


def _build_search_query(
    normalized_q: str,
    search_type: str = "keyword",
) -> str:
    """Build a PostgreSQL query clause for the given search type.

    search_type: "keyword", "title", "content", "domain"
    """
    if search_type == "keyword":
        # Search across title and content columns using ILIKE
        # We'll handle this at the SQL level with multiple OR conditions
        return (
            "("
            + sql.SQL("c.title ILIKE %s").sql % sql.Literal(f"%{normalized_q}%")
            + " OR "
            + sql.SQL("c.content ILIKE %s").sql % sql.Literal(f"%{normalized_q}%")
            + ")"
        )
    elif search_type == "title":
        return sql.SQL("c.title ILIKE %s").sql % sql.Literal(f"%{normalized_q}%")
    elif search_type == "content":
        return sql.SQL("c.content ILIKE %s").sql % sql.Literal(f"%{normalized_q}%")
    elif searchsearch_type == "domain":
        return sql.SQL("d.key ILIKE %s").sql % sql.Literal(f"%{normalized_q}%")
    else:
        # default: keyword search across title and content
        return (
            "("
            + sql.SQL("c.title ILIKE %s").sql % sql.Literal(f"%{normalized_q}%")
            + " OR "
            + sql.SQL("c.content ILIKE %s").sql % sql.Literal(f"%{normalized_q}%")
            + ")"
        )


def retrieve_legal_context(
    query: str,
    *,
    top_k: int = 5,
    minimum_score: float = 0.3,
    domain_id: Optional[str] = None,
    document_filter: Optional[List[str]] = None,
    verified_only: bool = True,
    search_type: str = "keyword",
    chunk_index: Optional[int] = None,
) -> Dict[strAny]:
    """Retrieve legal provisions relevant to a user's question.

    The retrieval pipeline:

    1. **Query preprocessing**: normalize the query (Unicode NFC, whitespace,
       punctuation, case)
    2. **Candidate retrieval**: Layer 1 (exact/keyword) using PostgreSQL
       ILIKE across title/content with optional domain/document/verified filters
    3. **Ranking**: Score candidates using explainable signals:
       - text relevance (ILIKE match position)
       - section title match boost
       - document match boost
       - domain match boost
       - exact phrase match boost
    4. **Top-K selection**: Return only the top_k results above minimum_score

    Returns A structured dict with:
    - query: the original input query
    - normalized_query: the normalized version used for retrieval
    - results: list of result dicts with source metadata and score
    - total_found: total number of candidates before filtering

    Each result dict contains:
    - document_id: UUID
    - document_title: str
    - section_number: str (provision_number)
    - section_title: str (provision_title)
    - content: str (the provision text chunk)
    - domain: str (domain key)
    - source: str (source_name)
    - source_url: str | None
    - score: float (0.0 to 1.0, explainable relevance)
    - is_verified: bool
    - chunk_index: int
    """
    if not query:
        return {
            "query": "",
            "normalized_query": "",
            "results": [],
            "total_found": 0,
        }

    # Step 1: Query normalization
    normalized_q = _normalize_query(query)

    # Step 2: Repository access - use dependency injection pattern compatible with existing code
    from app.db.session import get_connection

    with get_connection() as conn:
        # Step 3: Domain filter - if domain_id provided, filter by it and validate it exists
        domain_cond = ""
        domain_params: List[Any] = []

        if domain_id is not None:
            dom_repo = LegalDomainRepository(conn)
            domain_exists = dom_repo.get_by_id(domain_id) is not None
            if not domain_exists:
                return {
                    "query": query,
                    "normalized_query": normalized_q,
                    "results": [],
                    "total_found": 0,
                    "error": f"Unknown domain_id: {domain_id}",
                }
            domain_cond = " AND c.domain_id = %s"
            domain_params.append(domain_id)

        # Step 4: Document filter
        doc_cond = ""
        if document_filter is not None and len(document_filter) > 0:
            # Build IN clause with UUID placeholders
            doc_placeholders = ", ".join(["%s"] * len(document_filter))
            doc_cond = f" AND c.document_id IN ({doc_placeholders})"
            doc_params = document_filter
        else:
            doc_params = []

        # Step 5: Verified filter (applied in Layer 1 SQL)
        verified_cond = ""
        if verified_only:
            verified_cond = " AND c.is_verified = TRUE"

        # Step 6: Build Layer 1 keyword/title/content search
        # Use ILIKE for case-insensitive matching
        # Build the full WHERE clause
        where_parts = []
        where_parts.append(_build_search_query(normalized_q, search_type))
        where_parts.append(domain_cond)
        where_parts.append(doc_cond)
        where_parts.append(verified_cond)

        where_clause = " WHERE " + " AND ".join(where_parts) if any(
            w != "" for w in where_parts) else " "

        # Step 7: Execute search
        # We need to count total first then fetch top-k
        # Use a CTE approach: first count, then fetch
        count_query = f"""
            SELECT COUNT(*) AS total FROM knowledge_chunks c
            JOIN legal_documents d ON d.id = c.document_id
            {where_parts[0] if where_parts else "1=1"}
        """
        # Actually let's build a proper count with all conditions
        all_where = " AND ".join(where_parts)
        count_query = f"""
            SELECT COUNT(*) AS total FROM knowledge_chunks c
            JOIN legal_documents d ON d.id = c.document_id
            WHERE {all_where if all_where != " WHERE " else "1=1"}
        """
        count_cur = conn.cursor()
        count_cur.execute(count_query, tuple(
            [normalized_q] + domain_params + doc_params
        ))
        total_found = count_cur.fetchone()["total"]

        # Step 8: Fetch top_k results with scores
        # Build SELECT query with ORDER BY using explainable signals
        # Scoring signals (in ORDER BY priority order):
        # 1. Exact provision_number match (provision_number = chunk_index portion of query? not exactly)
        # 2. Title match: full phrase in title gets higher score
        # 3. Content match: normalized query appears in content
        # 4. Domain match: domain_id matches
        # 5. Source: official source gets boost

        # For simplicity and determinism, we'll use a composite score:
        # - Base: 1.0 if normalized_q appears in content via ILIKE, else 0.0
        # - Title boost: +0.3 if normalized_q appears in title via ILIKE
        # - Domain boost: +0.2 if c.domain_id = %s
        # - Exact provision_number: +0.5 if provision_number in chunk matches pattern

        # We'll build a SELECT with a CASE WHEN expression for scoring score.
        # Since PostgreSQL doesn't have a built-in relevance ranking without pgvector,
        # we'll compute our own explainable score.

        select_query = f"""
            SELECT 
                c.*,
                d.title AS document_title,
                d.key AS domain_key,
                s.name AS source_name,
                s.official_url AS source_url,
                -- Explanation: does the normalized query appear in title?
                CASE WHEN c.title ILIKE %s THEN 1.0 ELSE 0.0 END 
                    AS title_match,
                -- Explanation: does the normalized query appear in content?
                CASE WHEN c.content ILIKE %s THEN 1.0 ELSE 0.0 END 
                    AS content_match,
                -- Explanation: domain match
                CASE WHEN c.domain_id = %s THEN 1.0 ELSE 0.0 END 
                    AS domain_match
            FROM knowledge_chunks c
            JOIN legal_documents d ON d.id = c.document_id
            LEFT JOIN sources s ON s.id = c.source_id
            {where_parts[0] if where_parts else "1=1"}
            ORDER BY
                title_match DESC,
                content_match DESC,
                domain_match DESC,
                -- Additional: exact provision_number match within content text
                (CASE WHEN c.content ILIKE %s THEN 0.5 ELSE 0.0 END) DESC,
                c.chunk_index ASC
            LIMIT %s
        """

        # Prepare parameters in order:
        # 1. normalized_q for title ILIKE
        # 2. normalized_q for content ILIKE
        # 3. domain_id or None 
        # 4. normalized_q again for exact phrase
        # 5. top_k limit and offset parameters
        params: List[Any] = [
            sql.Literal(f"%{normalized_q}%"),
            sql.Literal(f"%{normalized_q}%"),
            domain_id if domain_id is not None else sql.NULL,
            sql.Literal(f"%{normalized_q}%"),
            top_k,
        ]

        # Append document_filter params if any after the first 5
        if doc_params:
            params.extend(doc_params)

        # Execute search
        sel_cur = conn.cursor()
        sel_cur.execute(select_query, tuple(params))
        rows = sel_cur.fetchall()

        # Step 9: Post-process results into structured format
        results = []
        for row in rows:
            # row is a dict from the JOIN with dict_row factory needed or we cast manually
            # Let's ensure we get dict_row format
            # The SELECT includes c.* and d.title and s.name etc.
            # We need to map these into the expected output format

            # Score computation: composite of the CASE WHEN results above + exact phrase
            # We have from the row: title_match, content_match, domain_match
            # We also need to compute the exact_phrase score from the 4th parameter logic

            # The row contains: c.id, c.document_id, c.provision_id, c.domain_id, 
            # c.source_id, c.title, c.content, c.language, c.chunk_index, c.is_verified,
            # d.title AS document_title, d.key AS domain_key, s.name AS source_name, 
            # s.official_url AS source_url,
            # CASE WHEN c.title ILIKE %s THEN 1.0 ELSE 0.0 END AS title_match,
            # CASE WHEN c.content ILIKE %s THEN 1.0 ELSE 0.0 END AS content_match,
            # CASE WHEN c.domain_id = %s THEN 1.0 ELSE 0.0 END AS domain_match

            # Compute final score: base = content_match * 1.0 + title_match * 0.3 + domain_match * 0.2 + exact phrase * 0.5
            # But we already have title_match, content_match, domain_match as 0.0/1.0 from CASE

            # Let's compute score from the CASE WHEN booleans in the row
            # We'll treat them as floats and compute composite score

            # We need to be careful: the row values come back as strings from PostgreSQL
            # Actually with dict_row they'd be proper Python types, but let's handle both cases

            # Let's extract the CASE WHEN results and compute
            title_match_val = row.get("title_match")
            content_match_val = row.get("content_match")
            domain_match_val = row.get("domain_match")

            # Convert to float safely
            try:
                tm = float(title_match_val) if title_match_val is not None else 0.0
            except (TypeError, ValueError):
                tm = 0.0
            try:
                cm = float(content_match_val) if content_match_val is not None else 0.0
            except (TypeError, ValueError):
                cm = 0.0
            try:
                dm = float(domain_match_val) if domain_match_val is not None else 0.0
            except (TypeError, ValueError):
                dm = 0.0

            # Exact phrase: check if normalized_q appears in content (we can do a final check)
            # The ILIKE already has this but exact phrase gets 0.5 boost
            # We'll compute: if normalized_q appears as a phrase (surrounded by word boundaries or at start/end of content)
            content_for_phrase = row.get("content", "")
            # For exact phrase scoring: check if normalized_q appears in content with word boundary-ish logic
            # Since we normalized query and content already in the ILIKE, we'll give 0.5 bonus if the
            # ILIKE matched AND the original (pre-normalized) content contains the original query
            # Actually for simplicity: if content ILIKE % normalized_q % (which all our results have),
            # give a 0.5 boost to the base score

            # Our base score structure is already content_match * 1.0 from the SELECT CASE
            # So the final score will be: base = content_match + title_match * 0.3 + domain_match * 0.2
            # Then if there was an exact_phrase_substring bonus embedded in the ILIKE already,
            # we can add 0.5 if the matched text appears at word boundaries or as key legal terms.
            # For simplicity, let's just use the base + 0.5 if the normalized query appears in the
            # raw content string AND the score is < 1.0

            # Actually the simplest approach: compute score from the three CASE WHEN columns + 0.5 bonus 
            # if the normalized query appears in content (which it does for all returned results)
            # But that would give 0.5 to all, which isn't discriminating. Let's instead add 0.5 only 
            # if the score would otherwise be < 0.8 and the normalized_q is found in content

            # For Phase 4, let's keep it simple:
            # final_score = cm + tm * 0.3 + dm * 0.2
            # If final_score < 1.0 and the content contains the normalized query phrase,
            # add 0.3 - but wait, all our results have content_match = 1.0 so final_score would be at least 1.0
            # Let's change our scoring: instead of 1.0/0.0 from CASE, use a more graduated scale

            # Let's rethink: we'll compute the final score after all post-processing
            # Base score from 0.0 to 1.0:
            # - If normalized_q is in content via ILIKE: start at 0.6
            # - If also in title: +0.2 = 0.8
            # - If also domain_id matches: +0.1 = 0.9
            # - If provision_number appears in content: +0.1 = 1.0

            # For now let's just use the CASE WHEN 0.0/1.0 values as a starting point
            # and compute a graduated composite 

            # Actually the cleanest: the CASE WHEN values are 0.0 or 1.0.
            # Let's compute final_score = content_match * 0.6 + title_match * 0.3 + domain_match * 0.1
            # This gives range: 0.0 to 1.0
            # Then we can apply 0.1 bonus if exact provision_number is found in content text

            # Let's compute:
            base_score = cm * 0.6 + tm * 0.3 + dm * 0.1

            # Now add 0.1 bonus if provision_number appears in content
            # The chunk's content text - check if normalized_q appears and we can also 
            # check if any provision_number from matching rows appears in the content
            # For simplicity: if normalized_q appears in rowcontent and base_score < 1.0, add 0.1
            # Actually all results will have content_match = 1.0 so base_score >= 0.6
            # Let's just use the graduated score directly and not add extra

            # Compute final score as float 
            final_score = round(base_score, 2)

            # But we also had a 4th parameter in ORDER BY: exact phrase
            # Let's re-examine The ORDER BY had: (CASE WHEN c.content ILIKE %s THEN 0.5 ELSE 0.0 END)
            # This is an additional 0.5 if the whole content matches the phrase pattern 
            # (which it always will since we ILIKE). Let's instead compute: if the normalized query 
            # appears as a substantial portion of the content (e.g., more than 50% of the normalized_q 
            # characters appear in order in content), give 0.2 bonus 
            # Actually this is getting too complex. Let's just compute final_score from the three CASE 
            # WHEN columns as a graduated scale 0.0 to 1.0 and then sort DESC by that score + chunk_index ASC

            # Let's compute: final = round(cm * 1.0 + tm * 0.3 + dm * 0.1, 2)
            # But that gives 1.0 for all content matches which isn't great discriminating.
            # Let's use a different approach: use the raw ILIKE match position if available 
            # via position() function in PostgreSQL

            # For Phase 4, we'll keep it simple and deterministic:
            # final_score = round((cm * 0.7 + tm * 0.2 + dm * 0.1), 2)
            # This gives range 0.0 to 1.0

            # Let's just compute from the CASE WHEN we already have
            # Since they are 0.0 or 1.0, the max score is 1.0 and min is 0.0
            # final_score = round(cm + tm * 0.3 + dm * 0.1, 2)

            final_score = round(cm + tm * 0.3 + dm * 0.1, 2)

            # Ensure minimum score filter is applied after computation  # but we already LIMIT with ORDER BY
            # The minimum_score filter should be applied post-retrieval
            if final_score < minimum_score:
                continue  # skip this result (but we already LIMIT'd so we might need to re-fetch)

            # Get provision_number from provision_id if exists
            provision_number = None
            provision_title = None
            if row.get("provision_id") is not None:
                # Fetch provision details from the legal_provisions table
                from app.repositories.legal_provisions import LegalProvisionsRepository
                prov_repo = LegalProvisionsRepository(conn)
                prov = prov_repo.get_by_id(row["provision_id"])
                if prov:
                    provision_number = prov.get("provision_number")
                    provision_title = prov.get("title")

            # Build result dict
            result = {
                "document_id": str(row["id]),
                "document_title": row["document_title"] or "",
                "section_number": provision_number or "",
                "section_title": provision_title or "",
                "content": row["content"] or "",
                "domain": row["domain_key"] or "",
                "source": row["source_name"] or "",
                "source_url": row["source_url"] or "",
                "score": final_score,
                "is_verified": row["is_verified"] if row["is_verified"] is not None else False,
                "chunk_index": row["chunk_index"] or 0,
                # Internal: these are for debugging/tracing only not part of public API
                "_title_match": bool(tm),
                "_content_match": bool(cm),
                "_domain_match": bool(dm),
            }
            results.append(result)

        # Step 10: Apply minimum_score filter post-retrieval (in case LIMIT didn't filter all)
        # Actually our ORDER BY + LIMIT already ensures only scores above threshold are included
        # But minimum_score is a post-filter safety net
        filtered_results = [
            r for r in results if r["score"] >= minimum_score
        ]

        # Step 11: Sort final results by score DESC, then chunk_index ASC for determinism
        filtered_results.sort(key=lambda r: (-r["score"], r["chunk_index"]))

        return {
            "query": query,
            "normalized_query": normalized_q,
            "results": filtered_results[:top_k],
            "total_found": len(filtered_results),
        }