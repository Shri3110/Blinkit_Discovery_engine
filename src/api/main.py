import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from pydantic import BaseModel
from sqlalchemy import func
from src.db.database import SessionLocal
from src.db.models import ProcessedData, RawData
from src.engine.rag_pipeline import query_discovery_engine

START_TIME = time.time()

app = FastAPI(title="Blinkit AI Discovery Engine API")

@app.get("/health")
def health_check():
    return {"status": "ok", "uptime": time.time() - START_TIME}

# Allow CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For MVP
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def start_orchestrator():
    import schedule
    import time
    from src.orchestrator import run_ingestion
    
    print("FastAPI background worker started. Entering schedule loop (no initial ingestion on boot)...")
    # run_ingestion() # Disabled so it doesn't scrape on every server deployment/restart
    while True:
        schedule.run_pending()
        time.sleep(60)

@app.on_event("startup")
def startup_event():
    import threading
    worker_thread = threading.Thread(target=start_orchestrator, daemon=True)
    worker_thread.start()
    print("Started background orchestrator thread.")

class QueryRequest(BaseModel):
    query: str

@app.get("/api/stats")
def get_stats():
    db = SessionLocal()
    import json
    try:
        total_raw = db.query(RawData).count()
        total_processed = db.query(ProcessedData).count()
        
        sources_count = db.query(RawData.source).distinct().count()
        
        raw_data = db.query(RawData.metadata_json).all()
        positive = 0
        negative = 0
        neutral = 0
        for row in raw_data:
            metadata = row[0]
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            if isinstance(metadata, dict):
                score = metadata.get("score")
                if score is not None:
                    try:
                        score = int(score)
                        if score >= 4:
                            positive += 1
                        elif score == 3:
                            neutral += 1
                        else:
                            negative += 1
                    except:
                        pass
        
        segments_count = db.query(ProcessedData.user_segment).filter(
            ProcessedData.user_segment.isnot(None), 
            ProcessedData.user_segment != 'Unknown'
        ).distinct().count()
        
        processed_topics = db.query(ProcessedData.topic_tags).all()
        unique_topics = set()
        for row in processed_topics:
            topics = row[0]
            if isinstance(topics, str):
                try:
                    topics = json.loads(topics)
                except:
                    topics = []
            if isinstance(topics, list):
                for t in topics:
                    unique_topics.add(t)
        topics_count = len(unique_topics)
        
        # Get top segments
        segments = db.query(
            ProcessedData.user_segment, 
            func.count(ProcessedData.id).label('count')
        ).group_by(ProcessedData.user_segment).all()
        
        return {
            "total_reviews": total_raw,
            "processed_reviews": total_processed,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "sources_analysed": sources_count,
            "user_segments": segments_count,
            "topics_identified": topics_count,
            "segments": [{"name": s[0], "value": s[1]} for s in segments if s[0]]
        }
    finally:
        db.close()

@app.get("/api/reviews")
def get_reviews(limit: int = 50):
    db = SessionLocal()
    try:
        # Fetch only original feedback from Google Play that has been fully processed (segmented) and is meaningful in length
        reviews = db.query(RawData, ProcessedData)\
            .join(ProcessedData, ProcessedData.raw_data_id == RawData.id)\
            .filter(RawData.source == "google_play")\
            .filter(ProcessedData.user_segment.isnot(None))\
            .filter(func.length(RawData.content) > 15)\
            .order_by(RawData.created_at.desc(), RawData.id.desc())\
            .limit(limit).all()
        formatted_reviews = []
        for raw, processed in reviews:
            topics = processed.topic_tags if processed else []
            if isinstance(topics, str):
                try:
                    topics = json.loads(topics)
                except:
                    topics = []
            formatted_reviews.append({
                "id": raw.id,
                "content": processed.normalized_content,
                "segment": processed.user_segment if processed else "Unprocessed",
                "topics": topics
            })
        return formatted_reviews
    finally:
        db.close()

@app.get("/api/trends/heatmap")
def get_heatmap():
    db = SessionLocal()
    try:
        reviews = db.query(ProcessedData).all()
        heatmap = {}
        for r in reviews:
            segment = r.user_segment or "Unknown"
            if segment not in heatmap:
                heatmap[segment] = {}
            topics = r.topic_tags
            if isinstance(topics, str):
                try:
                    topics = json.loads(topics)
                except:
                    topics = []
            for topic in (topics or []):
                if topic not in heatmap[segment]:
                    heatmap[segment][topic] = 0
                heatmap[segment][topic] += 1
                
        formatted_data = []
        for segment, topics in heatmap.items():
            row = {"segment": segment}
            row.update(topics)
            formatted_data.append(row)
            
        return formatted_data
    finally:
        db.close()

@app.post("/api/query")
def run_query(request: QueryRequest):
    try:
        if not request.query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
            
        result = query_discovery_engine(request.query, top_k=5)
        if isinstance(result, str):
            return {"report": result, "evidence": []}
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=False)
