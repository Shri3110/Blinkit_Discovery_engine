import random
from datetime import datetime, timedelta
from src.db.database import SessionLocal
from src.db.models import RawData

def insert_synthetic_app_store_reviews(count=500):
    print("Apple's App Store currently blocks automated scraping (both Playwright and API endpoints).")
    print(f"Generating {count} realistic synthetic App Store reviews for the case study...")
    
    db = SessionLocal()
    
    positive_templates = [
        "Great app, delivery is always on time.",
        "Lifesaver! Got my groceries in 10 minutes.",
        "UI is very smooth on iOS. Much better than competitors.",
        "Love the new categories, especially the gifting section.",
        "Best quick commerce app in India right now.",
        "Always rely on Blinkit for my midnight cravings.",
        "Prices are decent and delivery is super fast."
    ]
    
    neutral_templates = [
        "Good app but sometimes items are out of stock.",
        "Delivery is fast but the fresh vegetables could be better.",
        "Decent experience, but I wish they had more electronics.",
        "App works well, but surge pricing is annoying during rain.",
        "Sometimes delivery takes 20 mins instead of 10, but it's okay."
    ]
    
    negative_templates = [
        "Customer support is terrible. I got a damaged item and they only gave me a coupon.",
        "Vegetables are not fresh at all. Ordered tomatoes and they were rotten.",
        "They sneak in handling fees at checkout. Very untransparent.",
        "Delivery agent was rude. Never using this again.",
        "Ordered an expensive item and it was open box. Cannot trust them for electronics.",
        "Refund process is a nightmare. Bots just keep replying."
    ]

    new_records = 0
    
    try:
        for i in range(count):
            # Determine sentiment to pick a template
            rand = random.random()
            if rand < 0.6:  # 60% positive
                content = random.choice(positive_templates)
                score = random.choice([4, 5])
            elif rand < 0.8: # 20% neutral
                content = random.choice(neutral_templates)
                score = random.choice([3])
            else: # 20% negative
                content = random.choice(negative_templates)
                score = random.choice([1, 2])
                
            author = f"iOSUser_{random.randint(1000, 99999)}"
            date_val = datetime.now() - timedelta(days=random.randint(1, 365))
            
            source_id = f"as_synthetic_{i}_{author}"
            
            existing = db.query(RawData).filter(RawData.source_id == source_id).first()
            if not existing:
                record = RawData(
                    source="app_store",
                    source_id=source_id,
                    content=content,
                    metadata_json={
                        "score": score,
                        "userName": author,
                        "date_str": date_val.strftime("%Y-%m-%d"),
                        "title": f"Review by {author}"
                    }
                )
                db.add(record)
                new_records += 1
                
        db.commit()
        print(f"Added {new_records} synthetic reviews from App Store.")
    except Exception as e:
        print(f"Error saving synthetic App Store reviews: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    insert_synthetic_app_store_reviews()
