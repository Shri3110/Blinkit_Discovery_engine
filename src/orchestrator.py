import schedule
import time
from src.connectors.google_play import fetch_google_play_reviews
from src.connectors.app_store import fetch_app_store_reviews
from src.connectors.reddit import fetch_reddit_posts
from src.connectors.synthetic_app_store import insert_synthetic_app_store_reviews
from src.connectors.dataset_ingestor import ingest_dataset_sample
from src.processing.normalizer import run_normalizer
from src.processing.vector_store import run_vector_store_pipeline
from src.engine.segmentation_engine import run_segmentation_pipeline

def run_ingestion():
    print("Starting data ingestion...")
    fetch_google_play_reviews()
    # fetch_app_store_reviews() # Disabled due to Apple blocks
    insert_synthetic_app_store_reviews()
    fetch_reddit_posts()
    ingest_dataset_sample()
    print("Data ingestion completed.")
    
    print("Starting Phase 2 processing...")
    run_normalizer(limit=50) # Process in chunks to avoid rate limits
    run_vector_store_pipeline()
    print("Phase 2 processing completed.")
    
    print("Starting Phase 3 segmentation...")
    run_segmentation_pipeline(limit=50)
    print("Phase 3 segmentation completed.")

# Schedule the job every day at 02:00 AM
schedule.every().day.at("02:00").do(run_ingestion)

if __name__ == "__main__":
    print("Orchestrator started. Running initial ingestion...")
    # Run once initially
    run_ingestion()
    
    print("Entering schedule loop...")
    while True:
        schedule.run_pending()
        time.sleep(60) # wait one minute
