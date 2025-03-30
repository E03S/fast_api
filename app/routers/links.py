from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
from app.models import Link
from app.schemas import LinkCreate, LinkShorten, LinkSearch, LinkStats, LinkBase
from app.database import get_db

router = APIRouter(prefix="/links", tags=["links"])

@router.post("/shorten")
async def shorten_link(link: LinkCreate, db: Session = Depends(get_db)):
    if link.custom_alias:
        existing_alias = db.query(Link).filter_by(custom_alias=link.custom_alias).first()
        if existing_alias:
            raise HTTPException(status_code=400, detail="Custom alias already exists")

    if not link.custom_alias:
        import string
        import random
        chars = string.ascii_letters + string.digits
        short_code = ''.join(random.choice(chars) for _ in range(6))
        while db.query(Link).filter_by(short_code=short_code).first():
            short_code = ''.join(random.choice(chars) for _ in range(6))
    else:
        short_code = link.custom_alias

    new_link = Link(
        short_code=short_code,
        original_url=link.original_url,
        expires_at=link.expires_at,
        custom_alias=link.custom_alias
    )
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return LinkShorten(
        short_code=short_code,
        original_url=link.original_url,
        expires_at=link.expires_at,
        custom_alias=link.custom_alias,
        created_at=new_link.created_at,
        redirect_count=0,
        last_used_at=None
    )

@router.get("/{short_code}")
async def redirect_to_original(short_code: str, db: Session = Depends(get_db), request: Request = None):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    
    if link.expires_at and datetime.now(timezone.utc) > link.expires_at:
        db.delete(link)
        db.commit()
        raise HTTPException(status_code=404, detail="Short link has expired")
    
    link.redirect_count += 1
    link.last_used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(link)
    
    return RedirectResponse(link.original_url, status_code=status.HTTP_303_SEE_OTHER)

@router.delete("/{short_code}")
async def delete_short_link(short_code: str, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    db.delete(link)
    db.commit()
    return {"message": "Short link deleted successfully"}

@router.put("/{short_code}")
async def update_short_link(short_code: str, link_data: LinkBase, db: Session = Depends(get_db)):
    link_in_db = db.query(Link).filter(Link.short_code == short_code).first()
    if not link_in_db:
        raise HTTPException(status_code=404, detail="Short link not found")
    
    if link_in_db.expires_at and datetime.now(timezone.utc) > link_in_db.expires_at:
        db.delete(link_in_db)
        db.commit()
        raise HTTPException(status_code=404, detail="Short link has expired")
    
    link_in_db.original_url = link_data.original_url
    link_in_db.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(link_in_db)
    
    return LinkShorten(
        short_code=link_in_db.short_code,
        original_url=link_in_db.original_url,
        expires_at=link_in_db.expires_at,
        custom_alias=link_in_db.custom_alias,
        created_at=link_in_db.created_at,
        redirect_count=link_in_db.redirect_count,
        last_used_at=link_in_db.last_used_at
    )

@router.get("/{short_code}/stats")
async def get_stats(short_code: str, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    
    if link.expires_at and datetime.now(timezone.utc) > link.expires_at:
        db.delete(link)
        db.commit()
        raise HTTPException(status_code=404, detail="Short link has expired")
    
    return LinkStats(
        original_url=link.original_url,
        created_at=link.created_at,
        redirect_count=link.redirect_count,
        last_used_at=link.last_used_at
    )

@router.get("/search")
async def search_by_original_url(original_url: str, db: Session = Depends(get_db)):
    links = db.query(Link).filter(Link.original_url == original_url).all()
    if not links:
        raise HTTPException(status_code=404, detail="No links found for this original URL")
    return [LinkSearch(short_code=link.short_code) for link in links]