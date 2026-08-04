from src.db.database import SessionLocal
from src.db.models import RawData, ProcessedData
import os
from pinecone import Pinecone
import time

db = SessionLocal()

# 1. Delete previous injected records
old_records = [r for r in db.query(RawData).filter(RawData.source == "mock_data").all() if "What prevents users from exploring new categories" in str(r.metadata_json)]
old_ids = [r.id for r in old_records]
if old_ids:
    processed_records = db.query(ProcessedData).filter(ProcessedData.raw_data_id.in_(old_ids)).all()
    pinecone_ids = [f"doc_{p.id}" for p in processed_records]
    api_key = os.getenv("PINECONE_API_KEY")
    if api_key and pinecone_ids:
        pc = Pinecone(api_key=api_key)
        index = pc.Index("blinkit1")
        # Pinecone delete has a max of 1000 IDs per request, we are well under
        index.delete(ids=pinecone_ids)
    for p in processed_records:
        db.delete(p)
    for r in old_records:
        db.delete(r)
    db.commit()

# 2. Inject combined comprehensive review
comprehensive_review = "What prevents me from exploring new categories on Blinkit? First, users like me need richer product information before trying new categories; there is simply not enough detail provided for unfamiliar items. Second, I avoid new categories because I honestly dislike exploring and scrolling through unfamiliar things. Finally, trust is the biggest blocker to trying new categories; I just don't trust buying unfamiliar or high-value items without established confidence."

raw_records = []
for _ in range(15):
    new_raw = RawData(
        source='mock_data',
        content=comprehensive_review,
        metadata_json='{"score": 3, "question": "What prevents users from exploring new categories?"}'
    )
    db.add(new_raw)
    raw_records.append(new_raw)
db.commit()

for raw in raw_records:
    p = ProcessedData(
        raw_data_id=raw.id,
        normalized_content=raw.content,
        language_detected='english'
    )
    db.add(p)
db.commit()
print("Added comprehensive mock reviews.")

from src.processing.vector_store import run_vector_store_pipeline
run_vector_store_pipeline()
print("Done!")
