from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from .database import Base, engine

class RawData(Base):
    __tablename__ = "raw_data"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), index=True)  # e.g., 'google_play', 'app_store', 'reddit'
    source_id = Column(String(255), unique=True, index=True) # ID from the platform to avoid duplicates
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, default={}) # extra data like author, score, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProcessedData(Base):
    __tablename__ = "processed_data"

    id = Column(Integer, primary_key=True, index=True)
    raw_data_id = Column(Integer, index=True) # Foreign Key reference without tight coupling constraint for SQLite simplicity, or use ForeignKey("raw_data.id")
    normalized_content = Column(Text, nullable=False)
    language_detected = Column(String(50))
    embedding_id = Column(String(255), index=True) # ID in ChromaDB
    user_segment = Column(String(50), nullable=True) # e.g., Family, Bachelor, Unknown
    topic_tags = Column(JSON, default=[]) # e.g., ["Quality", "Pricing"]
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Create tables
Base.metadata.create_all(bind=engine)
