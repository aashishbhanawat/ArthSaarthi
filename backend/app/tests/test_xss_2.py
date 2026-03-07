from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_xss_2():
    response = client.get("/api/v1/auth/status")
    print(response.headers)
