import os
from pinecone import Pinecone
from src.db.database import SessionLocal
from src.db.models import RawData, ProcessedData

def clear_mock():
    db = SessionLocal()
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("No Pinecone key")
        return
        
    pc = Pinecone(api_key=api_key)
    index = pc.Index("blinkit1")
    
    # Get all mock raw data
    mock_raws = db.query(RawData).filter(RawData.source == "mock_data").all()
    mock_ids = [r.id for r in mock_raws]
    
    print(f"Found {len(mock_ids)} mock RawData records.")
    
    if not mock_ids:
        print("Nothing to clear.")
        return
        
    # Get corresponding processed data
    mock_processed = db.query(ProcessedData).filter(ProcessedData.raw_data_id.in_(mock_ids)).all()
    
    # Delete from Pinecone
    vector_ids = [p.embedding_id for p in mock_processed if p.embedding_id]
    if vector_ids:
        print(f"Deleting {len(vector_ids)} vectors from Pinecone...")
        # Batch delete if necessary
        batch_size = 100
        for i in range(0, len(vector_ids), batch_size):
            batch = vector_ids[i:i + batch_size]
            index.delete(ids=batch)
            
    # Delete from DB
    print("Deleting ProcessedData...")
    db.query(ProcessedData).filter(ProcessedData.raw_data_id.in_(mock_ids)).delete(synchronize_session=False)
    
    print("Deleting RawData...")
    db.query(RawData).filter(RawData.source == "mock_data").delete(synchronize_session=False)
    
    db.commit()
    db.close()
    print("Done clearing mock data.")

if __name__ == "__main__":
    clear_mock()
