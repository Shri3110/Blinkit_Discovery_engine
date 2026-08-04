from src.db.database import SessionLocal
from src.db.models import RawData, ProcessedData
import os
from pinecone import Pinecone

db = SessionLocal()

# Find the injected raw records based on the specific question in metadata
# Or by exact content. Since we know the content, we can match exactly.
reviews = [
    'I always end up buying from the exact same grocery categories on Blinkit every single week. The main reason is that I just need richer product information before I even think about trying new categories. When I look at the electronics or beauty sections, there is barely any detail, so I just stick to what I know works.',
    'I actively avoid exploring new categories on the app because I honestly dislike exploring. It takes too much time and mental energy to scroll through things I am not familiar with. I just open the app, re-order from my usual categories, and close it. Exploring new sections is just too tedious for me.',
    'Trust is absolutely the biggest blocker to trying new categories on Blinkit. I trust them with my regular groceries and snacks because they have proven themselves there, but I do not trust them enough to buy high-value items or try completely new product lines. Without that established trust, I repeatedly buy from the same safe categories.'
]

raw_records = db.query(RawData).filter(RawData.content.in_(reviews)).all()
raw_ids = [r.id for r in raw_records]

print(f"Found {len(raw_records)} raw records to delete.")

if raw_ids:
    processed_records = db.query(ProcessedData).filter(ProcessedData.raw_data_id.in_(raw_ids)).all()
    pinecone_ids = [f"doc_{p.id}" for p in processed_records]
    
    # Delete from Pinecone
    api_key = os.getenv("PINECONE_API_KEY")
    if api_key and pinecone_ids:
        pc = Pinecone(api_key=api_key)
        index_name = "blinkit1"
        if index_name in [index.name for index in pc.list_indexes()]:
            index = pc.Index(index_name)
            index.delete(ids=pinecone_ids)
            print(f"Deleted {len(pinecone_ids)} vectors from Pinecone.")
            
    # Delete from Database
    for p in processed_records:
        db.delete(p)
    for r in raw_records:
        db.delete(r)
    
    db.commit()
    print("Deleted from SQLite database.")
else:
    print("No records found to delete.")

db.close()
