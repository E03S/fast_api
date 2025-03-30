from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_short_link():
    response = client.post(
        "/links/shorten",
        json={"original_url": "https://example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "short_code" in data