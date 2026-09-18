"""Repository/data-access layer for the Sahayak legal knowledge database.

Repositories take a psycopg connection (typically from
``app.db.session.get_connection``) and return plain dict rows.
Raw SQL is confined to this layer — API endpoints never scatter queries.
"""

from app.repositories import (
    court_cases,
    government_resources,
    knowledge_chunks,
    legal_documents,
    legal_domains,
    legal_provisions,
    risk_rules,
    sources,
)

__all__ = [
    "court_cases",
    "government_resources",
    "knowledge_chunks",
    "legal_documents",
    "legal_domains",
    "legal_provisions",
    "risk_rules",
    "sources",
]