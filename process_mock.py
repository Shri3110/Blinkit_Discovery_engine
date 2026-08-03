import os
import time
import json
from groq import Groq
from pinecone import Pinecone
from src.db.database import SessionLocal
from src.db.models import RawData, ProcessedData
from src.processing.vector_store import get_embedding_model

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_ID")

def process_mock_data():
    db = SessionLocal()
    
    # 1. Normalization
    print("Finding un-normalized mock data...")
    mock_raws = db.query(RawData).filter(RawData.source == "mock_data").all()
    mock_raw_ids = [r.id for r in mock_raws]
    
    existing_processed = db.query(ProcessedData).filter(ProcessedData.raw_data_id.in_(mock_raw_ids)).all()
    existing_processed_raw_ids = [p.raw_data_id for p in existing_processed]
    
    unnormalized = [r for r in mock_raws if r.id not in existing_processed_raw_ids]
    
    if unnormalized:
        print(f"Normalizing {len(unnormalized)} mock records...")
        for r in unnormalized:
            db.add(ProcessedData(
                raw_data_id=r.id,
                normalized_content=r.content.strip(),
                language_detected="en"
            ))
        db.commit()
    
    # Reload processed data for mock records
    mock_processed = db.query(ProcessedData).filter(ProcessedData.raw_data_id.in_(mock_raw_ids)).all()
    
    # 2. Segmentation
    unsegmented = [p for p in mock_processed if p.user_segment is None]
    if unsegmented:
        print(f"Segmenting {len(unsegmented)} mock records via Groq...")
        groq_client = Groq(api_key=GROQ_API_KEY)
        for i, p in enumerate(unsegmented):
            system_prompt = """
            You are an expert product analyst. Based on this review, assign ONE primary user persona from these:
            - Convenience Seeker
            - Value-Conscious Shopper
            - Quality/Freshness Prioritizer
            - Routine/Habitual Shopper
            - Occasional/Emergency Shopper
            
            If it does not fit perfectly, derive a descriptive 2-4 word behavioural label. General is a last resort.
            Return a JSON object with exactly one key "persona" containing the string name. Example: {"persona": "Routine/Habitual Shopper"}
            """
            try:
                response = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": p.normalized_content}
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                data = json.loads(response.choices[0].message.content)
                p.user_segment = data.get("persona", "Unknown")
            except Exception as e:
                print(f"Error on {p.id}: {e}")
                p.user_segment = "General"
                
            db.commit()
            time.sleep(2) # Rate limit
    
    # 3. Vector Embeddings
    unembedded = [p for p in mock_processed if p.embedding_id is None]
    if unembedded:
        print(f"Embedding {len(unembedded)} mock records into Pinecone...")
        api_key = os.getenv("PINECONE_API_KEY")
        pc = Pinecone(api_key=api_key)
        index = pc.Index("blinkit1")
        model = get_embedding_model()
        
        vectors_to_upsert = []
        for p in unembedded:
            doc_id = f"doc_{p.id}"
            embedding = list(model.embed([p.normalized_content]))[0].tolist()
            vectors_to_upsert.append({
                "id": doc_id,
                "values": embedding,
                "metadata": {
                    "raw_data_id": p.raw_data_id,
                    "text": p.normalized_content
                }
            })
            p.embedding_id = doc_id
            
        index.upsert(vectors=vectors_to_upsert)
        db.commit()
        
    print("Done processing mock data.")
    db.close()

if __name__ == "__main__":
    process_mock_data()
