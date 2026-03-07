from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_xss():
    response = client.get("/api/v1/openapi.json")
    print(response.status_code)
