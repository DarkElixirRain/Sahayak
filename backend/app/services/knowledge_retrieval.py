"""Knowledge retrieval service - Phase 4 legal retrieval engine.

Retrieval is **deterministic lexical matching**: the query is Unicode-NFC
normalized, whitespace-collapsed, tokenized, stripped of stop words, and each
remaining term is matched with PostgreSQL ``ILIKE`` against the chunk title,
the chunk content and (for ``search_type="domain"``) the domain key. Matches are
ranked with an explainable per-term weighted sum and then filtered by
``minimum_score`` and ``top_k``.

Why not full-text search or embeddings (documented decision, not an omission):

* PostgreSQL ships no Nepali text-search configuration. With ``simple`` or
  ``english``, Devanagari text degenerates to one lexeme per whitespace word, so
  ``tsvector`` buys prefix/stemming behaviour that does not apply here, while
  requiring a generated column plus GIN index (a schema migration).
* There is no embedding column on ``knowledge_chunks`` (see migration 005) and
  introducing pgvector would add an infrastructure dependency plus a corpus-wide
  re-embedding job, for a 721-row hand-verified corpus.

So this stays plain relational matching on the project's psycopg 3 connection,
which keeps it deterministic, dependency-free and testable. This service never
generates legal answers; it only returns structured, source-traceable results.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import UUID

from psycopg.rows import dict_row

from app.db.session import get_connection
from app.repositories.legal_documents import LegalDocumentRepository
from app.repositories.legal_domains import LegalDomainRepository

# Explainable ranking weights. Every signal is a *ratio* of the query terms
# that matched, so a single-term query scores exactly as before
# (content 1.0, +0.3 title, +0.1 domain) and the ceiling is unchanged.
CONTENT_WEIGHT = 1.0
TITLE_WEIGHT = 0.3
DOMAIN_WEIGHT = 0.1
MAX_SCORE = CONTENT_WEIGHT + TITLE_WEIGHT + DOMAIN_WEIGHT

SEARCH_TYPES: Tuple[str, ...] = ("keyword", "title", "content", "domain")
DEFAULT_SEARCH_TYPE = "keyword"

# Retrieval outcome, so "no match", "matches exist but are unverified" and
# "error" can never be collapsed into one indistinguishable empty response.
STATUS_OK = "ok"
STATUS_NO_MATCH = "no_match"
STATUS_UNVERIFIED_ONLY = "unverified_only"
STATUS_ERROR = "error"

MAX_QUERY_TOKENS = 24

# Upper bound on an accepted question, enforced by the API layer. Keeps a
# pathological request from turning into thousands of LIKE comparisons.
MAX_QUERY_LENGTH = 2000

# Stop words are dropped only to reduce noise: a query that is nothing but stop
# words falls back to its raw tokens rather than matching nothing at all.
STOP_WORDS: frozenset[str] = frozenset(
    {
        # Nepali
        "को", "का", "की", "के", "मा", "ले", "लाई", "बाट", "द्वारा", "सँग",
        "छ", "छन्", "छु", "हो", "हुन्", "हुन", "हुन्छ", "थियो", "थिए", "गर्न",
        "गर्ने", "गरे", "गरेको", "भए", "भएको", "भन्ने", "भने", "अब", "मलाई",
        "मेरो", "मेरा", "मैले", "तपाईं", "तिमी", "यो", "त्यो", "यी", "ती",
        "र", "वा", "पनि", "तर", "कसरी", "किन", "कहिले", "कुन", "कहाँ", "कति",
        "लागि", "बारे", "जस्तो", "जस्तै", "अनि", "हुँदा", "भयो", "गर्नु",
        "पर्छ", "पर्यो", "हुने", "गर्छ", "दिन", "दिनु", "सक्छ", "सक्छु",
        # English
        "the", "a", "an", "and", "or", "but", "if", "then", "is", "are",
        "was", "were", "be", "been", "being", "to", "of", "in", "on", "at",
        "for", "with", "by", "from", "as", "this", "that", "these", "those",
        "my", "your", "his", "her", "our", "their", "i", "me", "we", "you",
        "he", "she", "it", "they", "them", "do", "does", "did", "done",
        "how", "what", "when", "where", "why", "which", "who", "can", "could",
        "will", "would", "shall", "should", "must", "not", "no", "yes",
        "have", "has", "had", "about", "into", "there", "here", "so", "than",
    }
)

# Token characters: word characters of any script plus the Devanagari block.
#
# ``\w`` alone is NOT enough for Nepali: it matches letters and digits but not
# the combining marks (matras / virama), so "संरक्षक" would be split into
# "रक" and "षक". The Devanagari ranges below cover the combining marks, and
# deliberately exclude the dandas (\u0964 \u0965) and the abbreviation sign
# (\u0970), which are punctuation and must separate terms. ZWNJ/ZWJ (\u200c
# \u200d) are kept so words joined by them stay single terms.
_DEVANAGARI_WORD = "\u0900-\u0963\u0966-\u096f\u0971-\u097f"
_TOKEN_RE = re.compile(
    rf"[\w{_DEVANAGARI_WORD}\u200c\u200d]+", re.UNICODE
)


def _normalize_query(query: str) -> str:
    """Normalize a query for robust retrieval.

    - Unicode NFC normalization
    - Whitespace normalization (collapse runs, strip leading/trailing)
    - Case normalization (lowercase; ILIKE also matches case-insensitively)

    The legal meaning of the query is never altered and the original query is
    still returned untouched in the response.
    """
    if not query:
        return query

    # Unicode NFC normalization
    normalized = unicodedata.normalize("NFC", query)

    # Whitespace normalization: collapse runs of whitespace, strip edges
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # Case normalization for matching (ILIKE is case-insensitive anyway)
    normalized = normalized.lower()

    return normalized


def tokenize_query(query: str, *, limit: int = MAX_QUERY_TOKENS) -> List[str]:
    """Split a query into distinct, meaningful search terms.

    Order is preserved (strongest signal first, as written by the user) and
    duplicates are removed so a repeated word cannot inflate the score.
    """
    normalized = _normalize_query(query or "")
    if not normalized:
        return []

    # Strip stray underscores that ``\w`` allows.
    raw = [token.strip("_") for token in _TOKEN_RE.findall(normalized)]
    raw = [token for token in raw if token]
    meaningful = [
        token
        for token in raw
        if token not in STOP_WORDS and (len(token) > 1 or token.isdigit())
    ]
    # A query made only of stop words / punctuation still has to search
    # something, so fall back to the raw tokens and finally the whole string.
    fallback = [t for t in raw if len(t) > 1 or t.isdigit()] or [normalized]
    tokens = meaningful or fallback

    deduped = list(dict.fromkeys(tokens))
    return deduped[:limit]


def _like_pattern(value: Any) -> str:
    """Build a LIKE pattern with any metacharacters in the input escaped.

    ``%`` and ``_`` are LIKE wildcards, so an unescaped query of ``%`` would
    match the entire corpus. A backslash is PostgreSQL's default LIKE escape
    character, so escaping each metacharacter is sufficient. Staying inside a
    bound parameter also means SQL injection is impossible by construction.
    """
    escaped = (
        str(value).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )
    return f"%{escaped}%"


def _build_search_clause(
    normalized_q: str, search_type: str
) -> Tuple[str, List[Any]]:
    """Return ``(sql_predicate, params)`` matching ONE term (or phrase).

    ``search_type`` is one of ``title``, ``content``, ``domain`` or
    ``keyword`` (the default, matching title *or* content). Unknown values fall
    back to ``keyword`` rather than raising, so a caller can never produce a
    malformed WHERE clause.
    """
    pattern = _like_pattern(normalized_q)

    if search_type == "title":
        return "c.title ILIKE %s", [pattern]
    if search_type == "content":
        return "c.content ILIKE %s", [pattern]
    if search_type == "domain":
        # The domain key lives on legal_domains (dm), not on legal_documents.
        return "dm.key ILIKE %s", [pattern]
    return "(c.title ILIKE %s OR c.content ILIKE %s)", [pattern, pattern]


def _build_match_predicate(
    tokens: Iterable[str], search_type: str
) -> Tuple[str, List[Any]]:
    """OR the per-term clauses together, so any term may match."""
    clauses: List[str] = []
    params: List[Any] = []
    for token in tokens:
        clause, clause_params = _build_search_clause(
            token,
            search_type if search_type in SEARCH_TYPES else DEFAULT_SEARCH_TYPE,
        )
        clauses.append(clause)
        params.extend(clause_params)
    if not clauses:
        # Unreachable for a non-empty token list; kept so the WHERE clause can
        # never become empty (which would scan the whole table).
        return "(c.title ILIKE %s OR c.content ILIKE %s)", ["%%", "%%"]
    # Always wrap the entire disjunction in parentheses to protect against AND precedence.
    # SQL gives AND higher precedence than OR, so an unwrapped predicate would
    # silently change meaning when the caller appends another condition:
    #
    #   a OR b OR c AND c.is_verified = TRUE   ->  a OR b OR (c AND verified)
    #
    # which would let unverified rows through a `verified_only` request. The
    # filter must never depend on the shape of the generated expression.
    return f"({' OR '.join(clauses)})", params


def _build_hit_expression(column: str, tokens: List[str]) -> str:
    """SQL counting how many distinct query terms appear in ``column``."""
    return " + ".join(
        f"CASE WHEN {column} ILIKE %s THEN 1 ELSE 0 END" for _ in tokens
    )


def _looks_like_uuid(value: Any) -> bool:
    try:
        UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return False
    return True


def _resolve_domain(conn: Any, value: Any) -> Optional[dict[str, Any]]:
    """Resolve a domain filter given either its stable key or its UUID."""
    repo = LegalDomainRepository(conn)
    if isinstance(value, str) and not _looks_like_uuid(value):
        return repo.get_by_key(value)
    found = repo.get_by_id(value)
    if found is None and isinstance(value, str):
        return repo.get_by_key(value)
    return found


def _resolve_document_ids(conn: Any, values: List[Any]) -> List[Any]:
    """Resolve a document filter given UUIDs and/or document titles.

    Titles are not unique across domains (the same law is imported once per
    domain), so a title filter deliberately matches every document with that
    title.
    """
    repo = LegalDocumentRepository(conn)
    ids: List[Any] = []
    titles: List[str] = []

    for value in values:
        if _looks_like_uuid(value):
            doc = repo.get_by_id(value)
            if doc is not None:
                ids.append(doc["id"])
        else:
            titles.append(str(value))

    if titles:
        for doc in repo.list_by_titles(titles):
            if doc["id"] not in ids:
                ids.append(doc["id"])

    return ids


def _empty_result(
    query: str, normalized_q: str, *, status: str, error: str | None = None,
    tokens: Optional[List[str]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "query": query,
        "normalized_query": normalized_q,
        "tokens": tokens or [],
        "results": [],
        "total_found": 0,
        "status": status,
    }
    if error:
        payload["error"] = error
    return payload


def retrieve_legal_context(
    query: str,
    *,
    top_k: int = 5,
    minimum_score: float = 0.3,
    domain_id: Optional[str] = None,
    document_filter: Optional[List[str]] = None,
    verified_only: bool = True,
    search_type: str = DEFAULT_SEARCH_TYPE,
    chunk_index: Optional[int] = None,
) -> Dict[str, Any]:
    """Retrieve legal provisions relevant to a user's question.

    Pipeline:

    1. **Query preprocessing** — Unicode NFC, whitespace collapse, lowercasing,
       tokenization, stop-word removal
    2. **Candidate retrieval** — one parameterized query; a row is a candidate
       when ANY query term matches (per ``search_type``), with optional domain /
       document / verified / chunk-index filters
    3. **Ranking** — explainable composite score computed identically in SQL and
       in Python: ``(content_hits / terms) * 1.0 + (title_hits / terms) * 0.3 +
       domain_match * 0.1`` (range ``0.0 .. 1.4``)
    4. **Selection** — drop anything below ``minimum_score``, order by score
       descending (ties broken by ``chunk_index`` then ``id`` for full
       determinism) and slice to ``top_k``

    Returns a dict with ``query``, ``normalized_query``, ``tokens``, ``results``,
    ``total_found`` and ``status``. ``status`` distinguishes:

    * ``ok``               — verified matches were found
    * ``unverified_only``  — nothing verified matched, but unverified matches
                             exist (``unverified_match_count`` is set)
    * ``no_match``         — nothing matched at all
    * ``error``            — an unresolvable domain/document filter

    Every result carries full source traceability: ``chunk_id``,
    ``document_id``, ``provision_id``, ``document_title``, ``section_number``,
    ``section_title``, ``content``, ``domain``, ``source``, ``source_url``,
    ``score``, ``is_verified`` and ``chunk_index``. Anonymous legal text is never
    returned.
    """
    if not query:
        return _empty_result(query, "", status=STATUS_NO_MATCH)

    normalized_q = _normalize_query(query)
    tokens = tokenize_query(query)

    if not tokens:
        return _empty_result(query, normalized_q, status=STATUS_NO_MATCH)

    token_patterns = [_like_pattern(token) for token in tokens]

    with get_connection() as conn:
        conditions: List[str] = []
        params: List[Any] = []

        # --- term matching (keyword / title / content / domain) ------------
        search_predicate, search_params = _build_match_predicate(tokens, search_type)
        conditions.append(search_predicate)
        params.extend(search_params)

        # --- domain filter (accepts a domain key or a UUID) ---------------
        domain_row = None
        if domain_id is not None:
            domain_row = _resolve_domain(conn, domain_id)
            if domain_row is None:
                return _empty_result(
                    query, normalized_q, status=STATUS_ERROR,
                    error=f"Unknown domain_id: {domain_id}", tokens=tokens,
                )
            conditions.append("c.domain_id = %s")
            params.append(domain_row["id"])

        # --- document filter (accepts UUIDs and/or document titles) -------
        if document_filter:
            document_ids = _resolve_document_ids(conn, list(document_filter))
            if not document_ids:
                return _empty_result(
                    query, normalized_q, status=STATUS_NO_MATCH, tokens=tokens
                )
            conditions.append("c.document_id = ANY(%s)")
            params.append(document_ids)

        # --- optional chunk index filter ----------------------------------
        if chunk_index is not None:
            conditions.append("c.chunk_index = %s")
            params.append(chunk_index)

        # Verified filtering is applied per query so the same base query can
        # also answer "do unverified matches exist?".
        verified_condition = "c.is_verified = TRUE" if verified_only else None

        token_count = len(tokens)
        title_hits = _build_hit_expression("c.title", tokens)
        content_hits = _build_hit_expression("c.content", tokens)
        domain_match = "CASE WHEN c.domain_id = %s THEN 1.0 ELSE 0.0 END"

        # Parameters for the inner SELECT, in SQL-text order: title hits,
        # content hits, domain match — then the WHERE-clause filters.
        scoring_params: List[Any] = [
            *token_patterns,                                       # title hits
            *token_patterns,                                       # content hits
            domain_row["id"] if domain_row else None,              # domain_match
        ]

        score_expr = (
            f"(content_hits::numeric / {token_count}) * {CONTENT_WEIGHT} "
            f"+ (title_hits::numeric / {token_count}) * {TITLE_WEIGHT} "
            f"+ domain_match * {DOMAIN_WEIGHT}"
        )

        def _inner_sql(extra_conditions: List[str]) -> str:
            where_sql = " AND ".join([*conditions, *extra_conditions])
            return f"""
            SELECT
                c.id AS chunk_id,
                c.document_id,
                c.provision_id,
                c.domain_id,
                c.source_id,
                c.title,
                c.content,
                c.language,
                c.chunk_index,
                c.is_verified,
                d.title AS document_title,
                dm.key AS domain_key,
                s.name AS source_name,
                s.official_url AS source_url,
                s.source_type AS source_type,
                s.is_verified AS source_is_verified,
                s.verified_at AS source_verified_at,
                d.status AS document_status,
                d.effective_date AS document_effective_date,
                p.provision_number,
                p.title AS provision_title,
                ({title_hits}) AS title_hits,
                ({content_hits}) AS content_hits,
                ({domain_match}) AS domain_match
            FROM knowledge_chunks c
            JOIN legal_documents d ON d.id = c.document_id
            LEFT JOIN legal_domains dm ON dm.id = c.domain_id
            LEFT JOIN sources s ON s.id = c.source_id
            LEFT JOIN legal_provisions p ON p.id = c.provision_id
            WHERE {where_sql}
            """

        primary_conditions = [verified_condition] if verified_condition else []
        primary_sql = _inner_sql(primary_conditions)
        primary_params = [*scoring_params, *params]

        with conn.cursor(row_factory=dict_row) as cur:
            # total matches at/above the threshold, before slicing to top_k
            cur.execute(
                f"""
                SELECT count(*) AS total
                FROM ({primary_sql}) scored
                WHERE ({score_expr}) >= %s
                """,
                (*primary_params, minimum_score),
            )
            total_row = cur.fetchone()
            total_found = int(total_row["total"]) if total_row else 0

            if total_found == 0:
                # Distinguish "nothing matched" from "unverified matches exist".
                unverified_count = 0
                if verified_only:
                    cur.execute(
                        f"""
                        SELECT count(*) AS total
                        FROM ({_inner_sql([])}) scored
                        WHERE ({score_expr}) >= %s
                        """,
                        (*scoring_params, *params, minimum_score),
                    )
                    diagnostic = cur.fetchone()
                    unverified_count = int(diagnostic["total"]) if diagnostic else 0

                payload = _empty_result(
                    query, normalized_q,
                    status=(STATUS_UNVERIFIED_ONLY if unverified_count
                            else STATUS_NO_MATCH),
                    tokens=tokens,
                )
                payload["verified_only"] = verified_only
                payload["unverified_match_count"] = unverified_count
                return payload

            cur.execute(
                f"""
                SELECT *
                FROM ({primary_sql}) scored
                WHERE ({score_expr}) >= %s
                ORDER BY ({score_expr}) DESC, chunk_index ASC, chunk_id ASC
                LIMIT %s
                """,
                (*primary_params, minimum_score, top_k),
            )
            rows = cur.fetchall()

        results: List[Dict[str, Any]] = []
        for row in rows:
            tm = int(row["title_hits"] or 0)
            cm = int(row["content_hits"] or 0)
            dm = float(row["domain_match"] or 0.0)
            score = round(
                (cm / token_count) * CONTENT_WEIGHT
                + (tm / token_count) * TITLE_WEIGHT
                + dm * DOMAIN_WEIGHT,
                2,
            )

            results.append(
                {
                    "chunk_id": str(row["chunk_id"]),
                    "document_id": str(row["document_id"]),
                    "provision_id": (
                        str(row["provision_id"]) if row["provision_id"] else None
                    ),
                    "document_title": row["document_title"] or "",
                    "section_number": row["provision_number"] or "",
                    "section_title": row["provision_title"] or "",
                    "content": row["content"] or "",
                    "domain": row["domain_key"] or "",
                    "source": row["source_name"] or "",
                    "source_url": row["source_url"] or "",
                    "source_id": str(row["source_id"]) if row["source_id"] else None,
                    "source_type": row["source_type"] or "",
                    "source_is_verified": bool(row["source_is_verified"]),
                    "source_verified_at": (
                        row["source_verified_at"].isoformat()
                        if row["source_verified_at"] else None
                    ),
                    "document_status": row["document_status"] or "",
                    "document_effective_date": (
                        str(row["document_effective_date"])
                        if row["document_effective_date"] else None
                    ),
                    "score": score,
                    "is_verified": bool(row["is_verified"]),
                    "chunk_index": row["chunk_index"] or 0,
                    # Explainability signals (trace/debug only).
                    "_title_match": tm > 0,
                    "_content_match": cm > 0,
                    "_domain_match": bool(dm),
                    "_title_hits": tm,
                    "_content_hits": cm,
                    "_matched_terms": cm + tm,
                }
            )

        # SQL already ordered and sliced; re-assert determinism defensively.
        results.sort(key=lambda r: (-r["score"], r["chunk_index"], r["chunk_id"]))

        return {
            "query": query,
            "normalized_query": normalized_q,
            "tokens": tokens,
            "results": results,
            "total_found": total_found,
            "status": STATUS_OK,
            "verified_only": verified_only,
            "unverified_match_count": 0,
        }
