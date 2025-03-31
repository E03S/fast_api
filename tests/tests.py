import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, patch

# Import the necessary modules and classes from the provided files
from app.main import app, get_db_session, ShortenedUrl, create_short_link, get_most_popular_urls_from_cache, update_cache_with_url_usage
from app.database import Base, DATABASE_URL

# Set up the database for testing
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Override the get_db_session dependency for testing
def override_get_db_session():
    try:
        session = TestingSessionLocal()
        yield session
    finally:
        session.close()

app.dependency_overrides[get_db_session] = override_get_db_session

# Create a TestClient for the FastAPI app
client = TestClient(app)

# Unit tests for service.py
def test_create_short_link():
    original_url = "http://example.com"
    timestamp = 1633072800.0
    short_link = create_short_link(original_url, timestamp)
    assert isinstance(short_link, str)
    assert len(short_link) == 7

# Unit tests for main.py
@patch('main.redis', new_callable=AsyncMock)
def test_create_short_link_endpoint():
    response = client.post("/links/shorten", json={"url": "http://example.com"})
    assert response.status_code == 200
    data = response.json()
    assert "short_link" in data

def test_redirect_to_original_url():
    # First, create a short link
    response = client.post("/links/shorten", json={"url": "http://example.com"})
    data = response.json()
    short_link = data["short_link"]

    # Then, try to redirect using the short link
    redirect_response = client.get(f"/links/{short_link}")
    assert redirect_response.status_code == 200
    # Check if the response is a redirect to the original URL
    assert redirect_response.headers["location"] == "http://example.com"

def test_get_expired_links():
    # This test assumes there are expired links in the database
    response = client.get("/links/expired")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

# Unit tests for database.py
def test_get_db_session():
    session_generator = get_db_session()
    session = next(session_generator)
    assert session is not None
    try:
        session.close()
    except Exception as e:
        pytest.fail(f"Session close failed: {e}")

# Run the tests
if __name__ == "__main__":
    pytest.main(["-v", "-s"])