from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://blinkit_user:blinkit_password@localhost:5432/discovery_engine")

# Ensure postgresql urls use proper dialect if needed (though postgresql:// works)
engine_kwargs = {}
if DATABASE_URL.startswith("postgres"):
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["connect_args"] = {"sslmode": "require"}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
