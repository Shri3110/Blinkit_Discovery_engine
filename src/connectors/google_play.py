from google_play_scraper import Sort, reviews
from src.db.database import SessionLocal
from src.db.models import RawData

def fetch_google_play_reviews(app_id="com.grofers.customerapp", lang='en', country='in', count=500):
    # 'com.grofers.customerapp' is the package name for Blinkit
    try:
        result, continuation_token = reviews(
            app_id,
            lang=lang,
            country=country,
            sort=Sort.NEWEST,
            count=count
        )
    except Exception as e:
        print(f"Error fetching from Google Play: {e}")
        return
    
    db = SessionLocal()
    try:
        new_records = 0
        for review in result:
            # check if review exists
            source_id = f"gp_{review['reviewId']}"
            existing = db.query(RawData).filter(RawData.source_id == source_id).first()
            if not existing:
                record = RawData(
                    source="google_play",
                    source_id=source_id,
                    content=review['content'],
                    metadata_json={
                        "score": review['score'],
                        "userName": review['userName'],
                        "at": review['at'].isoformat() if review['at'] else None,
                        "replyContent": review.get('replyContent')
                    }
                )
                db.add(record)
                new_records += 1
        db.commit()
        print(f"Added {new_records} new reviews from Google Play.")
    except Exception as e:
        print(f"Error saving Google Play reviews: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fetch_google_play_reviews()
