import os
from src.db.database import SessionLocal
from src.db.models import RawData

def ingest_dataset_sample():
    file_path = "dataset_sample.md"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return
        
    db = SessionLocal()
    new_records = 0
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    current_author = "Unknown"
    current_content = []
    
    def save_record(author, content_lines):
        nonlocal new_records
        if not content_lines:
            return
        content = " ".join(content_lines).strip()
        source_id = f"dataset_sample_{new_records}"
        
        # Check if already exists
        existing = db.query(RawData).filter(RawData.source_id == source_id).first()
        if not existing:
            record = RawData(
                source="dataset_sample",
                source_id=source_id,
                content=content,
                metadata_json={"author_or_context": author}
            )
            db.add(record)
            new_records += 1
            
    for line in lines:
        line = line.strip()
        if line.startswith("**") and line.endswith("**") and len(line) > 4:
            # We found a new author/context line
            # Save previous if any
            save_record(current_author, current_content)
            current_author = line.strip("*")
            current_content = []
        elif line.startswith(">"):
            current_content.append(line[1:].strip())
            
    # Save last record
    save_record(current_author, current_content)
    
    try:
        db.commit()
        print(f"Successfully ingested {new_records} records from dataset_sample.md")
    except Exception as e:
        print(f"Error saving to DB: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    ingest_dataset_sample()
