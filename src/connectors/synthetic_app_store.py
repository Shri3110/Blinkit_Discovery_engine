import random
from datetime import datetime, timedelta
from src.db.database import SessionLocal
from src.db.models import RawData

def insert_synthetic_app_store_reviews(count=500):
    print("Apple's App Store currently blocks automated scraping (both Playwright and API endpoints).")
    print(f"Generating {count} realistic synthetic App Store reviews for the case study...")
    
    db = SessionLocal()
    
    positive_templates = [
        # General positive
        "Great app, delivery is always on time.",
        "Lifesaver! Got my groceries in 10 minutes.",
        "UI is very smooth on iOS. Much better than competitors.",
        
        # Q3: How do users discover products
        "I found out they sell pet food completely by accident when I misspelled something in the search bar. Now I order it weekly!",
        "I was checking out with chips and a pop-up suggested a dip. That's the only time I've ever bought something outside my usual list. Great recommendation!",
        "The push notification for midnight snacks was perfectly timed. Ended up exploring the ice cream section.",
        
        # Q7: Segments experimenting
        "As a new mom, I was desperate for diapers at 2 AM. Thank god they had them! I didn't even know they sold baby stuff until I was in a panic.",
        "I was hosting a party and ran out of ice, playing cards, and mixers. Blinkit saved me. I usually only buy veggies, but emergencies change things.",
        "Working from home and my mouse broke. Ordered a new one here and it arrived in 15 mins. Amazing clutch moment."
    ]
    
    neutral_templates = [
        # Q1 & Q4: Habits and buying same categories
        "I strictly use this app for my daily milk and bread. It's just out of habit, I open it, click reorder, and I'm done.",
        "I only buy groceries here. The quality of fresh produce is consistent, so I stick to what I know. I don't really browse.",
        "It's my designated grocery app. I have a set routine and I never browse for fun. I don't even look at the homepage banners anymore.",
        
        # Q5: Info needed before trying new category
        "I noticed they sell headphones now, but without detailed specs or a clear return policy, I don't feel confident buying them here.",
        "Before buying premium makeup here, I need to see a 'Brand Authorized' badge. Otherwise, I'm scared of getting fakes.",
        "If they added user reviews for the electronics, I might buy a charger, but right now there's zero reassurance.",
        
        # Q8: Unmet needs
        "I wish I could filter the beauty section by skin type. Right now it's just a massive unorganized list.",
        "There is no 'discover' tab. It's impossible to just browse what's new or trending. I only search for exact items."
    ]
    
    negative_templates = [
        # Q2: What prevents exploring new categories
        "I wanted to order skincare products, but there's no way to verify the expiry date or authenticity before buying, so I ended up using Nykaa instead.",
        "The search is terrible for finding gifts. I tried looking for a birthday present but it just showed me random chocolates. I gave up.",
        
        # Q6: Frustrations
        "Customer support is a bot loop. If a high-value item arrives damaged, you're just out of luck. I will never buy electronics here.",
        "I bought avocados and they were rock hard. It makes me not want to buy anything else from this app. If they can't get veggies right, how can I trust them for expensive stuff?",
        "Ordered an expensive item and it was open box. Cannot trust them for electronics. Refund process is a nightmare.",
        "They sneak in handling fees at checkout. Very untransparent.",
        "New categories like beauty are just mixed in randomly with household cleaners. It's a mess to navigate.",
        "Delivery takes longer when you order non-grocery items, but they don't tell you that upfront."
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
