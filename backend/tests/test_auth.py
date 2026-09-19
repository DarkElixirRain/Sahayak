import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_connection

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    with get_connection() as conn:
        conn.execute("DELETE FROM conversation_messages")
        conn.execute("DELETE FROM conversation_sessions")
        conn.execute("DELETE FROM users")
        conn.commit()
    yield

@pytest.fixture(autouse=True)
def unmock_auth():
    app.dependency_overrides.clear()
    yield

def test_register_user_success():
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "securepassword123",
        "name": "Test User"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data

def test_register_duplicate_email():
    client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "securepassword123"
    })
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "anotherpassword"
    })
    assert response.status_code == 400
    assert "Email already registered" in response.json()["error"]["message"]

def test_login_success():
    client.post("/api/auth/register", json={
        "email": "login@example.com",
        "password": "securepassword123"
    })
    response = client.post("/api/auth/login", data={
        "username": "login@example.com",
        "password": "securepassword123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_incorrect_password():
    client.post("/api/auth/register", json={
        "email": "login2@example.com",
        "password": "securepassword123"
    })
    response = client.post("/api/auth/login", data={
        "username": "login2@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_current_user_me():
    client.post("/api/auth/register", json={
        "email": "me@example.com",
        "password": "securepassword123",
        "name": "Me"
    })
    login_response = client.post("/api/auth/login", data={
        "username": "me@example.com",
        "password": "securepassword123"
    })
    token = login_response.json()["access_token"]

    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "me@example.com"
