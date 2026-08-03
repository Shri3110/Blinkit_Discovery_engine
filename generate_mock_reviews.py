import os
import json
import uuid
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
Generate 30 realistic Blinkit user reviews that provide stronger evidence for answering these product research questions:

* Why do users repeatedly buy from the same categories?
* What prevents users from exploring new categories?
* How do users discover products today?
* What role do habits play in shopping behavior?
* What information do users need before trying a new category?
* What frustrations emerge repeatedly?
* Which user segments are more likely to experiment?
* What unmet needs emerge consistently across discussions?

The reviews should sound like genuine Google Play/App Store reviews, naturally mentioning shopping habits, search behaviour, product discovery, category exploration, trust, pricing, quality, recommendations, and repeat purchases. Do not make the reviews explicitly answer the questions. Instead, embed the evidence naturally so the RAG pipeline can retrieve and synthesize meaningful insights. Avoid repetitive wording and ensure a mix of positive, negative, and neutral experiences.

You MUST output ONLY a valid JSON object with a single key "reviews" mapping to a list of strings.
Example: {"reviews": ["Review 1", "Review 2"]}
"""

    groq_client = Groq(api_key=GROQ_API_KEY)
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        max_tokens=3000,
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
