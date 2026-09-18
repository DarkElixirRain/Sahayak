"""Tests for the read-only knowledge API endpoints.

The database is mocked so these tests never need a connection.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_list_domains_returns_repo_rows():
    canned = [
        {"id": "11111111-1111-1111-1111-111111111111", "key": "consumer",
         "name": "Consumer", "description": "d", "is_active": True}
    ]
    with patch("app.api.routes.knowledge.get_connection") as gc, \
         patch("app.api.routes.knowledge.LegalDomainRepository") as repo:
        gc.return_value.__enter__.return_value = "conn"
        gc.return_value.__exit__.return_value = None
        repo.return_value.list.return_value = canned

        response = client.get("/api/knowledge/domains")

    assert response.status_code == 200
    assert response.json()[0]["key"] == "consumer"


def test_search_requires_domain_lookup():
    canned_chunk = {
        "id": "22222222-2222-2222-2222-222222222222",
        "chunk_title": "One",
        "content": "Sample verified content with enough length.",
        "language": "nepali",
        "chunk_index": 1,
        "is_verified": True,
        "document_title": "Doc",
        "document_type": "act",
        "source_name": "Source",
        "source_url": "https://example.invalid/x",
    }
    with patch("app.api.routes.knowledge.get_connection") as gc, \
         patch("app.api.routes.knowledge.LegalDomainRepository") as dr, \
         patch("app.api.routes.knowledge.KnowledgeChunkRepository") as cr:
        gc.return_value.__enter__.return_value = "conn"
        dr.return_value.get_by_key.return_value = {"id": "dom1", "key": "consumer"}
        cr.return_value.search.return_value = [canned_chunk]

        response = client.get("/api/knowledge/search?domain=consumer&q=संरक्षण")

    assert response.status_code == 200
    assert response.json()[0]["document_title"] == "Doc"
    cr.return_value.search.assert_called_once()


def test_search_unknown_domain_returns_404():
    with patch("app.api.routes.knowledge.get_connection") as gc, \
         patch("app.api.routes.knowledge.LegalDomainRepository") as dr:
        gc.return_value.__enter__.return_value = "conn"
        dr.return_value.get_by_key.return_value = None

        response = client.get("/api/knowledge/search?domain=science")

    assert response.status_code == 404