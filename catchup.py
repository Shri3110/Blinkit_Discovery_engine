import time
from src.processing.normalizer import run_normalizer
from src.processing.vector_store import run_vector_store_pipeline
from src.engine.segmentation_engine import run_segmentation_pipeline
from src.db.database import SessionLocal
from src.db.models import RawData, ProcessedData

def main():
    print("Starting Catch-up Script...")
    db = SessionLocal()
    
    total_raw = db.query(RawData).count()
    total_processed = db.query(ProcessedData).count()
    db.close()
    
    print(f"Total Raw: {total_raw}, Total Processed: {total_processed}")
    
    while True:
        db = SessionLocal()
        total_raw_current = db.query(RawData).count()
        total_processed_current = db.query(ProcessedData).count()
        unsegmented_count = db.query(ProcessedData).filter(ProcessedData.user_segment == None).count()
        db.close()
        
        # Stop condition: if all raw data has been processed AND all processed data has been segmented
        if total_processed_current >= total_raw_current and unsegmented_count == 0:
            print("Backlog completely processed!")
            break
            
        print("\n--- Processing Next Batch ---")
        try:
            if total_processed_current < total_raw_current:
                print("Running Normalizer...")
                run_normalizer(limit=50)
            
            print("Running Vector Store Pipeline...")
            run_vector_store_pipeline()
            
            if unsegmented_count > 0:
                print("Running Segmentation Pipeline...")
                run_segmentation_pipeline(limit=50)
            
            print("Batch completed. Sleeping for 5 seconds to cool down APIs...")
            time.sleep(5)
            
        except Exception as e:
            print(f"Error during catchup batch: {e}")
            print("Sleeping for 15 seconds before retrying...")
            time.sleep(15)

if __name__ == "__main__":
    main()
