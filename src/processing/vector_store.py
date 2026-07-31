import os
import time
from pinecone import Pinecone
from src.db.database import SessionLocal
from src.db.models import ProcessedData

# Lazy load the embedding model to save RAM
_model = None
def get_embedding_model():
    global _model
    if _model is None:
        from fastembed import TextEmbedding
        _model = TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2')
    return _model

def run_vector_store_pipeline():
    print("Starting Vector Store Pipeline (Pinecone)...")
    
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("PINECONE_API_KEY is not set. Skipping vector store ingestion.")
        return
        
    pc = Pinecone(api_key=api_key)
    index_name = "blinkit1"
    
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
            model = get_embedding_model()
            embedding = list(model.embed([record.normalized_content]))[0].tolist()
            
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
