import praw
import os
from dotenv import load_dotenv
from src.db.database import SessionLocal
from src.db.models import RawData

load_dotenv()

def fetch_reddit_posts(subreddit_name="blinkit", limit=100):
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "BlinkitDiscoveryEngine/1.0")

    if not client_id or not client_secret or client_id == "your_client_id":
        print("Reddit API credentials not configured. Skipping Reddit ingestion.")
        return

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
    except Exception as e:
        print(f"Error initializing Reddit client: {e}")
        return

    db = SessionLocal()
    try:
        new_records = 0
        subreddit = reddit.subreddit(subreddit_name)
        for submission in subreddit.new(limit=limit):
            source_id = f"reddit_post_{submission.id}"
            existing = db.query(RawData).filter(RawData.source_id == source_id).first()
            
            if not existing:
                record = RawData(
                    source="reddit",
                    source_id=source_id,
                    content=f"{submission.title}\n{submission.selftext}",
                    metadata_json={
                        "score": submission.score,
                        "url": submission.url,
                        "num_comments": submission.num_comments,
                        "created_utc": submission.created_utc
                    }
                )
                db.add(record)
                new_records += 1
                
            # Optionally fetch top level comments
            submission.comments.replace_more(limit=0)
            for comment in submission.comments.list():
                comment_source_id = f"reddit_comment_{comment.id}"
                existing_comment = db.query(RawData).filter(RawData.source_id == comment_source_id).first()
                if not existing_comment:
                    comment_record = RawData(
                        source="reddit",
                        source_id=comment_source_id,
                        content=comment.body,
                        metadata_json={
                            "score": comment.score,
                            "parent_id": comment.parent_id,
                            "created_utc": comment.created_utc
                        }
                    )
                    db.add(comment_record)
                    new_records += 1
                    
        db.commit()
        print(f"Added {new_records} new posts and comments from Reddit.")
    except Exception as e:
        print(f"Error saving Reddit data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fetch_reddit_posts()
