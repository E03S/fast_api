from datetime import datetime, timezone

from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import HttpUrl
from sqlalchemy.orm import Session
import aioredis

from .database import ShortenedUrl, get_db_session
from .service import create_short_link

class URLRequest(BaseModel):
    url: str
    expiration_date: datetime = None

app = FastAPI()

redis = aioredis.from_url("redis://localhost")

# Function to get the most popular URLs from the cache
async def get_most_popular_urls_from_cache():
    cached_urls = await redis.zrevrange("popular_urls", 0, 9, withscores=True)
    return [(url.decode('utf-8'), int(score)) for url, score in cached_urls]

async def update_cache_with_url_usage(short_code: str, use_count: int):
    await redis.zadd("popular_urls", {short_code: use_count})

@app.post("/links/shorten")
async def get_short_link(
    url_req: URLRequest,db: Session = Depends(get_db_session)
):

    timestamp = datetime.now().replace(tzinfo=timezone.utc).timestamp()
    short_link = create_short_link(url_req.url, timestamp)
    expiration_date = url_req.expiration_date or (datetime.now() + datetime.timedelta(days=15))
    obj = ShortenedUrl(original_url=url_req.url, short_link=short_link, use_count = 0, date_creation = datetime.now(), date_last_use = datetime.datetime(1, 1, 1, 0, 0), expirtion =expiration_date)
    db.add(obj)
    db.commit()

    return {"short_link": short_link}


@app.get("/links/{short_code}")
async def redirect_to_original_url(short_code: str, db: Session = Depends(get_db_session)):
    # Query the database for the short code
    shortened_url = db.query(ShortenedUrl).filter(ShortenedUrl.short_link == short_code).first()

    if not shortened_url:
        raise HTTPException(status_code=404, detail="Short link not found")

    # Check if the link has expired
    if shortened_url.expiration and shortened_url.expiration < datetime.now():
        db.delete(shortened_url)
        db.commit()
        raise HTTPException(status_code=410, detail="Link has expired")

    # Update the use count and last used date
    shortened_url.use_count += 1
    shortened_url.date_last_use = datetime.now()
    db.commit()

    # Redirect to the original URL
    return RedirectResponse(url=shortened_url.original_url)


@app.delete("/links/{short_code}")
async def delete_short_link(short_code: str, db: Session = Depends(get_db_session)):
    # Query the database for the short code
    shortened_url = db.query(ShortenedUrl).filter(ShortenedUrl.short_link == short_code).first()

    if not shortened_url:
        raise HTTPException(status_code=404, detail="Short link not found")

    # Delete the entry from the database
    db.delete(shortened_url)
    db.commit()

    return {"detail": "Short link deleted successfully"}

@app.put("/links/{short_code}")
async def update_short_link(short_code: str, db: Session = Depends(get_db_session)):
    # Query the database for the short code
    shortened_url = db.query(ShortenedUrl).filter(ShortenedUrl.short_link == short_code).first()

    if not shortened_url:
        raise HTTPException(status_code=404, detail="Short link not found")

    # Generate a new short code
    timestamp = datetime.now().replace(tzinfo=timezone.utc).timestamp()
    short_link = create_short_link(shortened_url.original_url, timestamp)

    # Update the entry with the new short code
    shortened_url.short_link = short_link
    db.commit()

    return {"detail": "Short link updated successfully", "new_short_link": short_link}

@app.get("/links/{short_code}/stats")
async def get_short_link_stats(short_code: str, db: Session = Depends(get_db_session)):
    # Query the database for the short code
    shortened_url = db.query(ShortenedUrl).filter(ShortenedUrl.short_link == short_code).first()

    if not shortened_url:
        raise HTTPException(status_code=404, detail="Short link not found")

    # Prepare the statistics response
    stats = {
        "original_url": shortened_url.original_url,
        "use_count": shortened_url.use_count,
        "date_creation": shortened_url.date_creation,
        "date_last_use": shortened_url.date_last_use if shortened_url.date_last_use != datetime(1, 1, 1, 0, 0) else None,
    }

    return stats