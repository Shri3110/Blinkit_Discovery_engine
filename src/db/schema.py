import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Review(Base):
    """
    Table to store raw and processed feedback data.
    """
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False) # e.g., 'Google Play', 'App Store'
    review_id = Column(String(100), unique=True, nullable=False) # ID from the platform
    author_id = Column(String(200)) # Anonymized/hashed author ID
    
    # Raw Data
    raw_text = Column(Text, nullable=False)
    rating = Column(Float)
    created_at = Column(DateTime)
    
    # Processed Data
    cleaned_text = Column(Text)
    processed_text = Column(Text) # Lemmatized and without stop words
    sentiment = Column(String(20))
    user_segment = Column(String(50))

# Setup database connection
# Default to local SQLite if POSTGRES_URI is not set in environment (good for local testing)
DB_URL = os.getenv("POSTGRES_URI", "sqlite:///../../discovery_engine.db")

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """
    Create tables if they don't exist.
    """
    Base.metadata.create_all(engine)
    print(f"Database schema initialized successfully at {DB_URL}")

if __name__ == "__main__":
    init_db()
