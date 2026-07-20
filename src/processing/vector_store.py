import os
import chromadb
from chromadb.utils import embedding_functions
from src.db.database import SessionLocal
from src.db.models import ProcessedData

# Use a lightweight sentence-transformer model by default
# This runs locally and doesn't require an API key, saving costs!
default_ef = embedding_functions.DefaultEmbeddingFunction()

def run_vector_store_pipeline():
    print("Starting Vector Store Pipeline (ChromaDB)...")
    
    # Initialize ChromaDB persistent client
    chroma_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_db")
    client = chromadb.PersistentClient(path=chroma_path)
    
    # Get or create collection
    collection = client.get_or_create_collection(
        name="reviews_collection",
        embedding_function=default_ef
    )
    
    db = SessionLocal()
    try:
        # Find processed data that hasn't been embedded yet (embedding_id is None)
        pending_records = db.query(ProcessedData).filter(ProcessedData.embedding_id == None).all()
        
        if not pending_records:
            print("No new records to embed.")
            return
            
        print(f"Found {len(pending_records)} pending records for embedding. Processing...")
        
        documents = []
        metadatas = []
        ids = []
        
        for record in pending_records:
            doc_id = f"doc_{record.id}"
            
            documents.append(record.normalized_content)
            metadatas.append({"raw_data_id": record.raw_data_id})
            ids.append(doc_id)
            
            # Update DB record with the ChromaDB id
            record.embedding_id = doc_id
            
        # Add to ChromaDB in batches (Chroma handles batching internally, but max batch size is usually 41666)
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        db.commit()
        print(f"Successfully generated embeddings and stored {len(pending_records)} records in ChromaDB.")
        
    except Exception as e:
        print(f"Error in vector store pipeline: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_vector_store_pipeline()
