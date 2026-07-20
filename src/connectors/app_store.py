import requests
import json
from src.db.database import SessionLocal
from src.db.models import RawData

def fetch_app_store_reviews(app_id="1052601267", country="in", count=500):
    print("Starting iTunes RSS fetch for App Store reviews...")
    db = SessionLocal()
    new_records = 0
    
    # Apple RSS allows pages 1 to 10, max 50 items per page
    max_pages = min(10, (count // 50) + 1)
    
    try:
        for page in range(1, max_pages + 1):
            url = f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/page={page}/json"
            response = requests.get(url)
            
            if response.status_code != 200:
                print(f"Failed to fetch page {page}: {response.status_code}")
                continue
                
            data = response.json()
            feed = data.get('feed', {})
            entries = feed.get('entry', [])
            
            # If no entries or only the app info entry, break
            if not entries:
                break
                
            for entry in entries:
                # The first entry in the first page is sometimes the app itself
                if 'author' not in entry:
                    continue
                
                author = entry['author']['name']['label']
                title = entry['title']['label']
                content = entry['content']['label']
                rating = entry['im:rating']['label']
                id_val = entry['id']['label']
                
                source_id = f"as_{id_val}"
                existing = db.query(RawData).filter(RawData.source_id == source_id).first()
                if not existing:
                    record = RawData(
                        source="app_store",
                        source_id=source_id,
                        content=content,
                        metadata_json={
                            "score": int(rating) if rating.isdigit() else 0,
                            "userName": author,
                            "title": title
                        }
                    )
                    db.add(record)
                    new_records += 1
                    
                    if new_records >= count:
                        break
            if new_records >= count:
                break
                
        db.commit()
        print(f"Added {new_records} new reviews from App Store (RSS).")
    except Exception as e:
        print(f"Error saving App Store reviews: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fetch_app_store_reviews()
