# fast_api
fast api homework
FastAPI URL Shortener
This is a URL shortener application built with FastAPI. It allows users to create shortened URLs, track usage statistics, and manage expired links.
API Endpoints
## 1. Create a Shortened URL
Endpoint: POST /links/shorten
Description: Creates a shortened URL for a given original URL.
Request Body:
Copy
```
{
  "url": "http://example.com",
  "expiration_date": "2023-12-31T23:59:59"  // Optional
}
```
Response:
Copy
```
{
  "short_link": "abc123"
}
```
3. Redirect to Original URL
Endpoint: GET /links/{short_code}
Description: Redirects to the original URL using the short link.
Response: Redirects to the original URL.
4. Get Usage Statistics
Endpoint: GET /links/stats/{short_code}
Description: Retrieves usage statistics for a shortened URL.
Response:
Copy
```
{
  "original_url": "http://example.com",
  "short_link": "abc123",
  "use_count": 5,
  "date_creation": "2023-01-01T00:00:00",
  "date_last_use": "2023-01-02T00:00:00",
  "expiration": "2023-12-31T23:59:59"
}
```
6. Get Expired Links
Endpoint: GET /links/expired
Description: Retrieves a list of expired shortened URLs.
Response:
Copy
```
[
  {
    "short_link": "def456",
    "original_url": "http://example.com",
    "use_count": 3,
    "date_creation": "2023-01-01T00:00:00",
    "date_last_use": "2023-01-02T00:00:00",
    "expiration": "2023-01-01T23:59:59"
  }
]
```
