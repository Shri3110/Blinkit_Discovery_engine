import os
import time
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from src.db.database import SessionLocal
from src.db.models import ProcessedData

# Load the local embedding model (same model Chroma used natively)
# Dimensions: 384
model = SentenceTransformer('all-MiniLM-L6-v2')

def run_vector_store_pipeline():
    print("Starting Vector Store Pipeline (Pinecone)...")
    
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("PINECONE_API_KEY is not set. Skipping vector store ingestion.")
        return
        
    pc = Pinecone(api_key=api_key)
    index_name = "blinkit-discovery"
    
    # Check if index exists
    if index_name not in [index.name for index in pc.list_indexes()]:
        print(f"Error: Pinecone index '{index_name}' does not exist. Please create it with 384 dimensions and cosine metric.")
        return
        
    index = pc.Index(index_name)
    
    db = SessionLocal()
    try:
        # Find processed data that hasn't been embedded yet (embedding_id is None)
        pending_records = db.query(ProcessedData).filter(ProcessedData.embedding_id == None).all()
        
        if not pending_records:
            print("No new records to embed.")
            return
            
        print(f"Found {len(pending_records)} pending records for embedding. Processing...")
        
        vectors_to_upsert = []
        
        for record in pending_records:
            doc_id = f"doc_{record.id}"
            
            # Generate embedding manually
            embedding = model.encode(record.normalized_content).tolist()
            
            # Create pinecone vector object
            vectors_to_upsert.append({
                "id": doc_id,
                "values": embedding,
                "metadata": {
                    "raw_data_id": record.raw_data_id,
                    "text": record.normalized_content
                }
            })
            
            # Update DB record with the Pinecone id
            record.embedding_id = doc_id
            
        # Add to Pinecone in batches of 100
        batch_size = 100
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            index.upsert(vectors=batch)
            time.sleep(0.5) # Slight delay to avoid rate limits
        
        db.commit()
        print(f"Successfully generated embeddings and stored {len(pending_records)} records in Pinecone.")
        
    except Exception as e:
        print(f"Error in vector store pipeline: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_vector_store_pipeline()
