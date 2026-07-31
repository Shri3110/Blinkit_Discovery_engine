import sqlite3
import json
from src.db.database import SessionLocal, engine
from src.db.models import ProcessedData, RawData
from src.processing.vector_store import run_vector_store_pipeline
from dotenv import load_dotenv

load_dotenv()

def migrate_processed():
    print("Connecting to local SQLite database...")
    conn = sqlite3.connect("discovery_engine.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM processed_data")
    rows = cursor.fetchall()
    
    if not rows:
        print("No processed data found in SQLite.")
        return
        
    print(f"Found {len(rows)} processed reviews. Migrating to Supabase...")
    
    db = SessionLocal()
    try:
        count = 0
        for row in rows:
            # Check if exists
            existing = db.query(ProcessedData).filter(ProcessedData.raw_data_id == row["raw_data_id"]).first()
            if not existing:
                try:
                    topics = json.loads(row["topic_tags"]) if isinstance(row["topic_tags"], str) else row["topic_tags"]
                except:
                    topics = []
                    
                record = ProcessedData(
                    raw_data_id=row["raw_data_id"],
                    normalized_content=row["normalized_content"],
                    language_detected=row["language_detected"],
                    embedding_id=None, # Force Pinecone re-embedding
                    user_segment=row["user_segment"],
                    topic_tags=topics,
                    created_at=row["created_at"]
                )
                db.add(record)
                count += 1
                
                if count % 50 == 0:
                    db.commit()
                    print(f"Migrated {count} processed records...")
                    
        db.commit()
        print(f"Migration complete! Successfully copied {count} processed reviews to Supabase.")
        
    except Exception as e:
        print(f"Migration error: {e}")
        db.rollback()
    finally:
        db.close()
        conn.close()

if __name__ == "__main__":
    migrate_processed()
    # Now that they are in Supabase with embedding_id=None, run the pipeline!
    run_vector_store_pipeline()
