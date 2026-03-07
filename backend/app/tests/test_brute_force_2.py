from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_brute_force():
    for _ in range(100):
        response = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "wrong"})
        assert response.status_code in [401, 429]
