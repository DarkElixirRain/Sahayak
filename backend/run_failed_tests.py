import httpx
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run():
    client.post("/api/auth/register", json={
        "email": "testdup@example.com",
        "password": "securepassword123",
        "name": "Test User"
    })
    response = client.post("/api/auth/register", json={
        "email": "testdup@example.com",
        "password": "anotherpassword",
        "name": "Test User 2"
    })
    print("Duplicate email response:", response.status_code, response.json())

run()
