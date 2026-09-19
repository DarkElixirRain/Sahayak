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

def get_auth_token():
    client.post("/api/auth/register", json={
        "email": "voice@example.com",
        "password": "securepassword123",
        "name": "Voice User"
    })
    response = client.post("/api/auth/login", data={
        "username": "voice@example.com",
        "password": "securepassword123"
    })
    return response.json()["access_token"]

def test_voice_endpoint_success():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Send a dummy audio file
    # We create a dummy wav payload. For mock provider, any non-empty byte string works, 
    # but since mutagen checks duration, let's just use an empty file if mutagen falls back gracefully, 
    # or let's create a minimal valid wav or mp3 if mutagen throws.
    # Actually, our API does:
    # try: audio_file = mutagen.File(...) ... except: pass
    # So an empty or invalid audio file will bypass duration check but fail size if too large.
    # We can pass some dummy bytes.
    dummy_audio = b"dummy audio content"
    
    response = client.post(
        "/api/conversations/session_123/voice",
        headers=headers,
        files={"audio": ("test.wav", dummy_audio, "audio/wav")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "audio" in data
    # Mock TTS returns some bytes, check if base64 works
    assert data["audio"] is not None

def test_voice_unauthorized():
    # No auth header
    dummy_audio = b"dummy audio content"
    response = client.post(
        "/api/conversations/session_123/voice",
        files={"audio": ("test.wav", dummy_audio, "audio/wav")}
    )
    assert response.status_code == 401

def test_voice_idor():
    token1 = get_auth_token()
    
    # Create another user
    client.post("/api/auth/register", json={
        "email": "voice2@example.com",
        "password": "securepassword123"
    })
    response2 = client.post("/api/auth/login", data={
        "username": "voice2@example.com",
        "password": "securepassword123"
    })
    token2 = response2.json()["access_token"]

    # User 1 creates session
    client.post(
        "/api/conversations/session_idor/messages",
        headers={"Authorization": f"Bearer {token1}"},
        json={"message": "hello"}
    )

    # User 2 tries to access it via voice
    dummy_audio = b"dummy audio content"
    response = client.post(
        "/api/conversations/session_idor/voice",
        headers={"Authorization": f"Bearer {token2}"},
        files={"audio": ("test.wav", dummy_audio, "audio/wav")}
    )
    assert response.status_code == 403

def test_voice_audio_too_large(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "max_audio_size_mb", 0) # 0 MB limit
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    dummy_audio = b"A" * 1024 # 1 KB
    response = client.post(
        "/api/conversations/session_123/voice",
        headers=headers,
        files={"audio": ("test.wav", dummy_audio, "audio/wav")}
    )
    assert response.status_code == 400
    assert "Audio file exceeds" in response.json()["error"]["message"]
