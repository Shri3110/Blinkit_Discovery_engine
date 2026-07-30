import os
import json
import time
from dotenv import load_dotenv
from groq import Groq
from src.db.database import SessionLocal
from src.db.models import RawData, ProcessedData

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def normalize_text(content):
    if not GROQ_API_KEY and not OPENAI_API_KEY:
        raise ValueError("No GROQ_API_KEY or OPENAI_API_KEY found in .env file.")
        
    system_prompt = """
    You are an expert NLP translation and normalization assistant.
    The user will provide a raw review or forum post which might contain 'Hinglish' (Hindi written in English alphabet), slang, or poor grammar.
    Your task:
    1. Translate any Hinglish to proper, professional English.
    2. Fix grammar and spelling.
    3. Maintain the core sentiment and meaning of the original text.
    4. Output ONLY the translated/normalized English text, nothing else.
    """
    
    if GROQ_API_KEY:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()
    else:
        # Fallback to OpenAI if configured
        import openai
        openai.api_key = OPENAI_API_KEY
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            temperature=0.1
        )
        return response.choices[0].message.content.strip()

def run_normalizer(limit=50):
    print("Starting NLP Normalization Pipeline (Hinglish to English)...")
    db = SessionLocal()
    
    try:
        # Find raw data IDs that haven't been processed yet
        processed_ids = db.query(ProcessedData.raw_data_id).all()
        processed_ids = [r[0] for r in processed_ids]
        
        pending_records = db.query(RawData).filter(RawData.id.notin_(processed_ids)).limit(limit).all()
        
        if not pending_records:
            print("No new records to process.")
            return

        print(f"Found {len(pending_records)} pending records. Processing...")
        
        success_count = 0
        for record in pending_records:
            try:
                normalized_text = normalize_text(record.content)
                
                processed_record = ProcessedData(
                    raw_data_id=record.id,
                    normalized_content=normalized_text,
                    language_detected="hinglish/english" # Simplified for MVP
                )
                db.add(processed_record)
                success_count += 1
                
                if success_count % 10 == 0:
                    db.commit() # batch commit
            except Exception as item_error:
                print(f"Error processing record {record.id}: {item_error}")
            finally:
                time.sleep(2) # 2-second delay for rate limit ALWAYS respected
                
        db.commit()
        print(f"Successfully normalized {success_count} records.")
        
    except Exception as e:
        print(f"Error in normalizer: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_normalizer()
