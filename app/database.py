import os
from datetime import datetime
from pydantic import BaseModel

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")
engine = create_engine(DATABASE_URL)
Base = declarative_base()
DBSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class URLRequest(BaseModel):
    url: str
    expiration_date: datetime = None

def get_db_session():
    session = DBSession()
    try:
        yield session
    except DBAPIError:
        session.rollback()
    finally:
        session.close()


class ShortenedUrl(Base):
    __tablename__ = "shortened_urls"

    id = Column(Integer, primary_key=True)
    original_url = Column(String(255))
    short_link = Column(String(7), unique=True, index=True)
    use_count = Column(int)
    date_creation = Column(datetime)
    date_last_use = Column(datetime)
    expiration = Column(datetime)