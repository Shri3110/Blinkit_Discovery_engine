import os
import json
import time
from groq import Groq
from src.db.database import SessionLocal
from src.db.models import ProcessedData

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_ID")

def infer_segmentation(content):
    if not GROQ_API_KEY:
        raise ValueError("No GROQ_API_KEY found in .env")
        
    system_prompt = """
    Analyze the user review/feedback.
    Infer the demographic user segment (e.g., 'Bachelor', 'Family', 'Student', 'Pet Owner', or 'General' if unknown).
    Infer 1-3 primary topics (e.g., 'Quality', 'Pricing', 'Delivery', 'Electronics', 'Fresh Produce').
    
    You MUST output valid JSON only in this exact format:
    {
      "segment": "Family",
      "topics": ["Quality", "Delivery"]
    }
    """
    
    groq_client = Groq(api_key=GROQ_API_KEY)
    response = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Feedback: {content}"}
        ],
        model="llama-3.1-8b-instant",
        temperature=0.1,
        max_tokens=150,
        response_format={"type": "json_object"}
    )
    
    result = response.choices[0].message.content.strip()
    return json.loads(result)

def run_segmentation_pipeline(limit=50):
    print("Starting Segmentation Engine...")
    db = SessionLocal()
    
    try:
        # Find processed data without segments
        pending_records = db.query(ProcessedData).filter(ProcessedData.user_segment == None).limit(limit).all()
        
        if not pending_records:
            print("No new records to segment.")
            return
            
        print(f"Found {len(pending_records)} pending records for segmentation. Processing...")
        
        success_count = 0
        for record in pending_records:
            try:
                inference = infer_segmentation(record.normalized_content)
                record.user_segment = inference.get("segment", "General")
                record.topic_tags = inference.get("topics", [])
                
                success_count += 1
                if success_count % 10 == 0:
                    db.commit()
                time.sleep(2) # 2-second delay for rate limit
            except Exception as item_error:
                print(f"Error segmenting record {record.id}: {item_error}")
                
        db.commit()
        print(f"Successfully segmented {success_count} records.")
        
    except Exception as e:
        print(f"Error in segmentation pipeline: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_segmentation_pipeline()
