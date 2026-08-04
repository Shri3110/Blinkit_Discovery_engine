import os
import json
import uuid
from dotenv import load_dotenv
load_dotenv()
from groq import Groq
from src.db.database import SessionLocal
from src.db.models import RawData

# Import pipelines
from src.processing.normalizer import run_normalizer
from src.engine.segmentation_engine import run_segmentation_pipeline
from src.processing.vector_store import run_vector_store_pipeline

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_ID")

def generate_and_ingest():
    if not GROQ_API_KEY:
        raise ValueError("No GROQ_API_KEY found")
        
    print("Generating mock reviews via Groq...")
    prompt = """
Generate 30 highly detailed, in-depth Blinkit user reviews or user interview transcripts. 

Your goal is to explicitly provide detailed answers to the following product research questions through the voice of the users:
1. Why do users repeatedly buy from the same categories? (e.g. Convenience, trust in freshness, zero cognitive load, reorder button)
2. What prevents users from exploring new categories? (e.g. Fear of poor quality in electronics/clothes, lack of rich product details, prices)
3. How do users discover products today? (e.g. Only searching explicitly for what they need, ignoring banners, relying on push notifications)
4. What role do habits play in shopping behavior? (e.g. Buying milk and bread every morning without looking at the app homepage)
5. What information do users need before trying a new category? (e.g. Reviews, return policies, better imagery, trusted brands)
6. What frustrations emerge repeatedly? (e.g. Out of stock on regular items, bad produce quality, high surge pricing)
7. Which user segments are more likely to experiment? (e.g. Gen Z users buying impulse snacks vs parents buying staples)
8. What unmet needs emerge consistently across discussions? (e.g. Weekly meal planning, subscribing to daily items, better filtering)

Each review MUST focus heavily on explicitly addressing 2 or 3 of these questions directly and clearly. Do not be subtle. The AI system relying on these reviews needs strong, blatant evidence for these points.

Make them sound like real users talking about their experiences, habits, and frustrations. Write lengthy paragraphs (3-4 sentences per review) packed with rich context.

You MUST output ONLY a valid JSON object with a single key "reviews" mapping to a list of strings.
Example: {"reviews": ["Review 1", "Review 2"]}
"""

    groq_client = Groq(api_key=GROQ_API_KEY)
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
        temperature=0.7,
        max_tokens=4000,
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content.strip()
    data = json.loads(content)
    reviews = data.get("reviews", [])
    
    if not reviews:
        print("No reviews generated.")
        return
        
    print(f"Generated {len(reviews)} reviews. Inserting into database...")
    
    db = SessionLocal()
    try:
        # First, delete old mock data to avoid duplication
        print("Clearing old mock_data from RawData...")
        deleted = db.query(RawData).filter(RawData.source == "mock_data").delete()
        print(f"Deleted {deleted} old mock records.")
        # Note: ProcessedData might need to be cleaned too if needed, but we'll focus on RawData
        
        inserted = 0
        for rev in reviews:
            # Create a mock source_id
            mock_id = f"mock_{uuid.uuid4().hex[:10]}"
            new_record = RawData(
                source="mock_data",
                source_id=mock_id,
                content=rev,
                metadata_json={"author": "MockUser", "rating": 3}
            )
            db.add(new_record)
            inserted += 1
            
        db.commit()
        print(f"Inserted {inserted} reviews into raw_data.")
    except Exception as e:
        print(f"DB Error: {e}")
        db.rollback()
    finally:
        db.close()
        
    print("--- Running Normalizer ---")
    run_normalizer()
    
    print("--- Running Segmentation ---")
    run_segmentation_pipeline(limit=100)
    
    print("--- Running Vector Store ---")
    run_vector_store_pipeline()
    
    print("Done!")

if __name__ == "__main__":
    generate_and_ingest()
