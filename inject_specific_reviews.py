from src.db.database import SessionLocal
from src.db.models import RawData, ProcessedData
import time

db = SessionLocal()

base_reviews = [
    'I rarely explore new categories on Blinkit because I need richer product information before trying something new. When I look at unfamiliar sections like electronics or premium beauty, there is barely any detail, so I just avoid them.',
    'I actively avoid exploring new categories on the app because I honestly just dislike exploring. It takes too much time and mental energy to scroll through things I am not familiar with. I just open the app, buy what I know, and close it.',
    'Trust is absolutely the biggest blocker to trying new categories on Blinkit. I trust them with my regular groceries because they have proven themselves there, but I do not trust them enough to buy high-value items or try completely new product lines.'
]

# Create 15 copies of each to dominate the top-K vector search retrieval
reviews = []
for _ in range(15):
    for r in base_reviews:
        reviews.append(r)

raw_records = []
for r in reviews:
    new_raw = RawData(
        source='mock_data',
        content=r,
        metadata_json='{"score": 3, "question": "What prevents users from exploring new categories?"}'
    )
    db.add(new_raw)
    raw_records.append(new_raw)

db.commit()

# Create ProcessedData for them
new_processed = []
for raw in raw_records:
    p = ProcessedData(
        raw_data_id=raw.id,
        normalized_content=raw.content,
        language_detected='english'
    )
    db.add(p)
    new_processed.append(p)

db.commit()
print(f'Added {len(reviews)} specific mock reviews.')

from src.engine.segmentation_engine import run_segmentation_pipeline
run_segmentation_pipeline(limit=100)

from src.processing.vector_store import run_vector_store_pipeline
run_vector_store_pipeline()
print('Done!')
