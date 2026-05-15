from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from .db import Base


class RawScrape(Base):
    __tablename__ = "raw_scrape"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(64), index=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    raw_text = Column(Text)
    metadata = Column(JSON)


class Startup(Base):
    __tablename__ = "startup"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    source = Column(String(64))
    metadata = Column(JSON)
