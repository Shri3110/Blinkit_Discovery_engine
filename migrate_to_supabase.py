import sqlite3
import json
from src.db.database import SessionLocal, engine
from src.db.models import RawData, Base
from datetime import datetime

def migrate_to_supabase():
    print("Creating tables in Supabase...")
    Base.metadata.create_all(bind=engine)
    
    print("Connecting to local SQLite database...")
    conn = sqlite3.connect("discovery_engine.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM raw_data")
    rows = cursor.fetchall()
    
    if not rows:
        print("No raw data found in SQLite.")
        return
        
    print(f"Found {len(rows)} raw reviews. Migrating to Supabase...")
    
    db = SessionLocal()
    try:
        count = 0
        for row in rows:
            # Check if exists
            existing = db.query(RawData).filter(RawData.source_id == row["source_id"]).first()
            if not existing:
                try:
                    meta = json.loads(row["metadata_json"]) if isinstance(row["metadata_json"], str) else row["metadata_json"]
                except:
                    meta = {}
                    
                record = RawData(
                    source=row["source"],
                    source_id=row["source_id"],
                    content=row["content"],
                    metadata_json=meta
                )
                db.add(record)
                count += 1
                
                if count % 100 == 0:
                    db.commit()
                    print(f"Migrated {count} records...")
                    
        db.commit()
        print(f"Migration complete! Successfully copied {count} raw reviews to Supabase.")
    except Exception as e:
        print(f"Migration error: {e}")
        db.rollback()
    finally:
        db.close()
        conn.close()

if __name__ == "__main__":
    migrate_to_supabase()
